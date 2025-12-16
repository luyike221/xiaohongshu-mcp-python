"""路由配置模型 - 声明式路由定义

重构核心：通过配置定义路由规则，而不是硬编码
"""

from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class TriggerType(str, Enum):
    """触发器类型"""
    INTENT = "intent"            # 意图匹配（LLM）
    KEYWORD = "keyword"          # 关键词匹配
    REGEX = "regex"              # 正则表达式
    FUNCTION = "function"        # 自定义函数
    ALWAYS = "always"            # 总是触发


class RouteStrategy(str, Enum):
    """路由策略"""
    SINGLE = "single"            # 单个节点
    PARALLEL = "parallel"        # 并行执行多个节点
    CASCADE = "cascade"          # 级联执行（顺序）
    CONDITIONAL = "conditional"  # 条件路由
    HYBRID = "hybrid"            # 混合策略（规则+LLM）


class MatchMode(str, Enum):
    """匹配模式"""
    ANY = "any"                  # 匹配任意一个
    ALL = "all"                  # 匹配所有
    FIRST = "first"              # 匹配第一个


# ============================================================================
# 触发器配置
# ============================================================================

class RouteTrigger(BaseModel):
    """路由触发器配置
    
    定义何时触发此路由
    """
    
    type: TriggerType = Field(
        description="触发器类型"
    )
    
    # 关键词/正则/意图模式
    patterns: list[str] = Field(
        default_factory=list,
        description="匹配模式列表"
    )
    
    keywords: list[str] = Field(
        default_factory=list,
        description="关键词列表"
    )
    
    # 自定义函数名（用于 FUNCTION 类型）
    function_name: Optional[str] = Field(
        default=None,
        description="自定义函数名称"
    )
    
    # 权重
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="触发器权重"
    )
    
    # 是否启用
    enabled: bool = Field(
        default=True,
        description="是否启用"
    )
    
    # 匹配选项
    case_sensitive: bool = Field(
        default=False,
        description="是否区分大小写"
    )
    
    match_mode: MatchMode = Field(
        default=MatchMode.ANY,
        description="匹配模式"
    )


# ============================================================================
# 路由规则
# ============================================================================

class RouteRule(BaseModel):
    """路由规则
    
    定义路由决策的具体规则
    """
    
    rule_id: str = Field(
        description="规则唯一标识"
    )
    
    name: str = Field(
        default="",
        description="规则名称"
    )
    
    # 条件表达式
    condition: str = Field(
        description="条件表达式（支持简单的逻辑表达式）"
    )
    
    # 目标
    target: str = Field(
        description="目标节点/路由"
    )
    
    # 优先级
    priority: int = Field(
        default=50,
        ge=0,
        le=100,
        description="规则优先级（0-100，越大越优先）"
    )
    
    # 是否启用
    enabled: bool = Field(
        default=True,
        description="是否启用"
    )
    
    # 元数据
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="规则元数据"
    )


# ============================================================================
# 路由配置
# ============================================================================

class RouteConfig(BaseModel):
    """路由配置 - 声明式路由定义
    
    核心设计理念：
    1. 声明式配置：通过配置定义路由
    2. 分层匹配：触发器 → 规则 → 目标
    3. 多策略支持：单节点、并行、级联等
    4. 可扩展：支持自定义触发器和规则
    """
    
    # ========================================================================
    # 基础信息
    # ========================================================================
    
    route_id: str = Field(
        description="路由唯一标识"
    )
    
    name: str = Field(
        description="路由名称"
    )
    
    description: str = Field(
        default="",
        description="路由描述"
    )
    
    # ========================================================================
    # 触发条件
    # ========================================================================
    
    triggers: list[RouteTrigger] = Field(
        default_factory=list,
        description="触发器列表"
    )
    
    # ========================================================================
    # 路由规则
    # ========================================================================
    
    rules: list[RouteRule] = Field(
        default_factory=list,
        description="路由规则列表（按优先级排序）"
    )
    
    # ========================================================================
    # 路由策略
    # ========================================================================
    
    strategy: RouteStrategy = Field(
        default=RouteStrategy.SINGLE,
        description="路由策略"
    )
    
    # ========================================================================
    # 目标节点
    # ========================================================================
    
    target_nodes: list[str] = Field(
        default_factory=list,
        description="目标节点列表"
    )
    
    # ========================================================================
    # 回退策略
    # ========================================================================
    
    fallback: Optional[str] = Field(
        default=None,
        description="回退节点（匹配失败时）"
    )
    
    # ========================================================================
    # 配置选项
    # ========================================================================
    
    enabled: bool = Field(
        default=True,
        description="是否启用此路由"
    )
    
    timeout: int = Field(
        default=300,
        ge=1,
        description="路由超时时间（秒）"
    )
    
    # ========================================================================
    # 元数据
    # ========================================================================
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="路由元数据"
    )
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def get_sorted_rules(self) -> list[RouteRule]:
        """获取按优先级排序的规则"""
        return sorted(
            [r for r in self.rules if r.enabled],
            key=lambda x: x.priority,
            reverse=True
        )
    
    def get_enabled_triggers(self) -> list[RouteTrigger]:
        """获取启用的触发器"""
        return [t for t in self.triggers if t.enabled]


# ============================================================================
# 路由决策结果
# ============================================================================

class RouteDecision(BaseModel):
    """路由决策结果
    
    Router 分析后的决策输出
    """
    
    # 决策信息
    route_id: Optional[str] = Field(
        default=None,
        description="匹配的路由 ID"
    )
    
    target_nodes: list[str] = Field(
        default_factory=list,
        description="目标节点列表"
    )
    
    strategy: RouteStrategy = Field(
        default=RouteStrategy.SINGLE,
        description="执行策略"
    )
    
    # 分析结果
    intent: str = Field(
        default="unknown",
        description="识别的意图"
    )
    
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="置信度"
    )
    
    reasoning: str = Field(
        default="",
        description="决策理由"
    )
    
    # 响应
    response: str = Field(
        default="",
        description="给用户的响应"
    )
    
    # 提取的参数
    extracted_params: dict[str, Any] = Field(
        default_factory=dict,
        description="从用户输入提取的参数"
    )
    
    # 匹配信息
    matched_triggers: list[str] = Field(
        default_factory=list,
        description="匹配的触发器列表"
    )
    
    matched_rules: list[str] = Field(
        default_factory=list,
        description="匹配的规则列表"
    )
    
    # 是否需要等待
    should_wait: bool = Field(
        default=False,
        description="是否需要等待用户输入"
    )
    
    # 元数据
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="决策元数据"
    )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 枚举
    "TriggerType",
    "RouteStrategy",
    "MatchMode",
    # 模型
    "RouteTrigger",
    "RouteRule",
    "RouteConfig",
    "RouteDecision",
]

