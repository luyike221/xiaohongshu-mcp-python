"""中间件链 - 组织和执行多个中间件

重构核心：实现洋葱模型的中间件链
"""

from typing import Any, Awaitable, Callable

from ..core.task import Task
from ..tools.logging import get_logger
from .base import BaseMiddleware

logger = get_logger(__name__)


# ============================================================================
# 中间件链
# ============================================================================

class MiddlewareChain:
    """中间件链 - 组织和执行多个中间件
    
    核心职责：
    1. 管理中间件列表
    2. 按顺序执行中间件
    3. 实现洋葱模型
    
    设计理念：
    - 洋葱模型：每个中间件包裹下一个中间件
    - 可组合：支持动态添加/删除中间件
    - 透明：对核心逻辑透明
    
    执行顺序：
    ```
    请求 → M1.before → M2.before → 核心逻辑 → M2.after → M1.after → 响应
    ```
    """
    
    def __init__(self, middlewares: list[BaseMiddleware] = None):
        """初始化中间件链
        
        Args:
            middlewares: 中间件列表
        """
        self.middlewares = middlewares or []
        logger.info(f"MiddlewareChain initialized with {len(self.middlewares)} middlewares")
    
    def add(self, middleware: BaseMiddleware):
        """添加中间件
        
        Args:
            middleware: 中间件实例
        """
        self.middlewares.append(middleware)
        logger.debug(f"Middleware added: {middleware.name}")
    
    def remove(self, middleware_name: str) -> bool:
        """移除中间件
        
        Args:
            middleware_name: 中间件名称
        
        Returns:
            是否成功移除
        """
        for i, m in enumerate(self.middlewares):
            if m.name == middleware_name:
                self.middlewares.pop(i)
                logger.debug(f"Middleware removed: {middleware_name}")
                return True
        return False
    
    async def execute(
        self,
        task: Task,
        state: dict[str, Any],
        core_handler: Callable[[Task, dict[str, Any]], Awaitable[dict[str, Any]]]
    ) -> dict[str, Any]:
        """执行中间件链
        
        Args:
            task: 任务对象
            state: 图状态
            core_handler: 核心处理器（最内层的逻辑）
        
        Returns:
            处理结果
        """
        if not self.middlewares:
            # 没有中间件，直接执行核心逻辑
            return await core_handler(task, state)
        
        # 构建中间件链（从后往前包裹）
        handler = core_handler
        
        for middleware in reversed(self.middlewares):
            # 闭包捕获当前的 handler 和 middleware
            handler = self._wrap_middleware(middleware, handler)
        
        # 执行链条
        return await handler(task, state)
    
    def _wrap_middleware(
        self,
        middleware: BaseMiddleware,
        next_handler: Callable[[Task, dict[str, Any]], Awaitable[dict[str, Any]]]
    ) -> Callable[[Task, dict[str, Any]], Awaitable[dict[str, Any]]]:
        """包裹中间件
        
        Args:
            middleware: 中间件实例
            next_handler: 下一个处理器
        
        Returns:
            包裹后的处理器
        """
        async def wrapped_handler(task: Task, state: dict[str, Any]) -> dict[str, Any]:
            return await middleware(task, state, next_handler)
        
        return wrapped_handler
    
    def clear(self):
        """清空中间件"""
        self.middlewares.clear()
        logger.debug("Middleware chain cleared")
    
    def __len__(self) -> int:
        return len(self.middlewares)
    
    def __repr__(self) -> str:
        names = [m.name for m in self.middlewares]
        return f"<MiddlewareChain({len(self.middlewares)}): {' → '.join(names)}>"


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "MiddlewareChain",
]

