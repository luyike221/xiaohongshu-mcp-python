"""配置加载器 - 从 YAML 加载配置并转换为 Python 对象

重构核心：统一的配置管理
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml

from ..core.node import (
    Capability,
    CapabilityType,
    ExecutorConfig,
    HealthCheckConfig,
    NodeConfig,
    NodeStatus,
    NodeType,
    ResourceLimit,
)
from ..core.route import (
    MatchMode,
    RouteConfig,
    RouteRule,
    RouteStrategy,
    RouteTrigger,
    TriggerType,
)

# 延迟导入避免循环依赖
def _get_logger():
    from ..tools.logging import get_logger
    return get_logger(__name__)


# ============================================================================
# 配置加载器
# ============================================================================

class ConfigLoader:
    """配置加载器 - 加载 YAML 配置并转换为 Pydantic 模型
    
    核心职责：
    1. 加载 YAML 文件
    2. 验证配置格式
    3. 转换为 Pydantic 模型
    4. 错误处理
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置加载器
        
        Args:
            config_dir: 配置文件目录（默认为项目根目录下的 config/）
        """
        if config_dir is None:
            # 默认配置目录：ai_social_scheduler/config/
            current_file = Path(__file__).resolve()
            # 从 src/ai_social_scheduler/config/loader.py 到 ai_social_scheduler/config/
            # 路径: src/ai_social_scheduler/config/loader.py
            # 向上4级: src/ai_social_scheduler/config -> src/ai_social_scheduler -> src -> 项目根目录
            project_root = current_file.parent.parent.parent.parent
            config_dir = project_root / "config"
            
            # 如果不存在，尝试相对路径
            if not config_dir.exists():
                # 尝试从当前工作目录查找
                import os
                cwd = Path(os.getcwd())
                alt_config = cwd / "config"
                if alt_config.exists():
                    config_dir = alt_config
        
        self.config_dir = Path(config_dir)
        
        _get_logger().info(f"ConfigLoader initialized, config_dir={self.config_dir}")
    
    # ========================================================================
    # YAML 加载
    # ========================================================================
    
    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """加载 YAML 文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            YAML 内容字典
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
            
            _get_logger().info(f"YAML loaded: {file_path}")
            return content or {}
            
        except FileNotFoundError:
            _get_logger().error(f"Config file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            _get_logger().error(f"Invalid YAML format: {file_path}, error: {e}")
            raise
        except Exception as e:
            _get_logger().error(f"Failed to load YAML: {file_path}, error: {e}")
            raise
    
    # ========================================================================
    # 路由配置加载
    # ========================================================================
    
    def load_routes(self, file_name: str = "routes.yaml") -> list[RouteConfig]:
        """加载路由配置
        
        Args:
            file_name: 文件名
        
        Returns:
            路由配置列表
        """
        file_path = self.config_dir / file_name
        
        _get_logger().info(f"Loading routes from: {file_path}")
        
        data = self._load_yaml(file_path)
        routes_data = data.get("routes", [])
        
        routes = []
        for route_data in routes_data:
            try:
                route = self._parse_route_config(route_data)
                routes.append(route)
            except Exception as e:
                _get_logger().error(
                    f"Failed to parse route: {route_data.get('route_id', 'unknown')}, "
                    f"error: {e}"
                )
                # 继续处理其他路由
        
        _get_logger().info(f"Loaded {len(routes)} routes")
        return routes
    
    def _parse_route_config(self, data: dict) -> RouteConfig:
        """解析路由配置"""
        # 解析触发器
        triggers = []
        for trigger_data in data.get("triggers", []):
            triggers.append(self._parse_trigger(trigger_data))
        
        # 解析规则
        rules = []
        for rule_data in data.get("rules", []):
            rules.append(self._parse_rule(rule_data))
        
        # 解析策略
        strategy_str = data.get("strategy", "single")
        strategy = RouteStrategy(strategy_str)
        
        return RouteConfig(
            route_id=data["route_id"],
            name=data["name"],
            description=data.get("description", ""),
            triggers=triggers,
            rules=rules,
            strategy=strategy,
            target_nodes=data.get("target_nodes", []),
            fallback=data.get("fallback"),
            enabled=data.get("enabled", True),
            timeout=data.get("timeout", 300),
            metadata=data.get("metadata", {}),
        )
    
    def _parse_trigger(self, data: dict) -> RouteTrigger:
        """解析触发器"""
        trigger_type = TriggerType(data["type"])
        match_mode_str = data.get("match_mode", "any")
        match_mode = MatchMode(match_mode_str)
        
        return RouteTrigger(
            type=trigger_type,
            patterns=data.get("patterns", []),
            keywords=data.get("keywords", []),
            function_name=data.get("function_name"),
            weight=data.get("weight", 1.0),
            enabled=data.get("enabled", True),
            case_sensitive=data.get("case_sensitive", False),
            match_mode=match_mode,
        )
    
    def _parse_rule(self, data: dict) -> RouteRule:
        """解析规则"""
        return RouteRule(
            rule_id=data["rule_id"],
            name=data.get("name", ""),
            condition=data["condition"],
            target=data["target"],
            priority=data.get("priority", 50),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )
    
    # ========================================================================
    # 节点配置加载
    # ========================================================================
    
    def load_nodes(self, file_name: str = "nodes.yaml") -> list[NodeConfig]:
        """加载节点配置
        
        Args:
            file_name: 文件名
        
        Returns:
            节点配置列表
        """
        file_path = self.config_dir / file_name
        
        _get_logger().info(f"Loading nodes from: {file_path}")
        
        data = self._load_yaml(file_path)
        nodes_data = data.get("nodes", [])
        
        nodes = []
        for node_data in nodes_data:
            try:
                node = self._parse_node_config(node_data)
                nodes.append(node)
            except Exception as e:
                _get_logger().error(
                    f"Failed to parse node: {node_data.get('node_id', 'unknown')}, "
                    f"error: {e}"
                )
                # 继续处理其他节点
        
        _get_logger().info(f"Loaded {len(nodes)} nodes")
        return nodes
    
    def _parse_node_config(self, data: dict) -> NodeConfig:
        """解析节点配置"""
        # 解析节点类型
        node_type = NodeType(data["node_type"])
        
        # 解析能力
        capabilities = []
        for cap_data in data.get("capabilities", []):
            capabilities.append(self._parse_capability(cap_data))
        
        # 解析执行器配置
        executor_data = data.get("executor", {})
        executor = ExecutorConfig(**executor_data)
        
        # 解析资源限制
        resources_data = data.get("resources", {})
        resources = ResourceLimit(**resources_data)
        
        # 解析健康检查
        health_data = data.get("health_check", {})
        health_check = HealthCheckConfig(**health_data)
        
        # 解析状态
        status_str = data.get("status", "active")
        status = NodeStatus(status_str)
        
        return NodeConfig(
            node_id=data["node_id"],
            name=data["name"],
            description=data.get("description", ""),
            node_type=node_type,
            class_name=data["class_name"],
            module_path=data.get("module_path"),
            capabilities=capabilities,
            executor=executor,
            middlewares=data.get("middlewares", []),
            resources=resources,
            health_check=health_check,
            status=status,
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )
    
    def _parse_capability(self, data: dict) -> Capability:
        """解析能力"""
        cap_type = CapabilityType(data["type"])
        
        return Capability(
            type=cap_type,
            name=data["name"],
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            required=data.get("required", False),
        )
    
    # ========================================================================
    # 批量加载
    # ========================================================================
    
    def load_all(
        self,
        routes_file: str = "routes.yaml",
        nodes_file: str = "nodes.yaml"
    ) -> tuple[list[RouteConfig], list[NodeConfig]]:
        """加载所有配置
        
        Args:
            routes_file: 路由配置文件名
            nodes_file: 节点配置文件名
        
        Returns:
            (路由配置列表, 节点配置列表)
        """
        routes = self.load_routes(routes_file)
        nodes = self.load_nodes(nodes_file)
        
        return routes, nodes


# ============================================================================
# 便捷函数
# ============================================================================

_default_loader: Optional[ConfigLoader] = None


def get_default_loader() -> ConfigLoader:
    """获取默认配置加载器（单例）"""
    global _default_loader
    if _default_loader is None:
        _default_loader = ConfigLoader()
    return _default_loader


def load_config(
    config_dir: Optional[str] = None,
    routes_file: str = "routes.yaml",
    nodes_file: str = "nodes.yaml"
) -> tuple[list[RouteConfig], list[NodeConfig]]:
    """加载配置的便捷函数
    
    Args:
        config_dir: 配置目录（None 使用默认）
        routes_file: 路由配置文件名
        nodes_file: 节点配置文件名
    
    Returns:
        (路由配置列表, 节点配置列表)
    """
    if config_dir:
        loader = ConfigLoader(config_dir)
    else:
        loader = get_default_loader()
    
    return loader.load_all(routes_file, nodes_file)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "ConfigLoader",
    "load_config",
]

