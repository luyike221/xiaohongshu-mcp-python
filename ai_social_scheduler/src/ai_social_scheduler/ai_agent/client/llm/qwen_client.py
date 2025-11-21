"""阿里百炼（通义千问）客户端"""

from typing import AsyncIterator, List, Optional

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from ....config import model_config
from ...tools.logging import get_logger
from .base import BaseLLMClient

logger = get_logger(__name__)


class QwenClient(BaseLLMClient):
    """阿里百炼（通义千问）客户端"""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: int = 60,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化通义千问客户端

        Args:
            model: 模型名称，如 qwen-plus, qwen-turbo, qwen-max 等
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大 token 数
            timeout: 请求超时时间（秒）
            api_key: API Key（如果不提供，从配置中读取）
            endpoint: API 端点（如果不提供，从配置中读取）
            **kwargs: 其他参数
        """
        # 从配置中获取默认值
        try:
            config = model_config.get_alibaba_bailian_config()
            default_model = model or config.model
            default_temperature = temperature if temperature != 0.7 else config.temperature
            default_max_tokens = max_tokens or config.max_tokens
            default_timeout = timeout if timeout != 60 else config.timeout
            default_api_key = api_key or config.api_key
            default_endpoint = endpoint or config.endpoint
        except ValueError:
            # 如果配置未设置，使用传入的参数或默认值
            default_model = model or "qwen-plus"
            default_temperature = temperature
            default_max_tokens = max_tokens
            default_timeout = timeout
            default_api_key = api_key
            default_endpoint = endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1"
            if not default_api_key:
                raise ValueError("必须提供 api_key 或配置 ALIBABA_BAILIAN_API_KEY")

        super().__init__(
            model=default_model,
            temperature=default_temperature,
            max_tokens=default_max_tokens,
            timeout=default_timeout,
            **kwargs,
        )

        self.api_key = default_api_key
        self.endpoint = default_endpoint

    def _create_client(self):
        """创建 LangChain ChatOpenAI 客户端"""
        # 处理 API Key 格式（如果需要）
        api_key = self.api_key
        if not api_key.startswith("sk-"):
            api_key = f"sk-{api_key}"

        return ChatOpenAI(
            model=self.model,
            openai_api_key=api_key,
            base_url=self.endpoint,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            **self.extra_params,
        )

    async def generate(
        self,
        messages: List[BaseMessage],
        **kwargs,
    ) -> str:
        """生成文本"""
        try:
            client = self.client
            response = await client.ainvoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error("通义千问生成失败", model=self.model, error=str(e))
            raise

    async def generate_stream(
        self,
        messages: List[BaseMessage],
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式生成文本"""
        try:
            client = self.client
            async for chunk in client.astream(messages, **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error("通义千问流式生成失败", model=self.model, error=str(e))
            raise

    def generate_sync(
        self,
        messages: List[BaseMessage],
        **kwargs,
    ) -> str:
        """同步生成文本"""
        try:
            client = self.client
            response = client.invoke(messages, **kwargs)
            return response.content
        except Exception as e:
            logger.error("通义千问生成失败", model=self.model, error=str(e))
            raise

    def generate_stream_sync(
        self,
        messages: List[BaseMessage],
        **kwargs,
    ):
        """同步流式生成文本"""
        try:
            client = self.client
            for chunk in client.stream(messages, **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error("通义千问流式生成失败", model=self.model, error=str(e))
            raise

