"""状态管理器 - 管理会话状态和任务上下文

重构核心：统一的状态管理
"""

from typing import Any, Optional

from langgraph.checkpoint.memory import MemorySaver

from ..core.task import Task
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 状态管理器
# ============================================================================

class StateManager:
    """状态管理器 - 管理会话状态和任务上下文
    
    核心职责：
    1. 会话状态持久化
    2. 任务上下文管理
    3. 状态查询和更新
    
    设计理念：
    - 分层：会话状态、任务状态分离
    - 持久化：支持多种存储后端
    - 缓存：提高访问性能
    """
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None):
        """初始化状态管理器
        
        Args:
            checkpointer: 检查点存储器
        """
        self.checkpointer = checkpointer or MemorySaver()
        self._task_store: dict[str, Task] = {}
        self._session_store: dict[str, dict] = {}
        
        logger.info("StateManager initialized")
    
    # ========================================================================
    # 任务状态管理
    # ========================================================================
    
    async def save_task(self, task: Task):
        """保存任务状态"""
        self._task_store[task.task_id] = task
        logger.debug(f"Task saved: {task.task_id}")
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        return self._task_store.get(task_id)
    
    async def update_task(self, task: Task):
        """更新任务状态"""
        self._task_store[task.task_id] = task
        logger.debug(f"Task updated: {task.task_id}")
    
    async def delete_task(self, task_id: str):
        """删除任务"""
        if task_id in self._task_store:
            del self._task_store[task_id]
            logger.debug(f"Task deleted: {task_id}")
    
    # ========================================================================
    # 会话状态管理
    # ========================================================================
    
    async def save_session(self, session_id: str, state: dict[str, Any]):
        """保存会话状态"""
        self._session_store[session_id] = state
        logger.debug(f"Session saved: {session_id}")
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话状态"""
        return self._session_store.get(session_id)
    
    async def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self._session_store:
            del self._session_store[session_id]
            logger.debug(f"Session cleared: {session_id}")
    
    # ========================================================================
    # 统计信息
    # ========================================================================
    
    def stats(self) -> dict:
        """获取统计信息"""
        return {
            "tasks_count": len(self._task_store),
            "sessions_count": len(self._session_store),
        }


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "StateManager",
]

