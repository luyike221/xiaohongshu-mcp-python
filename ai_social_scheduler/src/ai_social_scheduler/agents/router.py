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

## 重要规则
**无论用户输入什么内容，都必须路由到 xhs_agent 生成小红书内容。**

## 你的职责
1. 理解用户的请求意图
2. **总是**调用 xhs_agent 生成小红书内容
3. 从用户消息中提取内容主题和参数
4. 生成友好的回复

## 可用的 Agent
- **xhs_agent**: 小红书内容生成专家（唯一可用）
  - 可以生成小红书笔记（标题、正文、配图）
  - 支持发布到小红书平台
  - **无论用户说什么，都要路由到这里**

## 决策规则
1. **xhs_agent**: **所有情况都必须路由到这里**
   - 如果用户明确提到小红书相关内容，直接提取主题
   - 如果用户只是打招呼或闲聊，将用户消息作为内容主题
   - 如果用户说"再见"或结束语，将对话历史或最后的话题作为内容主题
   - 如果用户输入任何其他内容，都将其作为小红书内容主题

## 输出格式
你需要以 JSON 格式输出决策结果，包含以下字段：
- next_agent: **必须始终是 "xhs_agent"**
- intent: 识别的意图类型（通常是 "create_content"）
- reasoning: 决策理由（说明如何将用户输入转换为小红书内容主题）
- response: 给用户的回复（表示正在生成小红书内容）
- extracted_params: 从用户消息中提取的参数（description 字段必须包含内容主题）
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
  "next_agent": "xhs_agent",
  "intent": "create_content",
  "reasoning": "用户说再见，将对话历史或最近的话题作为小红书内容主题",
  "response": "好的，我来为你生成一篇小红书笔记~",
  "extracted_params": {"description": "再见", "image_count": 3},
  "confidence": 0.9
}
```

用户: "你好"
输出:
```json
{
  "next_agent": "xhs_agent",
  "intent": "create_content",
  "reasoning": "用户打招呼，将问候语作为内容主题生成小红书笔记",
  "response": "你好！我来为你生成一篇小红书笔记~",
  "extracted_params": {"description": "你好", "image_count": 3},
  "confidence": 0.9
}
```

用户: "今天天气真好"
输出:
```json
{
  "next_agent": "xhs_agent",
  "intent": "create_content",
  "reasoning": "用户提到天气，将其作为小红书内容主题",
  "response": "好的，我来为你生成一篇关于今天天气的小红书笔记~",
  "extracted_params": {"description": "今天天气真好", "image_count": 3},
  "confidence": 0.95
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
