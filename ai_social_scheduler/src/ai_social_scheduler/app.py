"""应用主入口 - 集成新架构

重构核心：统一的应用初始化和管理
"""

from typing import Optional

from .config import load_config
from .graph import GraphBuilder, GraphExecutor
from .nodes import NodeFactory, NodeRegistry
from .orchestrator import Orchestrator
from .router import RouterSystem, RouterStrategy
from .state import StateManager
from .tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 应用类
# ============================================================================

class SocialSchedulerApp:
    """社交内容调度器应用
    
    核心职责：
    1. 初始化所有组件
    2. 加载配置
    3. 构建图
    4. 提供统一接口
    
    使用方式：
    ```python
    app = SocialSchedulerApp()
    await app.initialize()
    
    response = await app.chat(
        user_input="帮我写一篇小红书笔记",
        thread_id="user_123"
    )
    ```
    """
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        router_strategy: str = RouterStrategy.RULE_FIRST,
    ):
        """初始化应用
        
        Args:
            config_dir: 配置目录
            router_strategy: 路由策略
        """
        self.config_dir = config_dir
        self.router_strategy = router_strategy
        
        # 组件
        self.node_registry: Optional[NodeRegistry] = None
        self.node_factory: Optional[NodeFactory] = None
        self.router_system: Optional[RouterSystem] = None
        self.orchestrator: Optional[Orchestrator] = None
        self.state_manager: Optional[StateManager] = None
        self.graph_builder: Optional[GraphBuilder] = None
        self.graph_executor: Optional[GraphExecutor] = None
        
        # 状态
        self._initialized = False
        
        logger.info("SocialSchedulerApp created")
    
    # ========================================================================
    # 初始化
    # ========================================================================
    
    async def initialize(self):
        """初始化应用"""
        if self._initialized:
            logger.warning("App already initialized")
            return
        
        logger.info("Initializing SocialSchedulerApp...")
        
        # 1. 加载配置
        logger.info("Loading configuration...")
        routes, nodes = load_config(self.config_dir)
        logger.info(f"Loaded {len(routes)} routes and {len(nodes)} nodes")
        
        # 2. 初始化节点系统
        logger.info("Initializing node system...")
        self.node_registry = NodeRegistry()
        
        # 注册节点配置
        for node_config in nodes:
            self.node_registry.register_config(node_config)
        
        self.node_factory = NodeFactory(registry=self.node_registry)
        
        # 注册中间件
        from .middleware import LoggingMiddleware, RetryMiddleware
        self.node_factory.register_middleware("logging", LoggingMiddleware())
        self.node_factory.register_middleware("retry", RetryMiddleware())
        
        logger.info("Node system initialized")
        
        # 3. 初始化路由系统
        logger.info("Initializing router system...")
        available_nodes = self.node_registry.list_active_nodes()
        
        self.router_system = RouterSystem(
            routes=routes,
            strategy=self.router_strategy,
            enable_llm=True,
            available_nodes=available_nodes,
        )
        logger.info("Router system initialized")
        
        # 4. 初始化调度器
        logger.info("Initializing orchestrator...")
        self.orchestrator = Orchestrator(
            router_system=self.router_system
        )
        logger.info("Orchestrator initialized")
        
        # 5. 初始化状态管理器
        logger.info("Initializing state manager...")
        self.state_manager = StateManager()
        logger.info("State manager initialized")
        
        # 6. 构建图
        logger.info("Building graph...")
        self.graph_builder = GraphBuilder(
            orchestrator=self.orchestrator,
            node_registry=self.node_registry,
            node_factory=self.node_factory,
            checkpointer=self.state_manager.checkpointer,
        )
        
        compiled_graph = await self.graph_builder.compile()
        logger.info("Graph compiled")
        
        # 7. 初始化图执行器
        self.graph_executor = GraphExecutor(compiled_graph)
        logger.info("Graph executor initialized")
        
        self._initialized = True
        logger.info("✅ SocialSchedulerApp initialized successfully")
    
    # ========================================================================
    # 主要接口
    # ========================================================================
    
    async def chat(
        self,
        user_input: str,
        thread_id: str,
        user_id: Optional[str] = None,
    ) -> str:
        """对话接口
        
        Args:
            user_input: 用户输入
            thread_id: 会话 ID
            user_id: 用户 ID
        
        Returns:
            AI 响应
        """
        if not self._initialized:
            raise RuntimeError("App not initialized. Call initialize() first.")
        
        logger.info(
            "Chat request",
            thread_id=thread_id,
            user_id=user_id,
            input_length=len(user_input)
        )
        
        # 执行图
        response = await self.graph_executor.invoke(
            user_input=user_input,
            thread_id=thread_id,
            user_id=user_id,
        )
        
        return response
    
    async def get_history(self, thread_id: str) -> list:
        """获取对话历史
        
        Args:
            thread_id: 会话 ID
        
        Returns:
            消息列表
        """
        if not self._initialized:
            raise RuntimeError("App not initialized")
        
        return await self.graph_executor.get_history(thread_id)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self._initialized:
            return {"initialized": False}
        
        return {
            "initialized": True,
            "nodes": len(self.node_registry.list_nodes()),
            "active_nodes": len(self.node_registry.list_active_nodes()),
            "queue": self.orchestrator.get_queue_stats(),
            "state": self.state_manager.stats(),
        }


# ============================================================================
# 全局实例
# ============================================================================

_app_instance: Optional[SocialSchedulerApp] = None


def get_app(
    config_dir: Optional[str] = None,
    router_strategy: str = RouterStrategy.RULE_FIRST,
) -> SocialSchedulerApp:
    """获取应用实例（单例）"""
    global _app_instance
    
    if _app_instance is None:
        _app_instance = SocialSchedulerApp(
            config_dir=config_dir,
            router_strategy=router_strategy,
        )
    
    return _app_instance


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "SocialSchedulerApp",
    "get_app",
]

