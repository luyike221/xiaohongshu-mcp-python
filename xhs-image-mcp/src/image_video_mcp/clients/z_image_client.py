"""Z-Image 图片生成客户端"""

import asyncio
from typing import Optional

import httpx
from loguru import logger

from ..config import settings
from ..utils.retry import retry_api_request

# 全局信号量，限制并发为1
_semaphore = asyncio.Semaphore(1)


class ZImageClient:
    """Z-Image 图片生成客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        初始化客户端

        Args:
            base_url: API 基础 URL（如果不提供，从配置中读取）
            timeout: 请求超时时间（如果不提供，从配置中读取）
            max_retries: 最大重试次数（如果不提供，从配置中读取）
        """
        try:
            config = settings.get_z_image_config()
            self.base_url = base_url or config.base_url
            self.timeout = timeout or config.timeout
            self.max_retries = max_retries or config.max_retries
            self.default_height = config.default_height
            self.default_width = config.default_width
            self.default_num_inference_steps = config.default_num_inference_steps
            self.default_guidance_scale = config.default_guidance_scale
        except ValueError as e:
            raise ValueError(f"配置错误: {e}")

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
            },
        )

    async def generate_image(
        self,
        prompt: str,
        height: Optional[int] = None,
        width: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> bytes:
        """
        生成图像

        Args:
            prompt: 图像生成提示词
            height: 图像高度，默认 1024
            width: 图像宽度，默认 1024
            num_inference_steps: 推理步数，默认 9
            guidance_scale: 引导强度，默认 0.0（Turbo 模型应为 0）
            seed: 随机种子（可选）

        Returns:
            图片二进制数据（PNG 格式）

        Raises:
            httpx.HTTPError: HTTP 请求错误
            ValueError: 参数验证错误
        """
        # 使用默认值
        height = height or self.default_height
        width = width or self.default_width
        num_inference_steps = num_inference_steps or self.default_num_inference_steps
        guidance_scale = guidance_scale if guidance_scale is not None else self.default_guidance_scale

        # 构建请求数据
        data = {
            "prompt": prompt,
            "height": height,
            "width": width,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }

        if seed is not None:
            data["seed"] = seed

        logger.info(f"Z-Image 生成图像: prompt={prompt[:50]}..., size={width}x{height}")

        # 使用信号量限制并发为1
        async with _semaphore:
            # 使用装饰器处理重试逻辑
            return await self._make_request(data)

    @retry_api_request(max_retries=3)
    async def _make_request(self, data: dict) -> bytes:
        """
        发送API请求（内部方法，使用重试装饰器）

        Args:
            data: 请求数据

        Returns:
            图片二进制数据
        """
        endpoint_url = f"{self.base_url.rstrip('/')}/generate"

        logger.debug(f"请求 URL: {endpoint_url}")
        logger.debug(f"请求数据: {data}")

        response = await self.client.post(
            endpoint_url,
            json=data,
        )

        # 如果请求失败，记录详细错误信息
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"API 返回错误 (状态码 {response.status_code}): {error_detail}")
            try:
                error_json = response.json()
                logger.error(f"错误详情: {error_json}")
            except:
                pass

        response.raise_for_status()

        # 读取图片二进制数据
        image_data = await response.aread()
        logger.info(f"Z-Image 图像生成成功: {len(image_data)} bytes")
        return image_data

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

