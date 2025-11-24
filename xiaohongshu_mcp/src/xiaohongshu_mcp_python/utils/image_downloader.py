"""
图片下载器
处理网络图片的下载和保存
"""

import os
import uuid
import asyncio
import aiofiles
import httpx
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from loguru import logger

from ..config import StorageConfig, ApiConfig


class ImageDownloader:
    """图片下载器"""
    
    def __init__(self, download_dir: Optional[str] = None):
        """
        初始化图片下载器
        
        Args:
            download_dir: 下载目录，默认使用配置中的下载目录
        """
        self.download_dir = Path(download_dir or StorageConfig.DOWNLOAD_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # HTTP 客户端配置
        self.client = httpx.AsyncClient(
            headers=ApiConfig.DEFAULT_HEADERS,
            timeout=ApiConfig.REQUEST_TIMEOUT,
            follow_redirects=True
        )
    
    async def download_image(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        下载单张图片
        
        Args:
            url: 图片URL
            filename: 保存的文件名，如果不提供则自动生成
            
        Returns:
            下载成功返回本地文件路径，失败返回None
        """
        try:
            if not self.is_image_url(url):
                logger.warning(f"不是有效的图片URL: {url}")
                return None
            
            # 生成文件名
            if not filename:
                filename = self._generate_filename(url)
            
            file_path = self.download_dir / filename
            
            # 如果文件已存在，直接返回路径
            if file_path.exists():
                logger.info(f"图片已存在，跳过下载: {file_path}")
                return str(file_path)
            
            # 下载图片
            logger.info(f"开始下载图片: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            
            # 验证内容类型
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                logger.warning(f"响应内容不是图片: {content_type}")
                return None
            
            # 保存文件
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(response.content)
            
            logger.info(f"图片下载成功: {file_path}")
            return str(file_path)
            
        except httpx.HTTPError as e:
            logger.error(f"下载图片HTTP错误 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"下载图片失败 {url}: {e}")
            return None
    
    async def download_images(self, urls: List[str]) -> List[str]:
        """
        批量下载图片
        
        Args:
            urls: 图片URL列表
            
        Returns:
            成功下载的本地文件路径列表
        """
        if not urls:
            return []
        
        logger.info(f"开始批量下载 {len(urls)} 张图片")
        
        # 并发下载
        tasks = [self.download_image(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功的结果
        downloaded_paths = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"下载图片失败 {urls[i]}: {result}")
            elif result:
                downloaded_paths.append(result)
        
        logger.info(f"批量下载完成，成功 {len(downloaded_paths)} 张，失败 {len(urls) - len(downloaded_paths)} 张")
        return downloaded_paths
    
    def is_image_url(self, url: str) -> bool:
        """
        检查URL是否是图片链接
        
        Args:
            url: 要检查的URL
            
        Returns:
            是否是图片URL
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # 检查文件扩展名
            path = parsed.path.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
            
            return any(path.endswith(ext) for ext in image_extensions)
            
        except Exception:
            return False
    
    def _generate_filename(self, url: str) -> str:
        """
        根据URL生成唯一的文件名
        
        Args:
            url: 图片URL
            
        Returns:
            生成的文件名
        """
        try:
            parsed = urlparse(url)
            original_name = Path(parsed.path).name
            
            # 如果原始文件名有扩展名，保留扩展名
            if original_name and '.' in original_name:
                name, ext = os.path.splitext(original_name)
                return f"{uuid.uuid4().hex[:8]}_{name}{ext}"
            else:
                # 默认使用 .jpg 扩展名
                return f"{uuid.uuid4().hex[:8]}.jpg"
                
        except Exception:
            return f"{uuid.uuid4().hex[:8]}.jpg"
    
    def _validate_image_file(self, file_path: str) -> bool:
        """
        验证下载的文件是否是有效的图片
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否是有效图片
        """
        try:
            from PIL import Image
            
            with Image.open(file_path) as img:
                img.verify()
            return True
            
        except Exception as e:
            logger.warning(f"图片验证失败 {file_path}: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.client.aclose()
            logger.debug("图片下载器清理完成")
        except Exception as e:
            logger.error(f"清理图片下载器失败: {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            import asyncio
            if hasattr(self, 'client') and not self.client.is_closed:
                # 在事件循环中清理
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.client.aclose())
                    else:
                        loop.run_until_complete(self.client.aclose())
                except Exception:
                    pass
        except Exception:
            pass