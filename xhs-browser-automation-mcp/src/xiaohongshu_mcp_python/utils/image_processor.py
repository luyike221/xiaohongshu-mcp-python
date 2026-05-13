"""
图片处理器
处理混合的图片URL和本地路径
"""

import os
from pathlib import Path
from typing import List, Optional, Sequence, Union, Any
from loguru import logger

from .image_downloader import ImageDownloader
from ..config import PublishConfig


def coerce_image_paths_arg(raw: Union[None, str, Sequence[Any]]) -> List[str]:
    """
    将 MCP/HTTP 传入的 images 统一为字符串路径列表。

    常见误用：把单个 Windows 路径当成字符串传入而非 ['path']，
    若直接 for 迭代会得到 'C'、':' 等单字符，校验全部失败。
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        s = raw.strip()
        return [s] if s else []
    out: List[str] = []
    for item in raw:
        if item is None:
            continue
        s = str(item).strip()
        if not s:
            continue
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
            s = s[1:-1].strip()
        out.append(s)
    return out


def normalize_local_path_str(path: str) -> str:
    """展开 ~ 与环境变量，规范化分隔符（Windows 上 Path 可接受两种斜杠）。"""
    p = os.path.expandvars(os.path.expanduser(path.strip()))
    return os.path.normpath(p)


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self, download_dir: Optional[str] = None):
        """
        初始化图片处理器
        
        Args:
            download_dir: 下载目录
        """
        self.downloader = ImageDownloader(download_dir)
    
    async def process_images(self, image_paths: Union[None, str, Sequence[Any]]) -> List[str]:
        """
        处理图片路径列表，下载URL图片并验证本地图片
        
        Args:
            image_paths: 图片路径列表，或单个路径字符串（均支持）
            
        Returns:
            处理后的本地图片路径列表
        """
        paths = coerce_image_paths_arg(image_paths)
        if not paths:
            return []

        logger.info(f"开始处理 {len(paths)} 张图片（归一化后路径: {paths!r}）")
        
        # 分离URL和本地路径
        urls = []
        local_paths = []
        
        for path in paths:
            # 处理 file:// URL 格式，转换为本地路径
            if path.startswith('file://'):
                # 移除 file:// 前缀，保留路径部分
                # file:///path/to/file -> /path/to/file
                # file://C:/path/to/file -> C:/path/to/file (Windows)
                local_path = path[7:]  # 移除 'file://' 前缀
                # 对于 Linux/Mac，file:// 后面可能有三个斜杠，需要处理
                if local_path.startswith('//'):
                    local_path = local_path[1:]  # 移除多余的斜杠
                local_paths.append(local_path)
            elif self.downloader.is_image_url(path):
                urls.append(path)
            else:
                local_paths.append(path)
        
        logger.info(f"发现 {len(urls)} 个URL，{len(local_paths)} 个本地路径")
        
        # 下载URL图片
        downloaded_paths = []
        if urls:
            downloaded_paths = await self.downloader.download_images(urls)
        
        # 验证本地图片
        validated_local_paths = []
        for path in local_paths:
            norm = normalize_local_path_str(path)
            if self._validate_local_image(norm):
                validated_local_paths.append(norm)
            else:
                logger.warning(f"本地图片无效或不存在: {path!r}（规范化后: {norm!r}）")
        
        # 合并结果
        all_paths = downloaded_paths + validated_local_paths
        
        # 验证图片格式和大小
        final_paths = []
        for path in all_paths:
            if self._validate_image_format(path) and self._validate_image_size(path):
                final_paths.append(path)
            else:
                logger.warning(f"图片验证失败，跳过: {path}")
        
        logger.info(f"图片处理完成，最终得到 {len(final_paths)} 张有效图片")
        return final_paths
    
    def _validate_local_image(self, path: str) -> bool:
        """
        验证本地图片是否存在且可读
        
        Args:
            path: 图片路径
            
        Returns:
            是否有效
        """
        try:
            norm = normalize_local_path_str(path)
            file_path = Path(norm)

            # 检查文件是否存在
            if not file_path.exists():
                logger.warning(f"图片文件不存在: {path!r} -> {norm!r}")
                return False

            # 检查是否是文件
            if not file_path.is_file():
                logger.warning(f"路径不是文件: {path!r} -> {norm!r}")
                return False

            # 检查文件是否可读
            if not os.access(str(file_path), os.R_OK):
                logger.warning(f"图片文件不可读: {norm!r}")
                return False

            return True

        except Exception as e:
            logger.error(f"验证本地图片失败 {path!r}: {e}")
            return False
    
    def _validate_image_format(self, path: str) -> bool:
        """
        验证图片格式是否支持
        
        Args:
            path: 图片路径
            
        Returns:
            是否支持的格式
        """
        try:
            file_path = Path(path)
            ext = file_path.suffix.lower()
            
            if ext not in PublishConfig.SUPPORTED_IMAGE_FORMATS:
                logger.warning(f"不支持的图片格式 {ext}: {path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证图片格式失败 {path}: {e}")
            return False
    
    def _validate_image_size(self, path: str) -> bool:
        """
        验证图片文件大小
        
        Args:
            path: 图片路径
            
        Returns:
            文件大小是否符合要求
        """
        try:
            file_size = os.path.getsize(path)
            
            if file_size > PublishConfig.MAX_IMAGE_SIZE:
                logger.warning(f"图片文件过大 {file_size} bytes: {path}")
                return False
            
            if file_size == 0:
                logger.warning(f"图片文件为空: {path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证图片大小失败 {path}: {e}")
            return False
    
    def _validate_image_content(self, path: str) -> bool:
        """
        验证图片内容是否有效
        
        Args:
            path: 图片路径
            
        Returns:
            图片内容是否有效
        """
        try:
            from PIL import Image
            
            with Image.open(path) as img:
                # 验证图片可以正常打开
                img.verify()
                
                # 重新打开获取尺寸信息（verify后需要重新打开）
                with Image.open(path) as img2:
                    width, height = img2.size
                    
                    # 检查图片尺寸是否合理
                    if width < 1 or height < 1:
                        logger.warning(f"图片尺寸无效 {width}x{height}: {path}")
                        return False
                    
                    # 检查图片尺寸是否过大
                    if width > 10000 or height > 10000:
                        logger.warning(f"图片尺寸过大 {width}x{height}: {path}")
                        return False
            
            return True
            
        except ImportError:
            logger.warning("PIL库未安装，跳过图片内容验证")
            return True
        except Exception as e:
            logger.warning(f"图片内容验证失败 {path}: {e}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.downloader.cleanup()
            logger.debug("图片处理器清理完成")
        except Exception as e:
            logger.error(f"清理图片处理器失败: {e}")