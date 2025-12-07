#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

# 添加错误处理
try:
    from PIL import Image
except ImportError:
    print("正在安装 Pillow...")
    os.system("pip3 install Pillow --quiet")
    from PIL import Image

source = '/data/project/ai_project/yy_运营/xhs_小红书运营/z-images/output/generated_20251207_224402_177423.png'
os.makedirs('src/assets', exist_ok=True)

if os.path.exists(source):
    img = Image.open(source)
    if img.mode == 'RGBA':
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg
    for s in [16, 48, 128]:
        img.resize((s, s), Image.Resampling.LANCZOS).save(f'src/assets/icon-{s}.png')
    print("图标创建成功")
else:
    print(f"文件不存在: {source}")
