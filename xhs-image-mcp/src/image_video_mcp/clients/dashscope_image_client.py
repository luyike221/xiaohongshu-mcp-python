"""DashScope 图片生成客户端（支持 z-image-turbo 和 ImageSynthesis）"""

import asyncio
import os
from http import HTTPStatus
from pathlib import PurePosixPath
from typing import Optional
from urllib.parse import urlparse, unquote

import httpx
import requests
from dashscope import ImageSynthesis
from dashscope.common.error import InvalidTask
from loguru import logger


class DashScopeImageClient:
    """DashScope 图片生成客户端（支持 z-image-turbo 和 ImageSynthesis）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "z-image-turbo",
        default_size: str = "1120*1440",
        endpoint: Optional[str] = None,
    ):
        """
        初始化客户端

        Args:
            api_key: DashScope API Key（如果不提供，从环境变量 DASHSCOPE_API_KEY 读取）
            model: 模型名称，默认 "z-image-turbo"
            default_size: 默认图像尺寸，格式为 "width*height"，默认 "1120*1440"
            endpoint: API 端点（如果不提供，根据模型自动选择）
        """
        # 从环境变量或参数获取 API Key
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DashScope API Key 未配置。请设置环境变量 DASHSCOPE_API_KEY 或通过参数传入"
            )

        self.model = model
        self.default_size = default_size

        # 根据模型选择 API 端点
        if endpoint:
            self.endpoint = endpoint
        elif model == "z-image-turbo":
            self.endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        else:
            # 使用 ImageSynthesis API
            self.endpoint = None
            import dashscope
            dashscope.api_key = self.api_key

        # 创建 HTTP 客户端
        self.client = httpx.AsyncClient(
            timeout=300.0,  # 5分钟超时
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        logger.info(f"DashScope 客户端初始化: model={model}, size={default_size}, endpoint={self.endpoint or 'ImageSynthesis API'}")

    async def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        model: Optional[str] = None,
        n: int = 1,
    ) -> bytes:
        """
        生成图像（异步）

        Args:
            prompt: 图像生成提示词
            size: 图像尺寸，格式为 "width*height"（如 "1024*1024"），默认使用初始化时的 default_size
            model: 模型名称，默认使用初始化时的 model
            n: 生成图像数量，默认 1

        Returns:
            图片二进制数据（PNG 格式）
            如果 n > 1，返回第一张图片的数据

        Raises:
            ValueError: API 调用失败
            RuntimeError: 网络请求错误
        """
        size = size or self.default_size
        model = model or self.model

        logger.info(f"DashScope 生成图像: model={model}, size={size}, prompt={prompt[:50]}...")

        # 使用异步方法生成图片
        result = await self._generate_image_async(
            prompt,
            size,
            model,
            n,
        )

        if not result:
            raise ValueError("图片生成失败：API 返回为空")

        logger.info(f"✅ DashScope 图像生成成功: {len(result)} bytes")
        return result

    async def _generate_image_async(
        self,
        prompt: str,
        size: str,
        model: str,
        n: int,
    ) -> Optional[bytes]:
        """
        异步生成图片

        Args:
            prompt: 提示词
            size: 图像尺寸
            model: 模型名称
            n: 生成数量

        Returns:
            图片二进制数据，如果失败则返回 None
        """
        # 如果是 z-image-turbo，使用 multimodal-generation API
        if model == "z-image-turbo":
            return await self._generate_with_multimodal_api(prompt, size, model)
        else:
            # 使用 ImageSynthesis API（同步调用）
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._generate_image_sync,
                prompt,
                size,
                model,
                n,
            )

    async def _generate_with_multimodal_api(
        self,
        prompt: str,
        size: str,
        model: str,
    ) -> Optional[bytes]:
        """
        使用 multimodal-generation API 生成图片（z-image-turbo）

        Args:
            prompt: 提示词
            size: 图像尺寸
            model: 模型名称

        Returns:
            图片二进制数据
        """
        try:
            # 构建请求数据
            data = {
                "model": model,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                },
                "parameters": {
                    "prompt_extend": False,
                    "size": size
                }
            }

            logger.debug(f"请求 multimodal-generation API: {self.endpoint}")
            logger.debug(f"请求数据: model={model}, size={size}")

            # 发送请求
            response = await self.client.post(
                self.endpoint,
                json=data,
            )

            if response.status_code != HTTPStatus.OK:
                error_detail = response.text
                logger.error(f"API 返回错误 (状态码 {response.status_code}): {error_detail}")
                try:
                    error_json = response.json()
                    error_msg = error_json.get("message", error_detail)
                    raise ValueError(
                        f"❌ API 调用失败: status_code={response.status_code}, "
                        f"message={error_msg}"
                    )
                except:
                    raise ValueError(f"❌ API 调用失败: status_code={response.status_code}")

            # 解析 JSON 响应
            result = response.json()
            logger.debug(f"API 调用成功，响应键: {result.keys()}")

            # 从响应中提取图片 URL
            # z-image-turbo 返回格式: output.choices[0].message.content[0].image (URL)
            output = result.get("output", {})
            
            # 提取图片 URL（标准 multimodal-generation 格式）
            if "choices" in output and len(output["choices"]) > 0:
                choice = output["choices"][0]
                message = choice.get("message", {})
                content = message.get("content", [])
                
                # 查找图片 URL
                for item in content:
                    if isinstance(item, dict) and "image" in item:
                        image_url = item["image"]
                        if isinstance(image_url, str) and (image_url.startswith("http://") or image_url.startswith("https://")):
                            # 下载图片
                            logger.debug(f"下载图片: {image_url}")
                            loop = asyncio.get_event_loop()
                            image_bytes = await loop.run_in_executor(
                                None,
                                self._download_image_sync,
                                image_url
                            )
                            if image_bytes:
                                logger.info(f"✅ 从 URL 下载图片成功: {len(image_bytes)} bytes")
                                return image_bytes

            # 如果没找到图片，记录完整响应以便调试
            logger.error("API 返回成功但未找到图片 URL")
            logger.debug(f"完整响应: {result}")
            raise ValueError("API 返回成功但未找到图片 URL")

        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求错误: {e}")
            raise RuntimeError(f"HTTP 请求失败: {e}") from e
        except Exception as e:
            logger.error(f"生成图片时发生错误: {e}")
            raise

    def _download_image_sync(self, image_url: str) -> bytes:
        """
        同步下载图片（使用 requests，在 executor 中运行）
        
        Args:
            image_url: 图片 URL（OSS 签名 URL）
            
        Returns:
            图片二进制数据
            
        Raises:
            ValueError: 下载失败
            RuntimeError: 网络错误
        """
        # 下载 OSS 图片，添加必要的 header
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://dashscope.aliyuncs.com/",
        }
        
        # OSS URL 需要 Authorization header
        if "aliyuncs.com" in image_url:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        logger.debug(f"下载图片: {image_url[:100]}...")
        
        try:
            response = requests.get(image_url, headers=headers, timeout=60, verify=True, allow_redirects=True)
            response.raise_for_status()
            
            image_bytes = response.content
            logger.debug(f"下载图片成功: {len(image_bytes)} bytes")
            return image_bytes
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                error_msg = (
                    f"❌ 下载图片失败 (403 Forbidden)\n\n"
                    f"可能的原因：\n"
                    f"1. OSS 签名 URL 已过期\n"
                    f"2. OSS 访问权限不足\n\n"
                    f"URL: {image_url[:200]}..."
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"下载图片时网络错误: {e}")
            raise RuntimeError(f"下载图片失败: {e}") from e

    def _generate_image_sync(
        self,
        prompt: str,
        size: str,
        model: str,
        n: int,
    ) -> Optional[bytes]:
        """
        同步生成图片（使用 ImageSynthesis API，在 executor 中运行）

        Args:
            prompt: 提示词
            size: 图像尺寸
            model: 模型名称
            n: 生成数量

        Returns:
            图片二进制数据，如果失败则返回 None
        """
        try:
            rsp = ImageSynthesis.call(
                model=model,
                prompt=prompt,
                size=size,
                n=n,
            )

            if rsp.status_code == HTTPStatus.OK:
                logger.debug(f"API 调用成功: {rsp.output}")
                logger.debug(f"使用量: {rsp.usage}")

                # 获取第一张图片
                if rsp.output and rsp.output.results and len(rsp.output.results) > 0:
                    first_result = rsp.output.results[0]
                    image_url = first_result.url

                    # 下载图片
                    logger.debug(f"下载图片: {image_url}")
                    response = requests.get(image_url, timeout=60)
                    response.raise_for_status()

                    image_data = response.content
                    logger.debug(f"图片下载成功: {len(image_data)} bytes")

                    # 如果有多张图片，记录日志
                    if len(rsp.output.results) > 1:
                        logger.info(f"生成了 {len(rsp.output.results)} 张图片，返回第一张")

                    return image_data
                else:
                    logger.error("API 返回成功但未包含图片结果")
                    return None
            else:
                # 提供更详细的错误信息
                if rsp.status_code == 403:
                    error_msg = (
                        f"❌ API 访问被拒绝 (403 AccessDenied)\n\n"
                        f"可能的原因：\n"
                        f"1. API Key 无效或过期\n"
                        f"2. 账户未开通 {model} 模型服务\n"
                        f"3. 账户余额不足\n"
                        f"4. API Key 权限不足\n\n"
                        f"错误详情: code={rsp.code}, message={rsp.message}\n"
                        f"请检查：https://help.aliyun.com/zh/model-studio/error-code#access-denied"
                    )
                elif rsp.status_code == 401:
                    error_msg = (
                        f"❌ API Key 认证失败 (401 Unauthorized)\n\n"
                        f"请检查 DASHSCOPE_API_KEY 是否正确\n"
                        f"错误详情: code={rsp.code}, message={rsp.message}"
                    )
                else:
                    error_msg = (
                        f"❌ API 调用失败: status_code={rsp.status_code}, "
                        f"code={rsp.code}, message={rsp.message}"
                    )
                logger.error(error_msg)
                raise ValueError(error_msg)

        except InvalidTask as e:
            # 处理 dashscope 的 InvalidTask 异常（通常是 403 错误）
            error_str = str(e)
            if "403" in error_str or "AccessDenied" in error_str:
                error_msg = (
                    f"❌ API 访问被拒绝 (403 AccessDenied)\n\n"
                    f"可能的原因：\n"
                    f"1. 账户未开通 {model} 模型服务\n"
                    f"2. 账户余额不足\n"
                    f"3. API Key 权限不足\n"
                    f"4. 模型名称不正确\n\n"
                    f"建议：\n"
                    f"- 检查阿里云控制台是否开通了 {model} 服务\n"
                    f"- 尝试使用其他模型（如 wan2.5-t2i-preview）\n"
                    f"- 检查账户余额\n\n"
                    f"错误详情: {error_str}"
                )
            else:
                error_msg = f"❌ 任务创建失败: {error_str}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except requests.RequestException as e:
            logger.error(f"下载图片时网络错误: {e}")
            raise RuntimeError(f"下载图片失败: {e}") from e
        except Exception as e:
            # 检查是否是 InvalidTask 异常（dashscope 库抛出的）
            error_str = str(e)
            if "Invalid task" in error_str or "403" in error_str or "AccessDenied" in error_str:
                error_msg = (
                    f"❌ API 访问被拒绝 (403 AccessDenied)\n\n"
                    f"可能的原因：\n"
                    f"1. 账户未开通 {model} 模型服务\n"
                    f"2. 账户余额不足\n"
                    f"3. API Key 权限不足\n"
                    f"4. 模型名称不正确\n\n"
                    f"建议：\n"
                    f"- 检查阿里云控制台是否开通了 {model} 服务\n"
                    f"- 尝试使用其他模型（如 wan2.5-t2i-preview）\n"
                    f"- 检查账户余额\n\n"
                    f"错误详情: {error_str}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg) from e
            else:
                logger.error(f"生成图片时发生错误: {e}")
                raise

    def generate_image_and_save(
        self,
        prompt: str,
        save_dir: str = "./",
        size: Optional[str] = None,
        model: Optional[str] = None,
        n: int = 1,
    ) -> list[str]:
        """
        生成图像并保存到本地（同步方法，用于测试）

        Args:
            prompt: 图像生成提示词
            save_dir: 保存目录，默认当前目录
            size: 图像尺寸，格式为 "width*height"
            model: 模型名称
            n: 生成图像数量

        Returns:
            保存的文件路径列表
        """
        size = size or self.default_size
        model = model or self.model

        logger.info(f"DashScope 生成并保存图像: model={model}, size={size}, n={n}")

        rsp = ImageSynthesis.call(
            model=model,
            prompt=prompt,
            size=size,
            n=n,
        )

        saved_files = []

        if rsp.status_code == HTTPStatus.OK:
            logger.info(f"API 调用成功: {rsp.output}")
            logger.info(f"使用量: {rsp.usage}")

            # 保存所有生成的图片
            for result in rsp.output.results:
                image_url = result.url
                file_name = PurePosixPath(unquote(urlparse(image_url).path)).parts[-1]
                file_path = os.path.join(save_dir, file_name)

                logger.debug(f"下载并保存图片: {image_url} -> {file_path}")
                response = requests.get(image_url, timeout=60)
                response.raise_for_status()

                with open(file_path, "wb+") as f:
                    f.write(response.content)

                saved_files.append(file_path)
                logger.info(f"✅ 图片已保存: {file_path}")

        else:
            error_msg = (
                f"API 调用失败: status_code={rsp.status_code}, "
                f"code={rsp.code}, message={rsp.message}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        return saved_files

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
