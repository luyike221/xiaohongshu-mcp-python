import torch
from modelscope import ZImagePipeline
import gc
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import io
import os
from datetime import datetime
from contextlib import asynccontextmanager

# 使用本地模型路径
MODEL_PATH = "/data/mxpt/models/Tongyi-MAI/Z-Image-Turbo"

# 输出目录
OUTPUT_DIR = "output"

# 全局变量存储模型管道
pipe = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时加载模型，关闭时清理"""
    global pipe
    
    # 启动时加载模型
    print("🔄 开始加载模型（内存优化模式）...")
    print("💾 使用 CPU offloading 和低内存模式")
    
    # 清理内存
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # 加载本地模型 - 内存优化配置
    try:
        pipe = ZImagePipeline.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        )
        print("✅ 使用 bfloat16 精度")
    except Exception as e:
        print(f"⚠️ bfloat16 加载失败，尝试 float16: {e}")
        pipe = ZImagePipeline.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
        )
        print("✅ 使用 float16 精度")
    
    # 启用 CPU offloading
    print("🔄 启用 CPU offloading...")
    pipe.enable_model_cpu_offload()
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 输出目录已创建: {OUTPUT_DIR}")
    
    print("✅ 模型加载完成！")
    
    yield
    
    # 关闭时清理
    print("🔄 清理模型资源...")
    del pipe
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("✅ 资源清理完成")


app = FastAPI(lifespan=lifespan)


def adjust_to_multiple_of_16(value: int) -> int:
    """将数值调整为16的倍数（向下取整）"""
    return (value // 16) * 16


class GenerateRequest(BaseModel):
    """图像生成请求模型"""
    prompt: str
    height: Optional[int] = 1024
    width: Optional[int] = 1024
    num_inference_steps: Optional[int] = 9
    guidance_scale: Optional[float] = 0.0
    seed: Optional[int] = None


@app.post("/generate")
async def generate_image(request: GenerateRequest):
    """
    生成图像接口
    
    - **prompt**: 图像描述提示词（必需）
    - **height**: 图像高度，默认 1024
    - **width**: 图像宽度，默认 1024
    - **num_inference_steps**: 推理步数，默认 9
    - **guidance_scale**: 引导强度，默认 0.0（Turbo 模型应为 0）
    - **seed**: 随机种子，默认 None（随机）
    """
    global pipe
    
    if pipe is None:
        return {"error": "模型未加载"}
    
    try:
        # 调整高度和宽度为16的倍数（模型要求）
        adjusted_height = adjust_to_multiple_of_16(request.height)
        adjusted_width = adjust_to_multiple_of_16(request.width)
        
        if adjusted_height != request.height or adjusted_width != request.width:
            print(f"⚠️ 尺寸已自动调整: {request.height}x{request.width} -> {adjusted_height}x{adjusted_width} (必须是16的倍数)")
        
        # 设置随机种子
        if request.seed is not None:
            generator = torch.Generator("cuda" if torch.cuda.is_available() else "cpu").manual_seed(request.seed)
        else:
            generator = None
        
        # 生成图像
        print(f"🎨 开始生成图像: {request.prompt[:50]}...")
        result = pipe(
            prompt=request.prompt,
            height=adjusted_height,
            width=adjusted_width,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            generator=generator,
        )
        
        image = result.images[0]
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"generated_{timestamp}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # 保存图像到 output 目录
        image.save(filepath, format='PNG')
        print(f"💾 图像已保存到: {filepath}")
        
        # 将图像转换为字节流用于返回
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        print("✅ 图像生成完成")
        
        return StreamingResponse(
            img_byte_arr,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        print(f"❌ 生成图像时出错: {e}")
        return {"error": str(e)}
