"""基础 LLM 客户端"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, List, Optional

from langchain_core.messages import BaseMessage


class BaseLLMClient(ABC):
    """基础 LLM 客户端抽象类"""

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        **kwargs,
    ):
        """
        初始化客户端

        Args:
            model: 模型名称
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大 token 数
            timeout: 请求超时时间（秒）
            **kwargs: 其他模型特定参数
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_params = kwargs
        self._client = None

    @abstractmethod
    def _create_client(self):
        """创建底层客户端（由子类实现）"""
        pass

    @property
    def client(self):
        """获取客户端实例（懒加载）"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @abstractmethod
    async def generate(
        self,
        messages: List[BaseMessage],
        **kwargs,
    ) -> str:
        """
        生成文本

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[BaseMessage],
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        流式生成文本

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            文本块
        """
        pass

    def update_config(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ):
        """
        更新配置

        Args:
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 超时时间
            **kwargs: 其他参数
        """
        if model is not None:
            self.model = model
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if timeout is not None:
            self.timeout = timeout
        if kwargs:
            self.extra_params.update(kwargs)
        # 重置客户端以应用新配置
        self._client = None




