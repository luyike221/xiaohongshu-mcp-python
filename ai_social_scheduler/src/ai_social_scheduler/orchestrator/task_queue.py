"""任务队列 - 管理任务的入队和出队

重构核心：支持优先级的任务队列
"""

import asyncio
from collections import deque
from typing import Optional

from ..core.task import Priority, Task
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 任务队列
# ============================================================================

class TaskQueue:
    """任务队列 - 支持优先级的任务队列
    
    核心职责：
    1. 任务入队/出队
    2. 优先级管理
    3. 队列统计
    
    设计理念：
    - 简单高效：使用 deque 实现
    - 优先级：支持不同优先级队列
    - 线程安全：使用 asyncio.Lock
    """
    
    def __init__(self, max_size: int = 0):
        """初始化任务队列
        
        Args:
            max_size: 最大队列大小（0 表示无限制）
        """
        self.max_size = max_size
        self._lock = asyncio.Lock()
        
        # 按优先级分组的队列
        self._queues = {
            Priority.CRITICAL: deque(),
            Priority.HIGH: deque(),
            Priority.NORMAL: deque(),
            Priority.LOW: deque(),
        }
        
        logger.info(f"TaskQueue initialized, max_size={max_size}")
    
    async def enqueue(self, task: Task) -> bool:
        """入队
        
        Args:
            task: 任务对象
        
        Returns:
            是否成功入队
        """
        async with self._lock:
            # 检查队列大小
            if self.max_size > 0 and self.size() >= self.max_size:
                logger.warning(
                    "Queue full, cannot enqueue",
                    task_id=task.task_id,
                    queue_size=self.size()
                )
                return False
            
            # 入队
            queue = self._queues.get(task.priority, self._queues[Priority.NORMAL])
            queue.append(task)
            
            logger.debug(
                "Task enqueued",
                task_id=task.task_id,
                priority=task.priority.value,
                queue_size=len(queue)
            )
            
            return True
    
    async def dequeue(self) -> Optional[Task]:
        """出队（按优先级）
        
        Returns:
            任务对象，如果队列为空则返回 None
        """
        async with self._lock:
            # 按优先级顺序出队
            for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                queue = self._queues[priority]
                if queue:
                    task = queue.popleft()
                    logger.debug(
                        "Task dequeued",
                        task_id=task.task_id,
                        priority=priority.value
                    )
                    return task
            
            return None
    
    async def peek(self) -> Optional[Task]:
        """查看队首任务（不出队）"""
        async with self._lock:
            for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
                queue = self._queues[priority]
                if queue:
                    return queue[0]
            return None
    
    def size(self) -> int:
        """获取队列总大小"""
        return sum(len(q) for q in self._queues.values())
    
    def is_empty(self) -> bool:
        """队列是否为空"""
        return self.size() == 0
    
    def is_full(self) -> bool:
        """队列是否已满"""
        return self.max_size > 0 and self.size() >= self.max_size
    
    async def clear(self):
        """清空队列"""
        async with self._lock:
            for queue in self._queues.values():
                queue.clear()
            logger.info("Queue cleared")
    
    def stats(self) -> dict:
        """获取队列统计信息"""
        return {
            "total": self.size(),
            "by_priority": {
                priority.value: len(queue)
                for priority, queue in self._queues.items()
            },
            "max_size": self.max_size,
            "is_full": self.is_full(),
        }
    
    def __repr__(self) -> str:
        return f"<TaskQueue(size={self.size()}, max_size={self.max_size})>"


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "TaskQueue",
]

