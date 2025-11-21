"""基础仓储"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseRepository(ABC):
    """基础仓储类"""

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Any:
        """创建记录"""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Any]:
        """根据 ID 获取记录"""
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Any]:
        """更新记录"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除记录"""
        pass

    @abstractmethod
    async def list(self, filters: Optional[Dict[str, Any]] = None, limit: int = 100, offset: int = 0) -> List[Any]:
        """列出记录"""
        pass

