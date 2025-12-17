"""子图基类 - 基于LangGraph

子图 = 多个Agent/节点的组合，用于实现复杂业务流程
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from langgraph.graph import StateGraph, END

from ..tools.logging import get_logger

logger = get_logger(__name__)


class BaseSubgraph(ABC):
    """LangGraph子图基类
    
    职责：
    1. 组合多个Agent/节点
    2. 定义状态Schema和流转规则
    3. 实现业务流程编排
    4. 支持流式输出
    
    子类需要实现：
    - _build_graph: 构建图结构
    - _define_state_schema: 定义状态Schema
    
    使用示例：
        class MySubgraph(BaseSubgraph):
            def __init__(self):
                super().__init__(name="my_subgraph")
            
            def _define_state_schema(self):
                return MyState
            
            async def _build_graph(self):
                workflow = StateGraph(self._define_state_schema())
                # ... 添加节点和边
                return workflow
        
        subgraph = MySubgraph()
        await subgraph.initialize()
        result = await subgraph.invoke({"input": "data"})
    """
    
    def __init__(self, name: str):
        """初始化子图
        
        Args:
            name: 子图名称
        """
        self.name = name
        self._graph: Optional[Any] = None  # CompiledGraph类型（StateGraph编译后的结果）
        self._initialized = False
        self.logger = logger
    
    @abstractmethod
    async def _build_graph(self) -> StateGraph:
        """构建图结构（子类必须实现）
        
        Returns:
            StateGraph实例
        
        示例：
            async def _build_graph(self):
                workflow = StateGraph(MyState)
                workflow.add_node("step1", self._step1_node)
                workflow.add_node("step2", self._step2_node)
                workflow.set_entry_point("step1")
                workflow.add_edge("step1", "step2")
                workflow.add_edge("step2", END)
                return workflow
        """
        pass
    
    @abstractmethod
    def _define_state_schema(self) -> type:
        """定义状态Schema（子类必须实现）
        
        Returns:
            状态Schema类型（TypedDict）
        
        示例：
            class MyState(TypedDict):
                input: str
                output: str
                messages: List[BaseMessage]
            
            def _define_state_schema(self):
                return MyState
        """
        pass
    
    async def initialize(self):
        """初始化子图
        
        步骤：
        1. 构建图结构
        2. 编译图
        """
        if self._initialized:
            self.logger.debug(f"Subgraph '{self.name}' already initialized")
            return
        
        try:
            self.logger.info(f"Initializing Subgraph '{self.name}'...")
            
            # 1. 构建图
            graph = await self._build_graph()
            
            # 2. 编译图
            self._graph = graph.compile()
            
            self._initialized = True
            self.logger.info(f"Subgraph '{self.name}' initialized successfully")
            
        except Exception as e:
            self.logger.error(
                f"Failed to initialize Subgraph '{self.name}'",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def invoke(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """调用子图（非流式）
        
        Args:
            input: 输入状态
        
        Returns:
            最终状态
        
        使用示例：
            result = await subgraph.invoke({
                "description": "写一篇文章",
                "image_count": 3,
            })
        """
        await self.initialize()
        
        if not self._graph:
            raise RuntimeError(f"Subgraph '{self.name}' not properly initialized")
        
        try:
            self.logger.info(
                f"Subgraph '{self.name}' invoking",
                input_keys=list(input.keys())
            )
            
            result = await self._graph.ainvoke(input)
            
            self.logger.info(
                f"Subgraph '{self.name}' invocation completed",
                result_keys=list(result.keys()) if isinstance(result, dict) else []
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"Subgraph '{self.name}' invocation failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    async def stream(self, input: Dict[str, Any]):
        """流式调用子图
        
        Args:
            input: 输入状态
        
        Yields:
            每个节点执行后的状态
        
        使用示例：
            async for state in subgraph.stream({"input": "data"}):
                print(f"Current state: {state}")
        """
        await self.initialize()
        
        if not self._graph:
            raise RuntimeError(f"Subgraph '{self.name}' not properly initialized")
        
        try:
            self.logger.info(
                f"Subgraph '{self.name}' streaming",
                input_keys=list(input.keys())
            )
            
            async for state in self._graph.astream(input):
                yield state
            
            self.logger.info(f"Subgraph '{self.name}' streaming completed")
            
        except Exception as e:
            self.logger.error(
                f"Subgraph '{self.name}' streaming failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    @property
    def graph(self) -> Any:
        """获取编译后的图（用于嵌套子图）
        
        Returns:
            编译后的图实例（StateGraph编译后的结果）
        
        Raises:
            RuntimeError: 如果子图未初始化
        """
        if not self._initialized:
            raise RuntimeError(
                f"Subgraph '{self.name}' not initialized. "
                f"Call await subgraph.initialize() first."
            )
        return self._graph
    
    async def close(self):
        """关闭子图并清理资源"""
        self._graph = None
        self._initialized = False
        self.logger.info(f"Subgraph '{self.name}' closed")
    
    def __repr__(self) -> str:
        """字符串表示"""
        status = "initialized" if self._initialized else "not initialized"
        return f"<{self.__class__.__name__} name='{self.name}' status={status}>"

