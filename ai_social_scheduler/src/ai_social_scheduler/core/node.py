"""节点配置模型 - 声明式节点定义

重构核心：节点可通过配置动态注册和发现
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class NodeType(str, Enum):
    """节点类型"""
    AGENT = "agent"              # Agent 节点
    TOOL = "tool"                # 工具节点
    SUBGRAPH = "subgraph"        # 子图节点
    FUNCTION = "function"        # 函数节点
    ROUTER = "router"            # 路由节点


class CapabilityType(str, Enum):
    """能力类型"""
    CONTENT_GENERATION = "content_generation"
    CONTENT_ANALYSIS = "content_analysis"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    PUBLISHING = "publishing"
    DATA_PROCESSING = "data_processing"
    QUERY = "query"
    CUSTOM = "custom"


class NodeStatus(str, Enum):
    """节点状态"""
    ACTIVE = "active"            # 活跃
    INACTIVE = "inactive"        # 不活跃
    DISABLED = "disabled"        # 已禁用
    ERROR = "error"              # 错误


# ============================================================================
# 能力描述
# ============================================================================

class Capability(BaseModel):
    """节点能力描述
    
    描述节点可以做什么
    """
    
    type: CapabilityType = Field(
        description="能力类型"
    )
    
    name: str = Field(
        description="能力名称"
    )
    
    description: str = Field(
        default="",
        description="能力描述"
    )
    
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="能力参数schema"
    )
    
    required: bool = Field(
        default=False,
        description="是否为必需能力"
    )


# ============================================================================
# 执行配置
# ============================================================================

class ExecutorConfig(BaseModel):
    """执行器配置
    
    控制节点的执行行为
    """
    
    max_concurrency: int = Field(
        default=1,
        ge=1,
        description="最大并发数"
    )
    
    timeout: int = Field(
        default=300,
        ge=1,
        description="超时时间（秒）"
    )
    
    retry_limit: int = Field(
        default=3,
        ge=0,
        description="最大重试次数"
    )
    
    retry_delay: int = Field(
        default=1,
        ge=0,
        description="重试延迟（秒）"
    )
    
    retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        description="重试退避系数"
    )
    
    enable_circuit_breaker: bool = Field(
        default=False,
        description="是否启用熔断器"
    )
    
    circuit_breaker_threshold: int = Field(
        default=5,
        ge=1,
        description="熔断器阈值（连续失败次数）"
    )


# ============================================================================
# 资源限制
# ============================================================================

class ResourceLimit(BaseModel):
    """资源限制配置"""
    
    memory_limit: Optional[str] = Field(
        default=None,
        description="内存限制（如：1GB, 512MB）"
    )
    
    cpu_limit: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="CPU 限制（核数）"
    )
    
    gpu_required: bool = Field(
        default=False,
        description="是否需要 GPU"
    )
    
    gpu_memory: Optional[str] = Field(
        default=None,
        description="GPU 内存要求"
    )


# ============================================================================
# 健康检查配置
# ============================================================================

class HealthCheckConfig(BaseModel):
    """健康检查配置"""
    
    enabled: bool = Field(
        default=True,
        description="是否启用健康检查"
    )
    
    interval: int = Field(
        default=60,
        ge=1,
        description="检查间隔（秒）"
    )
    
    timeout: int = Field(
        default=10,
        ge=1,
        description="检查超时（秒）"
    )
    
    failure_threshold: int = Field(
        default=3,
        ge=1,
        description="失败阈值（连续失败多少次标记为不健康）"
    )
    
    success_threshold: int = Field(
        default=1,
        ge=1,
        description="成功阈值（连续成功多少次标记为健康）"
    )
    
    endpoint: Optional[str] = Field(
        default=None,
        description="健康检查端点"
    )


# ============================================================================
# 节点配置
# ============================================================================

class NodeConfig(BaseModel):
    """节点配置 - 声明式节点定义
    
    核心设计理念：
    1. 声明式配置：通过配置定义节点
    2. 插件化：节点可动态加载
    3. 可观测：支持健康检查和监控
    4. 可控制：资源限制和执行控制
    """
    
    # ========================================================================
    # 基础信息
    # ========================================================================
    
    node_id: str = Field(
        description="节点唯一标识"
    )
    
    name: str = Field(
        description="节点名称"
    )
    
    description: str = Field(
        default="",
        description="节点描述"
    )
    
    node_type: NodeType = Field(
        description="节点类型"
    )
    
    # ========================================================================
    # 实现信息
    # ========================================================================
    
    class_name: str = Field(
        description="实现类名"
    )
    
    module_path: Optional[str] = Field(
        default=None,
        description="模块路径"
    )
    
    # ========================================================================
    # 能力描述
    # ========================================================================
    
    capabilities: list[Capability] = Field(
        default_factory=list,
        description="节点能力列表"
    )
    
    # ========================================================================
    # 执行配置
    # ========================================================================
    
    executor: ExecutorConfig = Field(
        default_factory=ExecutorConfig,
        description="执行器配置"
    )
    
    # ========================================================================
    # 中间件
    # ========================================================================
    
    middlewares: list[str] = Field(
        default_factory=list,
        description="中间件列表（按顺序执行）"
    )
    
    # ========================================================================
    # 资源配置
    # ========================================================================
    
    resources: ResourceLimit = Field(
        default_factory=ResourceLimit,
        description="资源限制"
    )
    
    # ========================================================================
    # 健康检查
    # ========================================================================
    
    health_check: HealthCheckConfig = Field(
        default_factory=HealthCheckConfig,
        description="健康检查配置"
    )
    
    # ========================================================================
    # 状态管理
    # ========================================================================
    
    status: NodeStatus = Field(
        default=NodeStatus.ACTIVE,
        description="节点状态"
    )
    
    # ========================================================================
    # 配置参数
    # ========================================================================
    
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="节点特定配置参数"
    )
    
    # ========================================================================
    # 元数据
    # ========================================================================
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="节点元数据"
    )
    
    tags: list[str] = Field(
        default_factory=list,
        description="标签（用于分类和过滤）"
    )
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def is_active(self) -> bool:
        """节点是否活跃"""
        return self.status == NodeStatus.ACTIVE
    
    def has_capability(self, capability_type: CapabilityType) -> bool:
        """是否具有指定能力"""
        return any(cap.type == capability_type for cap in self.capabilities)
    
    def get_capability(self, capability_type: CapabilityType) -> Optional[Capability]:
        """获取指定能力"""
        for cap in self.capabilities:
            if cap.type == capability_type:
                return cap
        return None


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 枚举
    "NodeType",
    "CapabilityType",
    "NodeStatus",
    # 模型
    "Capability",
    "ExecutorConfig",
    "ResourceLimit",
    "HealthCheckConfig",
    "NodeConfig",
]

