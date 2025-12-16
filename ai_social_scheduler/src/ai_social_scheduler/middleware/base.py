"""中间件基类

重构核心：定义中间件的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional

from ..core.task import Task
from ..tools.logging import get_logger


# ============================================================================
# 中间件基类
# ============================================================================

class BaseMiddleware(ABC):
    """中间件基类
    
    核心职责：
    1. 定义中间件接口
    2. 实现洋葱模型执行
    3. 支持异步处理
    
    设计理念：
    - 洋葱模型：请求 → 中间件1 → 中间件2 → 核心逻辑 → 中间件2 → 中间件1 → 响应
    - 职责单一：每个中间件只关注一个横切关注点
    - 可组合：多个中间件可以组合成链
    
    执行流程：
    1. before_execute (前置处理)
    2. next() (调用下一个中间件或核心逻辑)
    3. after_execute (后置处理)
    4. on_error (错误处理)
    """
    
    def __init__(self, name: Optional[str] = None):
        """初始化中间件
        
        Args:
            name: 中间件名称
        """
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"middleware.{self.name}")
    
    async def __call__(
        self,
        task: Task,
        state: dict[str, Any],
        next_handler: Callable[[Task, dict[str, Any]], Awaitable[dict[str, Any]]]
    ) -> dict[str, Any]:
        """中间件调用入口
        
        Args:
            task: 任务对象
            state: 图状态
            next_handler: 下一个处理器（中间件或核心逻辑）
        
        Returns:
            处理结果
        """
        try:
            # 前置处理
            await self.before_execute(task, state)
            
            # 调用下一个处理器
            result = await next_handler(task, state)
            
            # 后置处理
            result = await self.after_execute(task, state, result)
            
            return result
            
        except Exception as e:
            # 错误处理
            return await self.on_error(task, state, e, next_handler)
    
    @abstractmethod
    async def before_execute(self, task: Task, state: dict[str, Any]):
        """前置处理（子类实现）
        
        在核心逻辑执行前调用
        """
        pass
    
    @abstractmethod
    async def after_execute(
        self,
        task: Task,
        state: dict[str, Any],
        result: dict[str, Any]
    ) -> dict[str, Any]:
        """后置处理（子类实现）
        
        在核心逻辑执行后调用
        
        Returns:
            处理后的结果
        """
        pass
    
    async def on_error(
        self,
        task: Task,
        state: dict[str, Any],
        error: Exception,
        next_handler: Callable
    ) -> dict[str, Any]:
        """错误处理（子类可重写）
        
        默认实现：直接抛出异常
        """
        raise error
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "BaseMiddleware",
]

