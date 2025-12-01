"""Agent 基类定义

提供所有 Agent 的抽象基类，定义统一的接口和通用功能
支持可扩展的 Agent 架构
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from pydantic import BaseModel, Field

from ..core.models import AgentConfig, TaskContext, TaskStatus
from ..core.state import AgentState
from ..tools.logging import get_logger


# ============================================================================
# Agent 基类
# ============================================================================

class BaseAgent(ABC):
    """Agent 抽象基类
    
    所有 Agent 都应该继承此类并实现必要的方法
    
    设计模式：
    1. 模板方法模式 - 定义执行流程框架
    2. 策略模式 - 子类实现具体策略
    
    使用方式：
    ```python
    class MyAgent(BaseAgent):
        async def _execute(self, state: AgentState) -> dict:
            # 实现具体逻辑
            return {"messages": [...]}
    
    # 创建实例并作为 LangGraph 节点使用
    agent = MyAgent(config)
    workflow.add_node("my_agent", agent)
    ```
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        name: Optional[str] = None,
        description: str = "",
        llm_model: str = "qwen-plus",
        temperature: float = 0.7,
    ):
        """初始化 Agent
        
        Args:
            config: Agent 配置对象（优先使用）
            name: Agent 名称（如果未提供 config）
            description: Agent 描述
            llm_model: LLM 模型名称
            temperature: LLM 温度参数
        """
        if config:
            self.config = config
        else:
            self.config = AgentConfig(
                name=name or self.__class__.__name__,
                description=description,
                llm_model=llm_model,
                temperature=temperature,
            )
        
        self.name = self.config.name
        self.logger = get_logger(f"agent.{self.name}")
        self._llm = None
        self._llm_with_tools = None
        self._tools: list = []
        self._system_prompt: Optional[SystemMessage] = None
        
        self.logger.info(
            f"Agent initialized: {self.name}",
            config=self.config.model_dump()
        )
    
    # ========================================================================
    # 属性
    # ========================================================================
    
    @property
    def llm(self):
        """获取 LLM 客户端（延迟初始化）"""
        if self._llm is None:
            self._init_llm()
        return self._llm
    
    @property
    def llm_with_tools(self):
        """获取绑定工具的 LLM"""
        if self._llm_with_tools is None and self._tools:
            self._llm_with_tools = self.llm.bind_tools(self._tools)
        return self._llm_with_tools or self.llm
    
    @property
    def system_prompt(self) -> Optional[SystemMessage]:
        """获取系统提示词"""
        return self._system_prompt
    
    @system_prompt.setter
    def system_prompt(self, value: str | SystemMessage):
        """设置系统提示词"""
        if isinstance(value, str):
            self._system_prompt = SystemMessage(content=value)
        else:
            self._system_prompt = value
    
    # ========================================================================
    # 初始化方法
    # ========================================================================
    
    def _init_llm(self):
        """初始化 LLM 客户端"""
        from ..client import QwenClient
        
        client = QwenClient(
            model=self.config.llm_model,
            temperature=self.config.temperature
        )
        self._llm = client.client
    
    def register_tools(self, tools: list):
        """注册工具列表
        
        Args:
            tools: 工具列表
        """
        self._tools = tools
        # 重置绑定的 LLM
        self._llm_with_tools = None
        self.logger.debug(f"Registered {len(tools)} tools")
    
    # ========================================================================
    # 核心执行方法
    # ========================================================================
    
    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """作为 LangGraph 节点被调用
        
        这是模板方法，定义了执行流程：
        1. 前置处理
        2. 执行核心逻辑
        3. 后置处理
        4. 错误处理
        
        Args:
            state: 当前图状态
        
        Returns:
            状态更新字典
        """
        self.logger.info(
            f"Agent {self.name} invoked",
            message_count=len(state.get("messages", []))
        )
        
        try:
            # 前置处理
            state = await self._pre_process(state)
            
            # 执行核心逻辑
            result = await self._execute(state)
            
            # 后置处理
            result = await self._post_process(state, result)
            
            self.logger.info(f"Agent {self.name} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(
                f"Agent {self.name} failed",
                error=str(e),
                exc_info=True
            )
            return await self._handle_error(state, e)
    
    @abstractmethod
    async def _execute(self, state: AgentState) -> dict[str, Any]:
        """执行核心逻辑（子类必须实现）
        
        Args:
            state: 当前图状态
        
        Returns:
            状态更新字典，通常包含 "messages" 键
        """
        pass
    
    async def _pre_process(self, state: AgentState) -> AgentState:
        """前置处理（可选重写）
        
        默认不做任何处理
        """
        return state
    
    async def _post_process(
        self,
        state: AgentState,
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """后置处理（可选重写）
        
        默认不做任何处理
        """
        return result
    
    async def _handle_error(
        self,
        state: AgentState,
        error: Exception
    ) -> dict[str, Any]:
        """错误处理（可选重写）
        
        默认返回错误消息
        """
        error_message = AIMessage(
            content=f"抱歉，执行过程中遇到错误：{str(error)}"
        )
        
        # 更新任务上下文（如果存在）
        task_context = state.get("task_context")
        if task_context:
            task_context.mark_failed(str(error))
        
        return {
            "messages": [error_message],
            "task_context": task_context,
        }
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def get_messages_with_system(
        self,
        messages: Sequence[BaseMessage]
    ) -> list[BaseMessage]:
        """获取包含系统提示词的消息列表"""
        if self._system_prompt:
            return [self._system_prompt] + list(messages)
        return list(messages)
    
    async def invoke_llm(
        self,
        messages: Sequence[BaseMessage],
        with_tools: bool = False
    ) -> AIMessage:
        """调用 LLM
        
        Args:
            messages: 消息列表
            with_tools: 是否使用绑定工具的 LLM
        
        Returns:
            AI 响应消息
        """
        llm = self.llm_with_tools if with_tools else self.llm
        messages_with_system = self.get_messages_with_system(messages)
        return await llm.ainvoke(messages_with_system)
    
    def create_ai_message(self, content: str) -> AIMessage:
        """创建 AI 消息"""
        return AIMessage(content=content)
    
    def get_last_user_input(self, state: AgentState) -> Optional[str]:
        """获取最后一条用户输入"""
        from langchain_core.messages import HumanMessage
        
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, HumanMessage):
                return msg.content
        return None


# ============================================================================
# Agent 注册表
# ============================================================================

class AgentRegistry:
    """Agent 注册表
    
    用于管理和发现可用的 Agent
    支持动态注册和获取 Agent
    """
    
    _instance = None
    _agents: dict[str, type[BaseAgent]] = {}
    _instances: dict[str, BaseAgent] = {}
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: str):
        """注册 Agent 的装饰器
        
        Usage:
            @AgentRegistry.register("my_agent")
            class MyAgent(BaseAgent):
                ...
        """
        def decorator(agent_class: type[BaseAgent]):
            cls._agents[name] = agent_class
            return agent_class
        return decorator
    
    @classmethod
    def get_agent_class(cls, name: str) -> Optional[type[BaseAgent]]:
        """获取 Agent 类"""
        return cls._agents.get(name)
    
    @classmethod
    def get_agent(
        cls,
        name: str,
        config: Optional[AgentConfig] = None,
        **kwargs
    ) -> Optional[BaseAgent]:
        """获取或创建 Agent 实例
        
        Args:
            name: Agent 名称
            config: Agent 配置
            **kwargs: 其他初始化参数
        
        Returns:
            Agent 实例
        """
        # 如果已有实例，直接返回
        if name in cls._instances:
            return cls._instances[name]
        
        # 创建新实例
        agent_class = cls._agents.get(name)
        if agent_class:
            instance = agent_class(config=config, **kwargs)
            cls._instances[name] = instance
            return instance
        
        return None
    
    @classmethod
    def list_agents(cls) -> list[str]:
        """列出所有已注册的 Agent 名称"""
        return list(cls._agents.keys())
    
    @classmethod
    def clear(cls):
        """清除所有注册（主要用于测试）"""
        cls._agents.clear()
        cls._instances.clear()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "BaseAgent",
    "AgentRegistry",
]
