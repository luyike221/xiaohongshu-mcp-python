"""节点工厂 - 节点实例的创建和管理

重构核心：负责节点的实例化，支持依赖注入和中间件装配
"""

import importlib
from typing import Any, Optional, Type

from ..core.node import NodeConfig
from ..tools.logging import get_logger
from .base import BaseNode
from .registry import NodeRegistry

logger = get_logger(__name__)


# ============================================================================
# 节点工厂
# ============================================================================

class NodeFactory:
    """节点工厂 - 创建和管理节点实例
    
    核心职责：
    1. 创建节点实例
    2. 注入依赖
    3. 装配中间件
    4. 管理实例生命周期
    
    设计理念：
    - 工厂模式：集中创建逻辑
    - 依赖注入：解耦依赖关系
    - 缓存管理：复用实例
    - 动态加载：支持运行时加载
    """
    
    def __init__(
        self,
        registry: Optional[NodeRegistry] = None,
        enable_cache: bool = True,
    ):
        """初始化节点工厂
        
        Args:
            registry: 节点注册表（默认使用全局注册表）
            enable_cache: 是否启用实例缓存
        """
        self.registry = registry or NodeRegistry()
        self.enable_cache = enable_cache
        
        # 中间件池
        self._middleware_pool: dict[str, Any] = {}
        
        logger.info(
            "NodeFactory initialized",
            enable_cache=enable_cache
        )
    
    # ========================================================================
    # 创建节点
    # ========================================================================
    
    def create(
        self,
        node_id: str,
        config: Optional[NodeConfig] = None,
        middlewares: Optional[list] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> BaseNode:
        """创建节点实例
        
        Args:
            node_id: 节点ID
            config: 节点配置（如果不提供，从注册表获取）
            middlewares: 中间件列表
            use_cache: 是否使用缓存（默认使用工厂配置）
            **kwargs: 额外的初始化参数
        
        Returns:
            节点实例
        
        Raises:
            ValueError: 节点不存在或配置无效
        """
        # 确定是否使用缓存
        use_cache = self.enable_cache if use_cache is None else use_cache
        
        # 如果启用缓存，先尝试获取缓存实例
        if use_cache:
            cached = self.registry.get_cached_instance(node_id)
            if cached:
                logger.debug(f"Using cached node instance: {node_id}")
                return cached
        
        logger.info(f"Creating node instance: {node_id}")
        
        # 获取配置
        if config is None:
            config = self.registry.get_node_config(node_id)
            if config is None:
                raise ValueError(f"Node config not found: {node_id}")
        
        # 获取节点类
        node_class = self.registry.get_node_class(node_id)
        
        # 如果没有注册类，尝试动态加载
        if node_class is None:
            node_class = self._load_node_class(config)
        
        if node_class is None:
            raise ValueError(f"Node class not found: {node_id}")
        
        # 装配中间件
        if middlewares is None:
            middlewares = self._load_middlewares(config.middlewares)
        
        # 创建实例
        try:
            instance = node_class(
                config=config,
                middlewares=middlewares,
                **kwargs
            )
            
            logger.info(f"Node instance created: {node_id}")
            
            # 缓存实例
            if use_cache:
                self.registry.cache_instance(node_id, instance)
            
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create node: {node_id}, error: {e}", exc_info=True)
            raise ValueError(f"Failed to create node {node_id}: {e}")
    
    def create_batch(
        self,
        node_ids: list[str],
        **kwargs
    ) -> dict[str, BaseNode]:
        """批量创建节点
        
        Args:
            node_ids: 节点ID列表
            **kwargs: 额外的创建参数
        
        Returns:
            节点实例字典
        """
        instances = {}
        for node_id in node_ids:
            try:
                instances[node_id] = self.create(node_id, **kwargs)
            except Exception as e:
                logger.error(f"Failed to create node {node_id}: {e}")
        
        return instances
    
    # ========================================================================
    # 动态加载
    # ========================================================================
    
    def _load_node_class(self, config: NodeConfig) -> Optional[Type[BaseNode]]:
        """动态加载节点类
        
        Args:
            config: 节点配置
        
        Returns:
            节点类，如果加载失败返回 None
        """
        if not config.module_path or not config.class_name:
            logger.warning(
                f"Cannot load node class: missing module_path or class_name",
                node_id=config.node_id
            )
            return None
        
        try:
            logger.info(
                f"Loading node class dynamically",
                module=config.module_path,
                class_name=config.class_name
            )
            
            # 导入模块
            module = importlib.import_module(config.module_path)
            
            # 获取类
            node_class = getattr(module, config.class_name)
            
            # 验证是 BaseNode 的子类
            # 注意：由于导入路径可能不一致，使用名称检查而不是 issubclass
            base_names = [base.__name__ for base in node_class.__mro__]
            if 'BaseNode' not in base_names:
                logger.error(
                    f"Class is not a subclass of BaseNode: {config.class_name}, MRO: {base_names}"
                )
                return None
            
            logger.debug(f"BaseNode found in MRO: {config.class_name}")
            
            # 注册到注册表
            self.registry.register_class(config.node_id, node_class)
            
            return node_class
            
        except Exception as e:
            logger.error(
                f"Failed to load node class: {config.class_name}",
                error=str(e),
                exc_info=True
            )
            return None
    
    def _load_middlewares(self, middleware_names: list[str]) -> list:
        """加载中间件列表
        
        Args:
            middleware_names: 中间件名称列表
        
        Returns:
            中间件实例列表
        """
        middlewares = []
        
        for name in middleware_names:
            middleware = self._middleware_pool.get(name)
            
            if middleware is None:
                logger.warning(f"Middleware not found: {name}")
                continue
            
            middlewares.append(middleware)
        
        return middlewares
    
    # ========================================================================
    # 中间件管理
    # ========================================================================
    
    def register_middleware(self, name: str, middleware: Any):
        """注册中间件
        
        Args:
            name: 中间件名称
            middleware: 中间件实例或类
        """
        self._middleware_pool[name] = middleware
        logger.info(f"Middleware registered: {name}")
    
    def get_middleware(self, name: str) -> Optional[Any]:
        """获取中间件
        
        Args:
            name: 中间件名称
        
        Returns:
            中间件实例，如果不存在返回 None
        """
        return self._middleware_pool.get(name)
    
    # ========================================================================
    # 实例管理
    # ========================================================================
    
    def clear_cache(self, node_id: Optional[str] = None):
        """清除缓存
        
        Args:
            node_id: 节点ID，如果为 None 则清除所有缓存
        """
        if node_id:
            self.registry.clear_instance(node_id)
        else:
            self.registry.clear_all_instances()
    
    def destroy(self, node_id: str):
        """销毁节点实例
        
        Args:
            node_id: 节点ID
        """
        instance = self.registry.get_cached_instance(node_id)
        
        if instance:
            # 可以在这里添加清理逻辑
            # 例如：关闭连接、释放资源等
            logger.info(f"Destroying node instance: {node_id}")
        
        self.registry.clear_instance(node_id)
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def validate_config(self, config: NodeConfig) -> tuple[bool, Optional[str]]:
        """验证节点配置
        
        Args:
            config: 节点配置
        
        Returns:
            (是否有效, 错误信息)
        """
        # 检查节点类是否存在
        node_class = self.registry.get_node_class(config.node_id)
        
        if node_class is None:
            # 检查是否可以动态加载
            if not config.module_path or not config.class_name:
                return False, "Node class not registered and cannot be loaded"
        
        # 检查中间件
        for middleware_name in config.middlewares:
            if middleware_name not in self._middleware_pool:
                logger.warning(f"Middleware not found: {middleware_name}")
        
        return True, None
    
    def __repr__(self) -> str:
        return (
            f"<NodeFactory(enable_cache={self.enable_cache}, "
            f"middlewares={len(self._middleware_pool)})>"
        )


# ============================================================================
# 全局实例
# ============================================================================

# 提供全局访问点
node_factory = NodeFactory()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "NodeFactory",
    "node_factory",
]

