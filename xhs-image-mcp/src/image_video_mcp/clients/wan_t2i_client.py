"""通义万相 T2I 客户端"""

import json
from typing import Optional, Dict, Any

import httpx
from loguru import logger

from ..config import settings
from ..utils.retry import retry_api_request


class WanT2IClient:
    """通义万相 2.5 T2I 预览版客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        初始化客户端

        Args:
            api_key: API Key（如果不提供，从配置中读取）
            endpoint: API 端点（如果不提供，从配置中读取）
            model: 模型名称（如果不提供，从配置中读取）
            timeout: 请求超时时间（如果不提供，从配置中读取）
            max_retries: 最大重试次数（如果不提供，从配置中读取）
        """
        try:
            config = settings.get_wan_t2i_config()
            self.api_key = api_key or config.api_key
            self.endpoint = endpoint or config.endpoint
            self.model = model or config.model
            self.timeout = timeout or config.timeout
            self.max_retries = max_retries or config.max_retries
            self.default_size = config.default_size
            self.default_n = config.default_n
        except ValueError as e:
            raise ValueError(f"配置错误: {e}")

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",  # 必须的请求头，用于异步调用
            },
        )

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: Optional[str] = None,
        n: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        生成图像

        Args:
            prompt: 图像生成提示词
            negative_prompt: 负面提示词（可选）
            size: 图像尺寸，格式为 "宽*高"，如 "1280*1280"
                  总像素必须在 768*768 到 1440*1440 之间
                  宽高比必须在 1:4 到 4:1 之间
            n: 生成图像数量，默认为 1
            seed: 随机种子（可选）

        Returns:
            包含生成结果的字典

        Raises:
            httpx.HTTPError: HTTP 请求错误
            ValueError: 参数验证错误
        """
        # 使用默认值
        size = size or self.default_size
        n = n or self.default_n

        # 验证尺寸格式
        if "*" not in size:
            raise ValueError(f"尺寸格式错误，应为 '宽*高'，如 '1280*1280'，当前: {size}")

        try:
            width, height = map(int, size.split("*"))
            total_pixels = width * height
            aspect_ratio = width / height if height > 0 else 0

            if total_pixels < 768 * 768 or total_pixels > 1440 * 1440:
                raise ValueError(
                    f"总像素必须在 768*768 到 1440*1440 之间，当前: {total_pixels}"
                )

            if aspect_ratio < 0.25 or aspect_ratio > 4.0:
                raise ValueError(
                    f"宽高比必须在 1:4 到 4:1 之间，当前: {aspect_ratio:.2f}"
                )
        except ValueError as e:
            raise ValueError(f"尺寸参数验证失败: {e}")

        # 构建请求数据
        data = {
            "model": self.model,
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "size": size,
                "n": n,
            },
        }

        if negative_prompt:
            data["input"]["negative_prompt"] = negative_prompt

        if seed is not None:
            data["parameters"]["seed"] = seed

        logger.info(f"生成图像: prompt={prompt[:50]}..., size={size}, n={n}")

        # 使用装饰器处理重试逻辑
        return await self._make_request(data)
    
    @retry_api_request(max_retries=3)
    async def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送API请求（内部方法，使用重试装饰器）
        
        Args:
            data: 请求数据
            
        Returns:
            API响应结果
        """
        endpoint_url = self.endpoint
        
        logger.debug(f"请求 URL: {endpoint_url}")
        logger.debug(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
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
                logger.error(f"错误详情: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
            except:
                pass
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"图像生成成功: {result.get('output', {}).get('task_id', 'N/A')}")
        return result

    @retry_api_request(max_retries=3)
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态信息，包含 task_status, results 等

        Raises:
            httpx.HTTPError: HTTP 请求错误
        """
        # 根据文档，查询任务结果的端点
        # 北京地域：GET https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}
        task_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        
        logger.info(f"查询任务状态: task_id={task_id}")
        
        response = await self.client.get(task_url)
        response.raise_for_status()
        result = response.json()
        
        task_status = result.get("output", {}).get("task_status", "UNKNOWN")
        logger.info(f"任务状态: {task_status}")
        
        return result

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 便捷函数
async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    size: Optional[str] = None,
    n: Optional[int] = None,
    seed: Optional[int] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    便捷函数：生成图像

    Args:
        prompt: 图像生成提示词
        negative_prompt: 负面提示词（可选）
        size: 图像尺寸
        n: 生成图像数量
        seed: 随机种子
        api_key: API Key（可选，如果不提供则从配置读取）

    Returns:
        包含生成结果的字典
    """
    async with WanT2IClient(api_key=api_key) as client:
        return await client.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            n=n,
            seed=seed,
        )

