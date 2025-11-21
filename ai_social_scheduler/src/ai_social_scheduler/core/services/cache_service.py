"""缓存服务"""

from typing import Any, Optional
import json

import redis.asyncio as redis

from ..config import settings
from ..tools.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """缓存服务"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        """获取 Redis 客户端"""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
            )
        return self.redis_client

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("缓存获取失败", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            client = await self._get_client()
            serialized = json.dumps(value)
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)
            return True
        except Exception as e:
            logger.error("缓存设置失败", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error("缓存删除失败", key=key, error=str(e))
            return False

    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()

