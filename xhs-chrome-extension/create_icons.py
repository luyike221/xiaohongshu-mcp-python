#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从源图片创建不同尺寸的 Chrome 扩展图标
"""
import os
import sys

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("错误: 需要安装 Pillow 库")
    print("请运行: pip install Pillow 或 pip3 install Pillow")
    sys.exit(1)

# 源图片路径
source_image = '/data/project/ai_project/yy_运营/xhs_小红书运营/z-images/output/generated_20251207_224402_177423.png'

# 确保 assets 目录存在
assets_dir = 'src/assets'
os.makedirs(assets_dir, exist_ok=True)

# 检查源图片是否存在
if not os.path.exists(source_image):
    print(f"警告: 源图片不存在: {source_image}")
    print("正在查找替代图片...")
    # 尝试查找其他图片
    alt_paths = [
        '/data/project/ai_project/yy_运营/xhs_小红书运营/z-images/output/generated_20251207_233431_493955.png',
        '/data/project/ai_project/yy_运营/xhs_小红书运营/z-images/output/generated_20251207_232457_071968.png',
    ]
    source_image = None
    for path in alt_paths:
        if os.path.exists(path):
            source_image = path
            print(f"使用替代图片: {path}")
            break
    
    if not source_image:
        print("错误: 找不到任何可用的图片文件")
        print("请确保图片文件存在，或手动创建图标文件")
        sys.exit(1)

try:
    # 打开源图片
    print(f"正在处理图片: {source_image}")
    img = Image.open(source_image)
    print(f"✓ 成功打开源图片")
    print(f"  原始尺寸: {img.size[0]}x{img.size[1]}")
    
    # 如果是 RGBA，转换为 RGB（避免透明度问题）
    if img.mode == 'RGBA':
        # 创建白色背景
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # 使用 alpha 通道作为 mask
        img = background
    
    # 创建不同尺寸的图标
    for size in [16, 48, 128]:
        # 调整大小并保持宽高比
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        output_path = os.path.join(assets_dir, f'icon-{size}.png')
        resized.save(output_path, 'PNG')
        print(f'✓ 已创建 {output_path} ({size}x{size})')
    
    print('\n所有图标创建完成！')
    
except Exception as e:
    import traceback
    print(f"错误: {e}")
    traceback.print_exc()
    sys.exit(1)
