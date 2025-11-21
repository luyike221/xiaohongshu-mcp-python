"""DeepSeek 客户端"""

from typing import AsyncIterator, List, Optional

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from ....config import model_config
from ...tools.logging import get_logger
from .base import BaseLLMClient

logger = get_logger(__name__)


class DeepSeekClient(BaseLLMClient):
    """DeepSeek 客户端"""

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
        初始化 DeepSeek 客户端

        Args:
            model: 模型名称，如 deepseek-chat, deepseek-coder 等
            temperature: 温度参数 (0.0-2.0)
            max_tokens: 最大 token 数
            timeout: 请求超时时间（秒）
            api_key: API Key（如果不提供，从配置中读取）
            endpoint: API 端点（如果不提供，从配置中读取）
            **kwargs: 其他参数
        """
        # 从配置中获取默认值（如果有 OCR 配置，可以复用）
        # 这里使用通用的 DeepSeek API
        default_endpoint = endpoint or "https://api.deepseek.com/v1/chat/completions"
        default_model = model or "deepseek-chat"

        # 尝试从配置中获取 API Key
        try:
            ocr_config = model_config.get_deepseek_ocr_config()
            default_api_key = api_key or ocr_config.api_key
            if ocr_config.endpoint and not endpoint:
                default_endpoint = ocr_config.endpoint
        except ValueError:
            default_api_key = api_key
            if not default_api_key:
                raise ValueError("必须提供 api_key 或配置 DEEPSEEK_OCR_API_KEY")

        super().__init__(
            model=default_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs,
        )

        self.api_key = default_api_key
        self.endpoint = default_endpoint

    def _create_client(self):
        """创建 LangChain ChatOpenAI 客户端"""
        return ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
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
            logger.error("DeepSeek 生成失败", model=self.model, error=str(e))
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
            logger.error("DeepSeek 流式生成失败", model=self.model, error=str(e))
            raise




