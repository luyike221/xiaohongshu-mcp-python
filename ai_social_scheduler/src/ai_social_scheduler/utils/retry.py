"""重试逻辑"""

from functools import wraps
from typing import Callable, TypeVar, Any
import asyncio

from tenacity import retry, stop_after_attempt, wait_exponential

T = TypeVar("T")


def retry_async(
    max_attempts: int = 3,
    wait_multiplier: float = 1.0,
    wait_max: float = 10.0,
):
    """异步重试装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=wait_multiplier, max=wait_max),
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def retry_sync(
    max_attempts: int = 3,
    wait_multiplier: float = 1.0,
    wait_max: float = 10.0,
):
    """同步重试装饰器"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=wait_multiplier, max=wait_max),
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator

