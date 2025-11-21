"""Agent 基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..tools.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent 逻辑"""
        pass

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """运行 Agent（包含错误处理）"""
        try:
            self.logger.info("Agent started", agent=self.name)
            result = await self.execute(state)
            self.logger.info("Agent completed", agent=self.name)
            return result
        except Exception as e:
            self.logger.error("Agent failed", agent=self.name, error=str(e))
            raise

