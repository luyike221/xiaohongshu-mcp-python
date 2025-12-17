"""Agent基类 - 基于LangGraph

新架构核心：
1. Agent = LLM + Tools
2. Agent自主决策调用哪个工具
3. 基于LangGraph的create_agent API
4. 统一的接口和生命周期管理
"""

from typing import List, Optional, Any, Dict
from abc import ABC, abstractmethod
import asyncio

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.tools import BaseTool

from ..client import QwenClient
from ..mcp.registry import mcp_registry
from ..tools.logging import get_logger

logger = get_logger(__name__)


class BaseLangGraphAgent(ABC):
    """LangGraph Agent基类
    
    职责：
    1. 管理LangChain Tools（从MCP Registry获取）
    2. 创建LangGraph Agent（使用create_agent）
    3. 提供统一的execute接口
    4. 支持流式输出
    
    子类只需实现：
    - _default_system_prompt: 定义Agent的系统提示词
    - tool_categories: 指定需要的工具类别
    
    使用示例：
        class MyAgent(BaseLangGraphAgent):
            def __init__(self):
                super().__init__(
                    name="my_agent",
                    tool_categories=["content", "image"]
                )
            
            def _default_system_prompt(self):
                return "你是一个xxx助手..."
        
        agent = MyAgent()
        await agent.initialize()
        result = await agent.invoke("帮我完成任务")
    """
    
    def __init__(
        self,
        name: str,
        tool_categories: List[str],
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        execution_timeout: Optional[int] = None,
    ):
        """初始化Agent
        
        Args:
            name: Agent名称
            tool_categories: 需要的工具类别列表（如 ["content", "image"]）
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数
            llm_api_key: LLM API密钥（可选）
            system_prompt: 系统提示词（可选，默认使用_default_system_prompt）
            execution_timeout: Agent执行超时时间（秒），None表示使用默认值（LLM timeout * 2）
        """
        self.name = name
        self.tool_categories = tool_categories
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_api_key = llm_api_key
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.execution_timeout = execution_timeout
        
        self._tools: List[BaseTool] = []
        self._agent = None
        self._llm_client: Optional[QwenClient] = None
        self._initialized = False
        self.logger = logger
    
    @abstractmethod
    def _default_system_prompt(self) -> str:
        """默认系统提示词（子类必须实现）
        
        Returns:
            系统提示词字符串
        """
        pass
    
    async def initialize(self):
        """初始化Agent
        
        步骤：
        1. 初始化MCP工具注册表
        2. 获取所需的工具
        3. 初始化LLM客户端
        4. 创建LangGraph Agent
        """
        if self._initialized:
            self.logger.debug(f"Agent '{self.name}' already initialized")
            return
        
        try:
            self.logger.info(f"Initializing Agent '{self.name}'...")
            
            # 1. 确保MCP工具已注册
            if not mcp_registry.is_initialized():
                await mcp_registry.initialize()
            
            # 2. 获取所需的工具
            self._tools = mcp_registry.get_tools_by_categories(self.tool_categories)
            
            if not self._tools:
                self.logger.warning(
                    f"Agent '{self.name}' has no tools",
                    categories=self.tool_categories
                )
            else:
                self.logger.info(
                    f"Agent '{self.name}' loaded tools",
                    tool_count=len(self._tools),
                    tool_names=[tool.name for tool in self._tools],
                    categories=self.tool_categories
                )
            
            # 3. 初始化LLM客户端
            self._llm_client = QwenClient(
                model=self.llm_model,
                temperature=self.llm_temperature,
                api_key=self.llm_api_key
            )
            self.logger.info(
                f"Agent '{self.name}' initialized LLM",
                model=self.llm_model,
                temperature=self.llm_temperature
            )
            
            # 4. 创建Agent（使用LangGraph的create_agent API）
            self._agent = create_agent(
                model=self._llm_client.client,
                tools=self._tools,
                system_prompt=self.system_prompt,
            )
            
            self._initialized = True
            self.logger.info(f"Agent '{self.name}' initialized successfully")
            
        except Exception as e:
            self.logger.error(
                f"Failed to initialize Agent '{self.name}'",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def execute(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """执行Agent（底层方法）
        
        Args:
            messages: 消息列表（LangChain格式）
        
        Returns:
            执行结果字典，包含messages等字段
        """
        await self.initialize()
        
        if not self._agent:
            raise RuntimeError(f"Agent '{self.name}' not properly initialized")
        
        try:
            self.logger.info(
                f"Agent '{self.name}' executing",
                message_count=len(messages),
                first_message=str(messages[0].content)[:100] if messages else "N/A"
            )
            
            # 执行Agent（带超时保护）
            if self.execution_timeout is not None:
                timeout = self.execution_timeout
            else:
                # 默认超时：LLM timeout * 2（Agent可能需要多次工具调用）
                timeout = (self._llm_client.timeout if self._llm_client else 120) * 2
            
            self.logger.debug(f"Agent '{self.name}' execution timeout: {timeout} seconds")
            
            result = await asyncio.wait_for(
                self._agent.ainvoke({"messages": messages}),
                timeout=timeout
            )
            
            self.logger.info(
                f"Agent '{self.name}' execution completed",
                result_keys=list(result.keys()) if isinstance(result, dict) else []
            )
            
            return result
            
        except asyncio.TimeoutError:
            if self.execution_timeout is not None:
                timeout = self.execution_timeout
            else:
                timeout = (self._llm_client.timeout if self._llm_client else 120) * 2
            
            self.logger.error(
                f"Agent '{self.name}' execution timeout",
                timeout_seconds=timeout
            )
            raise TimeoutError(f"Agent execution exceeded {timeout} seconds")
        
        except Exception as e:
            self.logger.error(
                f"Agent '{self.name}' execution failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    async def invoke(self, input: str, **kwargs) -> Dict[str, Any]:
        """便捷调用接口（推荐使用）
        
        Args:
            input: 用户输入文本
            **kwargs: 额外参数（未来扩展）
        
        Returns:
            执行结果
        
        使用示例：
            agent = MyAgent()
            result = await agent.invoke("帮我生成一篇文章")
        """
        messages = [HumanMessage(content=input)]
        return await self.execute(messages)
    
    async def stream(self, input: str):
        """流式执行Agent（暂未实现）
        
        TODO: 实现流式输出
        """
        await self.initialize()
        raise NotImplementedError("Streaming not yet implemented")
    
    @property
    def agent(self):
        """获取底层Agent实例（用于子图组合）
        
        Returns:
            LangGraph Agent实例
        
        Raises:
            RuntimeError: 如果Agent未初始化
        """
        if not self._initialized:
            raise RuntimeError(
                f"Agent '{self.name}' not initialized. "
                f"Call await agent.initialize() first."
            )
        return self._agent
    
    @property
    def tools(self) -> List[BaseTool]:
        """获取Agent的工具列表
        
        Returns:
            工具列表
        """
        return self._tools
    
    def get_tool_names(self) -> List[str]:
        """获取Agent的工具名称列表
        
        Returns:
            工具名称列表
        """
        return [tool.name for tool in self._tools]
    
    async def close(self):
        """关闭Agent并清理资源"""
        self._agent = None
        self._llm_client = None
        self._tools = []
        self._initialized = False
        self.logger.info(f"Agent '{self.name}' closed")
    
    def __repr__(self) -> str:
        """字符串表示"""
        status = "initialized" if self._initialized else "not initialized"
        tool_count = len(self._tools) if self._tools else 0
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"status={status} "
            f"tools={tool_count}>"
        )

