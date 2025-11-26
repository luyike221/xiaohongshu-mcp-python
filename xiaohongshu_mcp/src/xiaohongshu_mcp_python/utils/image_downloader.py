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
            
            # 如果提供了文件名，先检查文件是否已存在
            if filename:
                file_path = self.download_dir / filename
                if file_path.exists():
                    logger.info(f"图片已存在，跳过下载: {file_path}")
                    return str(file_path)
            
            # 下载图片（先下载以获取 Content-Type）
            logger.info(f"开始下载图片: {url}")
            response = await self.client.get(url)
            response.raise_for_status()
            
            # 获取 Content-Type
            content_type = response.headers.get("content-type", "")
            
            # 验证内容类型（如果 Content-Type 明确不是图片，则警告但不直接返回）
            content_type_lower = content_type.lower() if content_type else ""
            if content_type_lower and not content_type_lower.startswith("image/"):
                # 如果 Content-Type 明确不是图片（如 text/html），则拒绝
                if content_type_lower.startswith("text/") or content_type_lower.startswith("application/json"):
                    logger.warning(f"响应内容不是图片: {content_type}")
                    return None
                # 如果 Content-Type 不明确或为空，继续下载，稍后通过文件内容验证
            
            # 生成文件名（使用 Content-Type 来确定扩展名）
            if not filename:
                filename = self._generate_filename(url, content_type)
            
            file_path = self.download_dir / filename
            
            # 再次检查文件是否已存在（可能在下载过程中其他进程创建了）
            if file_path.exists():
                logger.info(f"图片已存在，跳过保存: {file_path}")
                return str(file_path)
            
            # 保存文件
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(response.content)
            
            # 验证下载的文件是否是有效的图片
            if not self._validate_image_file(str(file_path)):
                logger.warning(f"下载的文件不是有效的图片: {file_path}")
                # 删除无效文件
                try:
                    file_path.unlink()
                except Exception:
                    pass
                return None
            
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
            
            # 必须包含 scheme 和 netloc（域名），才是有效的 URL
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # 只接受 http 和 https 协议
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # 检查文件扩展名（如果路径有扩展名，优先检查）
            path = parsed.path.lower()
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
            
            # 如果路径以图片扩展名结尾，肯定是图片URL
            if any(path.endswith(ext) for ext in image_extensions):
                return True
            
            # 如果路径没有扩展名，但包含查询参数或路径中有图片相关的标识，
            # 也认为是可能的图片URL（很多图片服务使用动态URL，如 Bing、CDN 等）
            # 这种情况下，只要是有 scheme 和 netloc 的 http/https URL，就认为是 URL
            # 让下载时通过 Content-Type 来验证是否是真正的图片
            
            # 检查是否是本地路径（Windows 路径如 C:\ 或 Unix 路径如 /path/to/file）
            # 如果包含常见的本地路径特征，则不是 URL
            if url.startswith('/') and not url.startswith('//'):
                # Unix 绝对路径
                return False
            if len(url) >= 2 and url[1] == ':' and url[0].isalpha():
                # Windows 绝对路径如 C:\
                return False
            
            # 其他情况：有 scheme 和 netloc 的 http/https URL，认为是可能的图片URL
            return True
            
        except Exception:
            return False
    
    def _generate_filename(self, url: str, content_type: Optional[str] = None) -> str:
        """
        根据URL生成唯一的文件名
        
        Args:
            url: 图片URL
            content_type: HTTP响应的Content-Type（可选，用于确定文件扩展名）
            
        Returns:
            生成的文件名
        """
        try:
            # 首先尝试从 Content-Type 获取扩展名
            ext = None
            if content_type:
                content_type = content_type.lower()
                # 常见的图片 Content-Type 映射
                content_type_map = {
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'image/png': '.png',
                    'image/gif': '.gif',
                    'image/webp': '.webp',
                    'image/bmp': '.bmp',
                    'image/svg+xml': '.svg',
                }
                # 提取主要的 content type（去掉参数）
                main_type = content_type.split(';')[0].strip()
                ext = content_type_map.get(main_type)
            
            # 如果 Content-Type 没有提供扩展名，尝试从 URL 路径获取
            if not ext:
                parsed = urlparse(url)
                original_name = Path(parsed.path).name
                
                if original_name and '.' in original_name:
                    _, ext = os.path.splitext(original_name)
                    # 验证扩展名是否有效
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
                    if ext.lower() not in valid_extensions:
                        ext = None
            
            # 如果还是没有扩展名，默认使用 .jpg
            if not ext:
                ext = '.jpg'
            
            # 确保扩展名以点开头
            if not ext.startswith('.'):
                ext = '.' + ext
            
            return f"{uuid.uuid4().hex[:8]}{ext}"
                
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