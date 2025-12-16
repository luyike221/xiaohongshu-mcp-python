"""日志中间件 - 记录请求和响应

重构核心：统一的日志记录
"""

from typing import Any

from ..core.task import Task
from .base import BaseMiddleware


# ============================================================================
# 日志中间件
# ============================================================================

class LoggingMiddleware(BaseMiddleware):
    """日志中间件 - 记录任务执行过程
    
    记录内容：
    - 任务开始时间
    - 任务参数
    - 执行时长
    - 执行结果
    """
    
    def __init__(self, name: str = "logging", verbose: bool = False):
        """初始化日志中间件
        
        Args:
            name: 中间件名称
            verbose: 是否详细记录
        """
        super().__init__(name)
        self.verbose = verbose
    
    async def before_execute(self, task: Task, state: dict[str, Any]):
        """记录任务开始"""
        self.logger.info(
            "Task execution started",
            task_id=task.task_id,
            task_type=task.task_type.value,
            priority=task.priority.value,
            current_node=task.current_node
        )
        
        if self.verbose:
            self.logger.debug(
                "Task details",
                input_data=task.input_data,
                route_path=task.route_path
            )
    
    async def after_execute(
        self,
        task: Task,
        state: dict[str, Any],
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """记录任务完成"""
        duration = task.duration()
        
        self.logger.info(
            "Task execution completed",
            task_id=task.task_id,
            status=task.status.value,
            duration=f"{duration:.2f}s" if duration else "N/A"
        )
        
        if self.verbose and task.status.value == "completed":
            self.logger.debug(
                "Task result",
                output_data=task.output_data
            )
        
        return result
    
    async def on_error(
        self,
        task: Task,
        state: dict[str, Any],
        error: Exception,
        next_handler
    ) -> dict[str, Any]:
        """记录任务错误"""
        self.logger.error(
            "Task execution failed",
            task_id=task.task_id,
            error=str(error),
            exc_info=True
        )
        
        # 继续抛出异常
        raise error


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "LoggingMiddleware",
]

