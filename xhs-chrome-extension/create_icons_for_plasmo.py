#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 Plasmo 创建图标文件
Plasmo 需要在根目录的 assets/ 目录中放置 icon.png 文件
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("正在安装 Pillow...")
    os.system("pip3 install Pillow --quiet")
    from PIL import Image, ImageDraw, ImageFont

def create_placeholder_icon():
    """创建一个简单的占位图标"""
    # 创建 512x512 的图标（Plasmo 推荐使用高分辨率）
    size = 512
    img = Image.new('RGB', (size, size), color='#ff2442')  # 小红书红色
    
    draw = ImageDraw.Draw(img)
    
    # 绘制一个白色的圆角矩形
    margin = 50
    draw.rounded_rectangle(
        [margin, margin, size-margin, size-margin],
        radius=30,
        fill='white'
    )
    
    # 尝试添加文字 "XHS"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except:
        try:
            font = ImageFont.load_default()
        except:
            font = None
    
    text = "XHS"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size - text_width) // 2, (size - text_height) // 2 - 20)
        draw.text(position, text, fill='#ff2442', font=font)
    
    return img

def copy_from_src_assets():
    """从 src/assets 复制现有图标"""
    src_icons = [
        'src/assets/icon-128.png',
        'src/assets/icon-48.png',
        'src/assets/icon-16.png'
    ]
    
    for icon_path in src_icons:
        if os.path.exists(icon_path):
            print(f"找到图标: {icon_path}")
            img = Image.open(icon_path)
            # 如果是小图标，放大到 512x512
            if img.size[0] < 512:
                print(f"  原始尺寸: {img.size}, 放大到 512x512")
                img = img.resize((512, 512), Image.Resampling.LANCZOS)
            return img
    
    return None

def main():
    print("🔧 为 Plasmo 创建图标...")
    
    # 创建 assets 目录（根目录）
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    print(f"✅ 创建目录: {assets_dir}")
    
    # 尝试从 src/assets 复制
    icon = copy_from_src_assets()
    
    # 如果没有找到，创建占位图标
    if icon is None:
        print("⚠️  未找到现有图标，创建占位图标...")
        icon = create_placeholder_icon()
    else:
        print("✅ 使用现有图标")
    
    # 保存为 icon.png
    output_path = assets_dir / 'icon.png'
    icon.save(output_path, 'PNG')
    print(f"✅ 图标已创建: {output_path}")
    print(f"   尺寸: {icon.size[0]}x{icon.size[1]}")
    print("")
    print("📋 现在可以运行: pnpm dev")

if __name__ == '__main__':
    main()
