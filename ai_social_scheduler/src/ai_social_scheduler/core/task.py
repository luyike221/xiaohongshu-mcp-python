"""任务模型 - 统一的任务抽象

重构核心：将所有工作抽象为 Task，提供统一的调度接口
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class TaskType(str, Enum):
    """任务类型"""
    CONTENT_GENERATION = "content_generation"    # 内容生成
    CONTENT_ANALYSIS = "content_analysis"        # 内容分析
    PUBLISHING = "publishing"                     # 发布
    QUERY = "query"                              # 查询
    CUSTOM = "custom"                            # 自定义


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"              # 待调度
    QUEUED = "queued"                # 已入队
    ROUTING = "routing"              # 路由中
    SCHEDULED = "scheduled"          # 已调度
    RUNNING = "running"              # 执行中
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消
    TIMEOUT = "timeout"              # 超时


class Priority(str, Enum):
    """任务优先级"""
    CRITICAL = "critical"    # 紧急
    HIGH = "high"            # 高
    NORMAL = "normal"        # 普通
    LOW = "low"              # 低


# ============================================================================
# 任务模型
# ============================================================================

class Task(BaseModel):
    """任务模型 - 系统中所有工作的统一抽象
    
    核心设计理念：
    1. 统一抽象：所有 Agent 工作都是 Task
    2. 可调度：支持优先级、超时、重试
    3. 可追踪：完整的生命周期追踪
    4. 可扩展：支持自定义字段
    """
    
    # ========================================================================
    # 基础信息
    # ========================================================================
    
    task_id: str = Field(
        default_factory=lambda: uuid4().hex[:12],
        description="任务唯一标识"
    )
    
    task_type: TaskType = Field(
        description="任务类型"
    )
    
    name: str = Field(
        default="",
        description="任务名称"
    )
    
    description: str = Field(
        default="",
        description="任务描述"
    )
    
    # ========================================================================
    # 状态管理
    # ========================================================================
    
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="任务状态"
    )
    
    priority: Priority = Field(
        default=Priority.NORMAL,
        description="任务优先级"
    )
    
    # ========================================================================
    # 输入输出
    # ========================================================================
    
    input_data: dict[str, Any] = Field(
        default_factory=dict,
        description="任务输入数据"
    )
    
    output_data: dict[str, Any] = Field(
        default_factory=dict,
        description="任务输出数据"
    )
    
    # ========================================================================
    # 路由信息
    # ========================================================================
    
    route_path: list[str] = Field(
        default_factory=list,
        description="路由路径（经过的节点列表）"
    )
    
    current_node: Optional[str] = Field(
        default=None,
        description="当前执行节点"
    )
    
    target_nodes: list[str] = Field(
        default_factory=list,
        description="目标节点列表"
    )
    
    # ========================================================================
    # 调度信息
    # ========================================================================
    
    retry_count: int = Field(
        default=0,
        description="当前重试次数"
    )
    
    max_retries: int = Field(
        default=3,
        description="最大重试次数"
    )
    
    timeout: int = Field(
        default=300,
        description="超时时间（秒）"
    )
    
    scheduled_at: Optional[datetime] = Field(
        default=None,
        description="调度时间"
    )
    
    started_at: Optional[datetime] = Field(
        default=None,
        description="开始执行时间"
    )
    
    completed_at: Optional[datetime] = Field(
        default=None,
        description="完成时间"
    )
    
    # ========================================================================
    # 依赖关系
    # ========================================================================
    
    dependencies: list[str] = Field(
        default_factory=list,
        description="依赖的任务 ID 列表"
    )
    
    parent_task_id: Optional[str] = Field(
        default=None,
        description="父任务 ID"
    )
    
    child_task_ids: list[str] = Field(
        default_factory=list,
        description="子任务 ID 列表"
    )
    
    # ========================================================================
    # 错误处理
    # ========================================================================
    
    error: Optional[str] = Field(
        default=None,
        description="错误信息"
    )
    
    error_stack: Optional[str] = Field(
        default=None,
        description="错误堆栈"
    )
    
    # ========================================================================
    # 上下文信息
    # ========================================================================
    
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="任务上下文（用户ID、会话ID等）"
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="元数据（可扩展字段）"
    )
    
    # ========================================================================
    # 时间戳
    # ========================================================================
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    
    # ========================================================================
    # 状态转换方法
    # ========================================================================
    
    def transition_to(self, status: TaskStatus, **kwargs) -> "Task":
        """状态转换
        
        Args:
            status: 目标状态
            **kwargs: 额外更新的字段
        """
        self.status = status
        self.updated_at = datetime.now()
        
        # 根据状态设置时间戳
        if status == TaskStatus.SCHEDULED:
            self.scheduled_at = datetime.now()
        elif status == TaskStatus.RUNNING:
            self.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.completed_at = datetime.now()
        
        # 更新额外字段
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        return self
    
    def mark_running(self, node: str) -> "Task":
        """标记为运行中"""
        self.current_node = node
        self.route_path.append(node)
        return self.transition_to(TaskStatus.RUNNING)
    
    def mark_completed(self, output: dict[str, Any]) -> "Task":
        """标记为已完成"""
        self.output_data = output
        return self.transition_to(TaskStatus.COMPLETED)
    
    def mark_failed(self, error: str, error_stack: Optional[str] = None) -> "Task":
        """标记为失败"""
        self.error = error
        self.error_stack = error_stack
        return self.transition_to(TaskStatus.FAILED)
    
    def increment_retry(self) -> "Task":
        """增加重试次数"""
        self.retry_count += 1
        self.updated_at = datetime.now()
        return self
    
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries
    
    def is_terminal(self) -> bool:
        """是否是终止状态"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT
        ]
    
    def duration(self) -> Optional[float]:
        """计算执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    def __repr__(self) -> str:
        return (
            f"Task(id={self.task_id}, type={self.task_type.value}, "
            f"status={self.status.value}, priority={self.priority.value})"
        )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "Task",
    "TaskType",
    "TaskStatus",
    "Priority",
]

