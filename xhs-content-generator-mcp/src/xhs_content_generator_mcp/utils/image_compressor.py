"""图片压缩工具"""
import io
from PIL import Image
from typing import Optional


def compress_image(
    image_data: bytes,
    max_size_kb: int = 200,  # 默认200KB
    quality_start: int = 85,
    quality_min: int = 20,
    max_dimension: int = 2048
) -> bytes:
    """
    压缩图片到指定大小以内

    Args:
        image_data: 原始图片数据
        max_size_kb: 最大文件大小（KB）
        quality_start: 起始压缩质量（1-100）
        quality_min: 最低压缩质量（1-100）
        max_dimension: 最大边长（像素）

    Returns:
        压缩后的图片数据
    """
    max_size_bytes = max_size_kb * 1024

    # 如果原图已经小于目标大小，直接返回
    if len(image_data) <= max_size_bytes:
        return image_data

    try:
        # 打开图片
        img = Image.open(io.BytesIO(image_data))

        # 转换为 RGB（处理 RGBA 等格式）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 如果图片尺寸过大，先缩小
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 逐步降低质量直到满足大小要求
        quality = quality_start
        compressed_data = None

        while quality >= quality_min:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed_data = output.getvalue()

            if len(compressed_data) <= max_size_bytes:
                break

            quality -= 5

        # 如果还是太大，进一步缩小尺寸
        if len(compressed_data) > max_size_bytes:
            width, height = img.size
            while len(compressed_data) > max_size_bytes and max(width, height) > 512:
                width = int(width * 0.9)
                height = int(height * 0.9)
                img_resized = img.resize((width, height), Image.Resampling.LANCZOS)

                output = io.BytesIO()
                img_resized.save(output, format='JPEG', quality=quality_min, optimize=True)
                compressed_data = output.getvalue()

        original_size_kb = len(image_data) / 1024
        compressed_size_kb = len(compressed_data) / 1024
        compression_ratio = (1 - compressed_size_kb / original_size_kb) * 100

        print(f"[图片压缩] {original_size_kb:.1f}KB → {compressed_size_kb:.1f}KB (压缩 {compression_ratio:.1f}%)")

        return compressed_data

    except Exception as e:
        print(f"[图片压缩] 压缩失败，返回原图: {e}")
        return image_data


def compress_images(images: list[bytes], max_size_kb: int = 200) -> list[bytes]:
    """
    批量压缩图片

    Args:
        images: 图片数据列表
        max_size_kb: 最大文件大小（KB）

    Returns:
        压缩后的图片数据列表
    """
    return [compress_image(img, max_size_kb) for img in images]

