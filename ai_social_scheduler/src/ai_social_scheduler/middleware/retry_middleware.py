"""重试中间件 - 自动重试失败的任务

重构核心：统一的重试机制
"""

import asyncio
from typing import Any, Callable

from ..core.task import Task, TaskStatus
from .base import BaseMiddleware


# ============================================================================
# 重试中间件
# ============================================================================

class RetryMiddleware(BaseMiddleware):
    """重试中间件 - 自动重试失败的任务
    
    功能：
    - 捕获异常并重试
    - 支持退避策略
    - 记录重试次数
    - 超过限制后失败
    """
    
    def __init__(
        self,
        name: str = "retry",
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
    ):
        """初始化重试中间件
        
        Args:
            name: 中间件名称
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            backoff_factor: 退避系数
            max_delay: 最大延迟（秒）
        """
        super().__init__(name)
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    async def before_execute(self, task: Task, state: dict[str, Any]):
        """前置处理：无需操作"""
        pass
    
    async def after_execute(
        self,
        task: Task,
        state: dict[str, Any],
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """后置处理：检查结果状态"""
        # 如果任务标记为失败但还能重试，可以在这里处理
        return result
    
    async def on_error(
        self,
        task: Task,
        state: dict[str, Any],
        error: Exception,
        next_handler: Callable
    ) -> dict[str, Any]:
        """错误处理：重试逻辑"""
        
        # 检查是否还能重试
        if not task.can_retry():
            self.logger.error(
                "Max retries exceeded",
                task_id=task.task_id,
                retry_count=task.retry_count,
                max_retries=task.max_retries
            )
            raise error
        
        # 增加重试次数
        task.increment_retry()
        
        # 计算延迟时间
        delay = min(
            self.initial_delay * (self.backoff_factor ** (task.retry_count - 1)),
            self.max_delay
        )
        
        self.logger.warning(
            "Retrying task after error",
            task_id=task.task_id,
            retry_count=task.retry_count,
            delay=f"{delay:.2f}s",
            error=str(error)
        )
        
        # 等待
        await asyncio.sleep(delay)
        
        # 重试
        try:
            # 重置任务状态
            task.status = TaskStatus.RUNNING
            
            # 再次执行
            result = await next_handler(task, state)
            
            self.logger.info(
                "Retry succeeded",
                task_id=task.task_id,
                retry_count=task.retry_count
            )
            
            return result
            
        except Exception as retry_error:
            # 重试仍然失败，继续递归处理
            return await self.on_error(task, state, retry_error, next_handler)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "RetryMiddleware",
]

