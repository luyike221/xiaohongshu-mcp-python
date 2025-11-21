"""图片处理工具"""

from typing import List, Tuple
from PIL import Image


def resize_image(image_path: str, size: Tuple[int, int]) -> str:
    """调整图片大小"""
    # TODO: 实现图片调整大小逻辑
    return image_path


def validate_image(image_path: str) -> bool:
    """验证图片"""
    try:
        Image.open(image_path)
        return True
    except Exception:
        return False


def get_image_info(image_path: str) -> dict:
    """获取图片信息"""
    try:
        img = Image.open(image_path)
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
        }
    except Exception:
        return {}

