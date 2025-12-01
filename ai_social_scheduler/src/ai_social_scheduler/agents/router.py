"""Router Agent - LLM 意图分析与路由决策

负责：
1. 📥 接收用户消息
2. 🤔 LLM 分析用户意图
3. 🎯 做出路由决策
4. 💬 生成回复内容
"""

from typing import Any, Optional

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from ..client import QwenClient
from ..core.models import (
    AgentConfig,
    IntentType,
    NextAgent,
    RouterDecision,
    TaskContext,
    TaskStatus,
)
from ..core.state import AgentState, get_last_human_message
from ..tools.logging import get_logger
from .base import AgentRegistry, BaseAgent

logger = get_logger(__name__)


# ============================================================================
# Router 系统提示词
# ============================================================================

ROUTER_SYSTEM_PROMPT = """你是一个智能路由助手，负责分析用户意图并决定下一步行动。

## 你的职责
1. 理解用户的请求意图
2. 决定是否需要调用专业 Agent
3. 生成友好的回复

## 可用的 Agent
- **xhs_agent**: 小红书内容生成专家
  - 可以生成小红书笔记（标题、正文、配图）
  - 支持发布到小红书平台
  - 触发关键词：小红书、笔记、发布、生成内容、写一篇等

## 决策规则
1. **xhs_agent**: 当用户想要创建、生成或发布小红书内容时
2. **wait**: 当需要用户提供更多信息或等待用户输入时
3. **end**: 当对话可以自然结束时（如用户说再见、完成任务等）

## 输出格式
你需要以 JSON 格式输出决策结果，包含以下字段：
- next_agent: "xhs_agent" | "wait" | "end"
- intent: 识别的意图类型
- reasoning: 决策理由
- response: 给用户的回复
- extracted_params: 从用户消息中提取的参数（如内容描述、图片数量等）
- confidence: 决策置信度 (0-1)

## 示例

用户: "帮我写一篇关于秋天穿搭的小红书"
输出:
```json
{
  "next_agent": "xhs_agent",
  "intent": "create_content",
  "reasoning": "用户明确要求生成小红书内容，主题是秋天穿搭",
  "response": "好的，我来帮你生成一篇关于秋天穿搭的小红书笔记~",
  "extracted_params": {"description": "秋天穿搭", "image_count": 3},
  "confidence": 0.95
}
```

用户: "再见"
输出:
```json
{
  "next_agent": "end",
  "intent": "casual_chat",
  "reasoning": "用户表示结束对话",
  "response": "再见！有需要随时找我哦~ 👋",
  "extracted_params": {},
  "confidence": 1.0
}
```

用户: "你好"
输出:
```json
{
  "next_agent": "wait",
  "intent": "casual_chat",
  "reasoning": "用户打招呼，等待进一步指令",
  "response": "你好！我是你的小红书内容助手，可以帮你生成精美的小红书笔记。需要我帮你创作什么内容吗？✨",
  "extracted_params": {},
  "confidence": 1.0
}
```
"""


# ============================================================================
# Router 输出模型（用于结构化输出）
# ============================================================================

class RouterOutput(BaseModel):
    """Router LLM 输出结构"""
    next_agent: str = Field(
        description="下一个要执行的 Agent: xhs_agent, wait, end"
    )
    intent: str = Field(
        default="unknown",
        description="识别的意图类型"
    )
    reasoning: str = Field(
        default="",
        description="决策理由"
    )
    response: str = Field(
        default="",
        description="给用户的回复"
    )
    extracted_params: dict[str, Any] = Field(
        default_factory=dict,
        description="提取的参数"
    )
    confidence: float = Field(
        default=1.0,
        description="置信度"
    )


# ============================================================================
# Router Agent
# ============================================================================

@AgentRegistry.register("router")
class RouterAgent(BaseAgent):
    """Router Agent - 智能路由与意图分析
    
    作为图的入口节点，负责：
    1. 分析用户意图
    2. 决定路由方向
    3. 生成回复消息
    
    决策结果通过 RouterDecision 传递给下游节点
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_model: str = "qwen-plus",
        temperature: float = 0.3,  # Router 使用较低温度以保证稳定性
    ):
        """初始化 Router Agent"""
        super().__init__(
            config=config,
            name="router",
            description="智能路由与意图分析 Agent",
            llm_model=llm_model,
            temperature=temperature,
        )
        
        # 设置系统提示词
        self.system_prompt = ROUTER_SYSTEM_PROMPT
        
        # 初始化结构化输出 LLM
        self._structured_llm = None
    
    @property
    def structured_llm(self):
        """获取支持结构化输出的 LLM"""
        if self._structured_llm is None:
            self._structured_llm = self.llm.with_structured_output(RouterOutput)
        return self._structured_llm
    
    async def _execute(self, state: AgentState) -> dict[str, Any]:
        """执行路由决策
        
        流程：
        1. 检查任务状态（如果已完成，直接路由到 wait）
        2. 获取用户消息
        3. 调用 LLM 分析意图
        4. 生成 RouterDecision
        5. 返回更新后的状态
        """
        messages = state.get("messages", [])
        task_context = state.get("task_context")
        user_input = get_last_human_message(state)
        
        # 🔥 关键修复：如果任务已完成，直接路由到 wait，避免重复执行
        if task_context:
            from ..core.models import TaskStatus
            if task_context.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                self.logger.info(
                    f"Task already {task_context.status.value}, routing to wait",
                    task_id=task_context.task_id
                )
                decision = RouterDecision(
                    next_agent=NextAgent.WAIT,
                    intent=IntentType.QUERY_STATUS,
                    reasoning=f"任务已完成（状态：{task_context.status.value}），等待用户新输入",
                    response="任务已完成！还有什么需要我帮助的吗？",
                    confidence=1.0,
                )
                return {
                    "messages": [AIMessage(content=decision.response)],
                    "decision": decision,
                    "current_agent": "router",
                    "iteration_count": state.get("iteration_count", 0) + 1,
                }
        
        self.logger.info(
            "Router analyzing intent",
            user_input=user_input[:50] if user_input else None
        )
        
        try:
            # 调用 LLM 进行结构化决策
            messages_with_system = self.get_messages_with_system(messages)
            output: RouterOutput = await self.structured_llm.ainvoke(messages_with_system)
            
            # 转换为 RouterDecision
            decision = self._create_decision(output)
            
            # 🔥 额外检查：如果任务已完成但 LLM 仍然决定执行 Agent，强制改为 wait
            if task_context and task_context.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                if decision.next_agent == NextAgent.XHS_AGENT:
                    self.logger.warning(
                        "LLM decided to execute agent but task is completed, overriding to wait"
                    )
                    decision.next_agent = NextAgent.WAIT
                    decision.reasoning = f"任务已完成，等待用户新输入。原决策：{decision.reasoning}"
                    decision.response = "任务已完成！还有什么需要我帮助的吗？"
            
            self.logger.info(
                "Router decision made",
                next_agent=decision.next_agent.value,
                intent=decision.intent.value,
                confidence=decision.confidence
            )
            
            # 创建 AI 回复消息
            ai_message = AIMessage(content=decision.response)
            
            # 创建/更新任务上下文
            task_context = self._create_task_context(state, decision)
            
            return {
                "messages": [ai_message],
                "decision": decision,
                "current_agent": decision.next_agent.value,
                "task_context": task_context,
                "iteration_count": state.get("iteration_count", 0) + 1,
            }
            
        except Exception as e:
            self.logger.error(f"Router decision failed: {e}")
            # 出错时返回等待状态
            return self._create_fallback_response(state, str(e))
    
    def _create_decision(self, output: RouterOutput) -> RouterDecision:
        """从 LLM 输出创建 RouterDecision"""
        # 映射 next_agent
        next_agent_map = {
            "xhs_agent": NextAgent.XHS_AGENT,
            "wait": NextAgent.WAIT,
            "end": NextAgent.END,
        }
        next_agent = next_agent_map.get(output.next_agent, NextAgent.WAIT)
        
        # 映射 intent
        intent_map = {
            "create_content": IntentType.CREATE_CONTENT,
            "query_status": IntentType.QUERY_STATUS,
            "get_help": IntentType.GET_HELP,
            "casual_chat": IntentType.CASUAL_CHAT,
            "feedback": IntentType.FEEDBACK,
        }
        intent = intent_map.get(output.intent, IntentType.UNKNOWN)
        
        return RouterDecision(
            next_agent=next_agent,
            intent=intent,
            reasoning=output.reasoning,
            response=output.response,
            extracted_params=output.extracted_params,
            confidence=output.confidence,
        )
    
    def _create_task_context(
        self,
        state: AgentState,
        decision: RouterDecision
    ) -> Optional[TaskContext]:
        """创建或更新任务上下文"""
        existing_context = state.get("task_context")
        
        # 如果决定调用 Agent，创建新的任务上下文
        if decision.next_agent == NextAgent.XHS_AGENT:
            import uuid
            return TaskContext(
                task_id=str(uuid.uuid4())[:8],
                task_type="xhs_content",
                status=TaskStatus.PENDING,
                params=decision.extracted_params,
            )
        
        # 否则保持现有上下文
        return existing_context
    
    def _create_fallback_response(
        self,
        state: AgentState,
        error: str
    ) -> dict[str, Any]:
        """创建降级响应"""
        decision = RouterDecision(
            next_agent=NextAgent.WAIT,
            intent=IntentType.UNKNOWN,
            reasoning=f"处理出错: {error}",
            response="抱歉，我遇到了一点问题。请再说一次您的需求？",
            confidence=0.0,
        )
        
        return {
            "messages": [AIMessage(content=decision.response)],
            "decision": decision,
            "current_agent": "router",
            "iteration_count": state.get("iteration_count", 0) + 1,
        }


# ============================================================================
# 便捷创建函数
# ============================================================================

def create_router_agent(
    llm_model: str = "qwen-plus",
    temperature: float = 0.3,
) -> RouterAgent:
    """创建 Router Agent 实例
    
    Args:
        llm_model: LLM 模型名称
        temperature: 温度参数
    
    Returns:
        RouterAgent 实例
    
    Example:
        >>> router = create_router_agent()
        >>> workflow.add_node("router", router)
    """
    return RouterAgent(
        llm_model=llm_model,
        temperature=temperature,
    )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "RouterAgent",
    "RouterOutput",
    "create_router_agent",
    "ROUTER_SYSTEM_PROMPT",
]
