"""重试装饰器工具"""

import asyncio
import functools
from typing import Callable, TypeVar, Any, Optional, Tuple
import httpx
from loguru import logger

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[Tuple[type, ...]] = None,
):
    """
    异步函数重试装饰器，支持指数退避
    
    Args:
        max_retries: 最大重试次数（不包括首次尝试），默认3次
        base_delay: 基础延迟时间（秒），默认1秒
        max_delay: 最大延迟时间（秒），默认60秒
        exponential_base: 指数退避的底数，默认2.0
        retry_on: 需要重试的异常类型，默认为所有异常
    
    Returns:
        装饰后的函数
    
    Example:
        @retry_with_backoff(max_retries=3)
        async def my_async_function():
            # 你的代码
            pass
    """
    if retry_on is None:
        retry_on = (Exception,)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 因为包括首次尝试
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    # 检查是否是429错误（速率限制）
                    is_rate_limit = False
                    status_code = None
                    error_detail = ""
                    
                    if isinstance(e, httpx.HTTPStatusError):
                        status_code = e.response.status_code if e.response else None
                        if e.response is not None:
                            try:
                                error_detail = e.response.text
                                if error_detail:
                                    logger.error(f"HTTP 错误详情: {error_detail}")
                            except:
                                pass
                        
                        if status_code == 429:
                            is_rate_limit = True
                            logger.warning(f"遇到速率限制（429），准备重试...")
                    
                    # 如果是最后一次尝试，直接抛出异常
                    if attempt >= max_retries:
                        logger.error(f"达到最大重试次数 ({max_retries})，放弃重试")
                        raise
                    
                    # 计算等待时间
                    if is_rate_limit:
                        # 429错误使用指数退避：base_delay * (exponential_base ^ attempt)
                        wait_time = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.info(
                            f"请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}，"
                            f"等待 {wait_time:.2f} 秒后重试（指数退避）"
                        )
                    else:
                        # 其他错误使用线性延迟
                        wait_time = min(base_delay * (attempt + 1), max_delay)
                        logger.warning(
                            f"请求失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}，"
                            f"等待 {wait_time:.2f} 秒后重试"
                        )
                    
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    # 不在重试列表中的异常直接抛出
                    logger.error(f"遇到不可重试的异常: {e}")
                    raise
            
            # 理论上不会到达这里，但为了类型检查
            if last_exception:
                raise last_exception
            
            raise RuntimeError("重试逻辑异常")
        
        return wrapper
    return decorator


# 便捷装饰器：专门用于API请求，默认重试3次
def retry_api_request(max_retries: int = 3):
    """
    专门用于API请求的重试装饰器
    
    Args:
        max_retries: 最大重试次数，默认3次
    
    Returns:
        装饰后的函数
    
    Example:
        @retry_api_request(max_retries=3)
        async def call_api():
            # API调用代码
            pass
    """
    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        retry_on=(httpx.HTTPError, httpx.HTTPStatusError, Exception),
    )

