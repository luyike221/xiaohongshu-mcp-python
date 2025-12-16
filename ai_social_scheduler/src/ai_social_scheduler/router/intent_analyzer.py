"""意图分析器 - LLM 驱动的意图识别

重构核心：使用 LLM 进行复杂意图分析
"""

from typing import Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..client import QwenClient
from ..core.route import RouteDecision
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# LLM 输出模型
# ============================================================================

class IntentAnalysisOutput(BaseModel):
    """LLM 意图分析输出"""
    
    intent: str = Field(
        description="识别的意图类型"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="置信度"
    )
    
    reasoning: str = Field(
        default="",
        description="分析理由"
    )
    
    response: str = Field(
        default="",
        description="给用户的回复"
    )
    
    extracted_params: dict[str, Any] = Field(
        default_factory=dict,
        description="提取的参数"
    )
    
    suggested_nodes: list[str] = Field(
        default_factory=list,
        description="建议的目标节点"
    )
    
    should_wait: bool = Field(
        default=False,
        description="是否需要等待用户输入"
    )


# ============================================================================
# 意图分析器
# ============================================================================

class IntentAnalyzer:
    """意图分析器 - LLM 驱动的意图识别
    
    核心职责：
    1. 使用 LLM 分析用户意图
    2. 提取关键参数
    3. 生成回复内容
    4. 建议路由目标
    
    设计理念：
    - 灵活：支持自定义提示词
    - 结构化：使用 Pydantic 模型约束输出
    - 可配置：支持不同的 LLM 模型
    """
    
    def __init__(
        self,
        llm_model: str = "qwen-plus",
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
        available_nodes: Optional[list[str]] = None,
    ):
        """初始化意图分析器
        
        Args:
            llm_model: LLM 模型名称
            temperature: 温度参数（较低保证稳定性）
            system_prompt: 自定义系统提示词
            available_nodes: 可用的节点列表
        """
        self.llm_model = llm_model
        self.temperature = temperature
        self.available_nodes = available_nodes or []
        
        # 初始化 LLM 客户端
        self._llm = None
        self._structured_llm = None
        
        # 系统提示词
        self.system_prompt = system_prompt or self._build_default_prompt()
        
        logger.info(
            "IntentAnalyzer initialized",
            llm_model=llm_model,
            temperature=temperature,
            available_nodes_count=len(self.available_nodes)
        )
    
    @property
    def llm(self):
        """获取 LLM 客户端（延迟初始化）"""
        if self._llm is None:
            self._llm = QwenClient(
                model=self.llm_model,
                temperature=self.temperature
            ).client
        return self._llm
    
    @property
    def structured_llm(self):
        """获取结构化输出的 LLM"""
        if self._structured_llm is None:
            self._structured_llm = self.llm.with_structured_output(IntentAnalysisOutput)
        return self._structured_llm
    
    def _build_default_prompt(self) -> str:
        """构建默认系统提示词"""
        nodes_info = ""
        if self.available_nodes:
            nodes_info = f"\n\n## 可用节点\n" + "\n".join(
                f"- **{node}**" for node in self.available_nodes
            )
        
        return f"""你是一个智能意图分析助手，负责理解用户请求并提供决策建议。

## 你的职责
1. 深入理解用户的真实意图
2. 提取关键参数和信息
3. 推荐合适的处理节点
4. 生成友好的回复{nodes_info}

## 输出格式
你需要以 JSON 格式输出分析结果，包含以下字段：
- **intent**: 识别的意图类型（如：create_content, query, chat 等）
- **confidence**: 置信度 (0-1)
- **reasoning**: 分析理由
- **response**: 给用户的友好回复
- **extracted_params**: 提取的参数（如描述、数量等）
- **suggested_nodes**: 建议的目标节点列表
- **should_wait**: 是否需要等待用户提供更多信息

## 意图类型参考
- **create_content**: 创建内容（小红书笔记、文章等）
- **query**: 查询信息（状态查询、数据查询等）
- **analysis**: 分析需求（数据分析、趋势分析等）
- **chat**: 闲聊或打招呼
- **help**: 寻求帮助
- **unknown**: 无法识别的意图

## 示例

用户: "帮我写一篇关于秋天穿搭的小红书笔记"
输出:
```json
{{
  "intent": "create_content",
  "confidence": 0.95,
  "reasoning": "用户明确要求创建小红书内容，主题是秋天穿搭",
  "response": "好的，我来帮你生成一篇关于秋天穿搭的小红书笔记~",
  "extracted_params": {{"description": "秋天穿搭", "platform": "小红书"}},
  "suggested_nodes": ["xhs_agent"],
  "should_wait": false
}}
```

用户: "你好"
输出:
```json
{{
  "intent": "chat",
  "confidence": 1.0,
  "reasoning": "用户打招呼，等待进一步指令",
  "response": "你好！我是你的智能助手，可以帮你生成小红书笔记等内容。需要我帮你做什么吗？✨",
  "extracted_params": {{}},
  "suggested_nodes": [],
  "should_wait": true
}}
```

## 注意事项
- 如果用户意图不明确，设置 should_wait=true 并请求更多信息
- 尽可能提取有用的参数
- 置信度低于 0.5 时，建议等待或请求澄清
- 回复要友好、自然、有帮助性
"""
    
    async def analyze(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None,
        messages: Optional[list[BaseMessage]] = None,
    ) -> RouteDecision:
        """分析用户意图
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            messages: 历史消息
        
        Returns:
            RouteDecision: 路由决策结果
        """
        try:
            logger.info(
                "Analyzing intent",
                user_input_length=len(user_input),
                has_context=context is not None,
                has_history=messages is not None
            )
            
            # 构建消息列表
            msg_list = [SystemMessage(content=self.system_prompt)]
            
            # 添加历史消息（如果有）
            if messages:
                # 只取最近的几条消息，避免 token 过多
                recent_messages = messages[-5:]
                msg_list.extend(recent_messages)
            
            # 添加当前用户输入
            msg_list.append(HumanMessage(content=user_input))
            
            # 调用 LLM
            output: IntentAnalysisOutput = await self.structured_llm.ainvoke(msg_list)
            
            logger.info(
                "Intent analyzed",
                intent=output.intent,
                confidence=output.confidence,
                suggested_nodes=output.suggested_nodes
            )
            
            # 转换为 RouteDecision
            decision = RouteDecision(
                intent=output.intent,
                confidence=output.confidence,
                reasoning=output.reasoning,
                response=output.response,
                extracted_params=output.extracted_params,
                target_nodes=output.suggested_nodes,
                should_wait=output.should_wait,
                metadata={
                    "analyzer": "llm",
                    "model": self.llm_model,
                }
            )
            
            logger.info(
                "Intent analysis completed",
                intent=output.intent,
                confidence=output.confidence,
                suggested_nodes=output.suggested_nodes,
                suggested_nodes_count=len(output.suggested_nodes),
                should_wait=output.should_wait
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}", exc_info=True)
            
            # 返回降级决策
            return RouteDecision(
                intent="unknown",
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}",
                response="抱歉，我遇到了一点问题。请再说一次您的需求？",
                should_wait=True,
                metadata={"error": str(e)}
            )
    
    def update_available_nodes(self, nodes: list[str]):
        """更新可用节点列表"""
        self.available_nodes = nodes
        self.system_prompt = self._build_default_prompt()
        # 清除缓存的 LLM 实例，使其使用新的提示词
        self._structured_llm = None
        
        logger.info("Available nodes updated", nodes=nodes)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "IntentAnalyzer",
    "IntentAnalysisOutput",
]

