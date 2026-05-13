#!/usr/bin/env python3
"""
Z-Image 图片生成测试脚本

通过 API 调用生成图片，传入提示词即可
"""

import requests
import os
from datetime import datetime
from pathlib import Path
from PIL import Image
import io


# API 地址
API_URL = "http://localhost:8000/generate"

# 输出目录
OUTPUT_DIR = "output"


def generate_image(
    prompt: str,
    height: int = 1024,
    width: int = 1024,
    num_inference_steps: int = 9,
    guidance_scale: float = 0.0,
    seed: int = None,
    api_url: str = API_URL,
    output_dir: str = OUTPUT_DIR,
) -> str:
    """
    根据提示词生成图片（通过 API 调用）
    
    Args:
        prompt: 图片生成提示词（必需）
        height: 图片高度，默认 1024
        width: 图片宽度，默认 1024
        num_inference_steps: 推理步数，默认 9
        guidance_scale: 引导强度，默认 0.0（Turbo 模型应为 0）
        seed: 随机种子，默认 None（随机）
        api_url: API 地址，默认 "http://localhost:8000/generate"
        output_dir: 输出目录，默认 "output"
    
    Returns:
        生成的图片文件路径
    """
    print(f"🎨 开始生成图片...")
    print(f"📝 提示词: {prompt[:100]}...")
    print(f"🌐 API 地址: {api_url}")
    
    # 构建请求数据
    request_data = {
        "prompt": prompt,
        "height": height,
        "width": width,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
    }
    
    if seed is not None:
        request_data["seed"] = seed
        print(f"🎲 使用随机种子: {seed}")
    
    # 调用 API
    print("🔄 调用 API 生成图片...")
    try:
        response = requests.post(api_url, json=request_data, timeout=300)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"无法连接到 API 服务器: {api_url}\n"
            f"请确保 Z-Image 服务已启动（运行 start.sh 或 uvicorn app:app --host 0.0.0.0 --port 8000）"
        )
    except requests.exceptions.HTTPError as e:
        error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        raise Exception(f"API 请求失败: {e}\n错误详情: {error_detail}")
    
    # 检查响应
    if response.headers.get('content-type', '').startswith('application/json'):
        # JSON 错误响应
        error_data = response.json()
        raise Exception(f"生成失败: {error_data.get('error', '未知错误')}")
    
    # 保存图片
    image_data = response.content
    image = Image.open(io.BytesIO(image_data))
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"generated_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    
    # 保存图片
    image.save(filepath, format='PNG')
    print(f"✅ 图片已保存到: {filepath}")
    
    return filepath


if __name__ == "__main__":
    # 直接在这里修改提示词进行测试
    prompt = """
**“一位邻家女孩，具有温柔清新气质，出现在阳光洒进的卧室中，正在开直播卖货。
她拥有柔和鹅蛋脸、大而自然的杏仁眼、双眼皮不夸张、自然眉形、柔和直鼻、淡色自然唇形，中长柔顺发搭配空气刘海；五官比例统一（consistent facial identity）。
皮肤清透、淡妆、微红脸颊，呈现温暖日常氛围。
光影采用 natural soft light，质感为 ultra detailed、premium quality。”**

    """ 
    
    # 可选：修改尺寸
    # height = 1024
    # width = 1024
    
    try:
        filepath = generate_image(prompt)
        print(f"\n🎉 生成成功！")
        print(f"📁 文件路径: {os.path.abspath(filepath)}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()

