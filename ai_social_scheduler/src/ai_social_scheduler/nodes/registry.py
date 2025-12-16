"""节点注册表 - 节点的注册和发现

重构核心：集中管理所有可用节点，支持动态注册和查询
"""

from typing import Optional, Type

from ..core.node import CapabilityType, NodeConfig, NodeStatus
from ..tools.logging import get_logger
from .base import BaseNode

logger = get_logger(__name__)


# ============================================================================
# 节点注册表
# ============================================================================

class NodeRegistry:
    """节点注册表 - 管理所有可用节点
    
    核心职责：
    1. 注册节点类和配置
    2. 查询和发现节点
    3. 维护节点状态
    4. 支持能力查询
    
    设计理念：
    - 单例模式：全局唯一注册表
    - 装饰器注册：简化注册流程
    - 配置分离：类和配置分开管理
    - 动态发现：支持按能力查找节点
    """
    
    _instance: Optional["NodeRegistry"] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化注册表"""
        if self._initialized:
            return
        
        self._node_classes: dict[str, Type[BaseNode]] = {}
        self._node_configs: dict[str, NodeConfig] = {}
        self._node_instances: dict[str, BaseNode] = {}
        
        self._initialized = True
        
        logger.info("NodeRegistry initialized")
    
    # ========================================================================
    # 注册方法
    # ========================================================================
    
    def register_class(
        self,
        node_id: str,
        node_class: Type[BaseNode],
    ):
        """注册节点类
        
        Args:
            node_id: 节点ID
            node_class: 节点类
        """
        self._node_classes[node_id] = node_class
        logger.info(f"Node class registered: {node_id}")
    
    def register_config(self, config: NodeConfig):
        """注册节点配置
        
        Args:
            config: 节点配置
        """
        self._node_configs[config.node_id] = config
        logger.info(f"Node config registered: {config.node_id}")
    
    def register(
        self,
        node_id: str,
        node_class: Optional[Type[BaseNode]] = None,
        config: Optional[NodeConfig] = None,
    ):
        """注册节点（类和配置一起）
        
        Args:
            node_id: 节点ID
            node_class: 节点类
            config: 节点配置
        """
        if node_class:
            self.register_class(node_id, node_class)
        
        if config:
            self.register_config(config)
    
    @classmethod
    def register_node(cls, node_id: str):
        """装饰器：注册节点类
        
        Usage:
            @NodeRegistry.register_node("my_node")
            class MyNode(BaseNode):
                ...
        """
        def decorator(node_class: Type[BaseNode]):
            registry = cls()
            registry.register_class(node_id, node_class)
            return node_class
        return decorator
    
    # ========================================================================
    # 查询方法
    # ========================================================================
    
    def get_node_class(self, node_id: str) -> Optional[Type[BaseNode]]:
        """获取节点类"""
        return self._node_classes.get(node_id)
    
    def get_node_config(self, node_id: str) -> Optional[NodeConfig]:
        """获取节点配置"""
        return self._node_configs.get(node_id)
    
    def has_node(self, node_id: str) -> bool:
        """检查节点是否存在"""
        return node_id in self._node_classes or node_id in self._node_configs
    
    def list_nodes(self) -> list[str]:
        """列出所有节点ID"""
        # 合并类和配置的ID
        all_ids = set(self._node_classes.keys()) | set(self._node_configs.keys())
        return sorted(all_ids)
    
    def list_active_nodes(self) -> list[str]:
        """列出所有活跃节点"""
        active = []
        for node_id, config in self._node_configs.items():
            if config.status == NodeStatus.ACTIVE:
                active.append(node_id)
        return active
    
    def find_nodes_by_capability(
        self,
        capability: CapabilityType
    ) -> list[str]:
        """根据能力查找节点
        
        Args:
            capability: 能力类型
        
        Returns:
            节点ID列表
        """
        matching = []
        for node_id, config in self._node_configs.items():
            if config.has_capability(capability):
                matching.append(node_id)
        return matching
    
    def find_nodes_by_tag(self, tag: str) -> list[str]:
        """根据标签查找节点
        
        Args:
            tag: 标签
        
        Returns:
            节点ID列表
        """
        matching = []
        for node_id, config in self._node_configs.items():
            if tag in config.tags:
                matching.append(node_id)
        return matching
    
    # ========================================================================
    # 实例管理
    # ========================================================================
    
    def cache_instance(self, node_id: str, instance: BaseNode):
        """缓存节点实例
        
        Args:
            node_id: 节点ID
            instance: 节点实例
        """
        self._node_instances[node_id] = instance
        logger.debug(f"Node instance cached: {node_id}")
    
    def get_cached_instance(self, node_id: str) -> Optional[BaseNode]:
        """获取缓存的节点实例
        
        Args:
            node_id: 节点ID
        
        Returns:
            节点实例，如果不存在则返回 None
        """
        return self._node_instances.get(node_id)
    
    def clear_instance(self, node_id: str):
        """清除缓存的实例
        
        Args:
            node_id: 节点ID
        """
        if node_id in self._node_instances:
            del self._node_instances[node_id]
            logger.debug(f"Node instance cleared: {node_id}")
    
    def clear_all_instances(self):
        """清除所有缓存的实例"""
        self._node_instances.clear()
        logger.info("All node instances cleared")
    
    # ========================================================================
    # 状态管理
    # ========================================================================
    
    def set_node_status(self, node_id: str, status: NodeStatus):
        """设置节点状态
        
        Args:
            node_id: 节点ID
            status: 节点状态
        """
        config = self.get_node_config(node_id)
        if config:
            config.status = status
            logger.info(f"Node status updated: {node_id} -> {status.value}")
    
    def disable_node(self, node_id: str):
        """禁用节点"""
        self.set_node_status(node_id, NodeStatus.DISABLED)
    
    def enable_node(self, node_id: str):
        """启用节点"""
        self.set_node_status(node_id, NodeStatus.ACTIVE)
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def get_node_info(self, node_id: str) -> dict:
        """获取节点信息
        
        Args:
            node_id: 节点ID
        
        Returns:
            节点信息字典
        """
        config = self.get_node_config(node_id)
        node_class = self.get_node_class(node_id)
        
        info = {
            "node_id": node_id,
            "has_class": node_class is not None,
            "has_config": config is not None,
            "is_active": False,
        }
        
        if config:
            info.update({
                "name": config.name,
                "type": config.node_type.value,
                "status": config.status.value,
                "is_active": config.is_active(),
                "capabilities": [c.type.value for c in config.capabilities],
                "tags": config.tags,
            })
        
        return info
    
    def clear(self):
        """清空注册表（主要用于测试）"""
        self._node_classes.clear()
        self._node_configs.clear()
        self._node_instances.clear()
        logger.info("NodeRegistry cleared")
    
    def __repr__(self) -> str:
        return (
            f"<NodeRegistry(classes={len(self._node_classes)}, "
            f"configs={len(self._node_configs)}, "
            f"instances={len(self._node_instances)})>"
        )


# ============================================================================
# 全局实例
# ============================================================================

# 提供全局访问点
node_registry = NodeRegistry()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "NodeRegistry",
    "node_registry",
]

