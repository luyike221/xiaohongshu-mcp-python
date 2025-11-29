"""
图像和视频生成 MCP 服务主入口
"""

import asyncio
from typing import Optional
from fastmcp import FastMCP
from loguru import logger

from .clients import WanT2IClient, GoogleGenAIClient
from .config import settings
from .prompts import register_prompts
from .resources import register_resources, register_resource_templates
from .services import ImageGenerationService

# 创建 MCP 应用实例
mcp = FastMCP("Image Video MCP")

# 注册所有 Resource 资源（必须先注册，因为 Template 会使用它们）
register_resources(mcp)

# 注册所有 Resource Template 模板
register_resource_templates(mcp)

# 注册所有 Prompt 模板
register_prompts(mcp)


@mcp.tool()
async def generate_image(
    prompt: str,
    negative_prompt: Optional[str] = None,
    width: int = 1280,
    height: int = 1280,
    seed: Optional[int] = None,
    max_wait_time: int = 600,
) -> dict:
    """
    生成图像（默认使用通义万相 WanT2I）
    
    这是默认的图片生成工具，使用通义万相 T2I 模型生成图像。
    如需使用 Google GenAI，请使用 generate_image_with_google_genai 工具。
    
    Args:
        prompt: 图像生成提示词
        negative_prompt: 负面提示词（可选）
        width: 图像宽度，默认 1280
        height: 图像高度，默认 1280
        seed: 随机种子（可选）
        max_wait_time: 最大等待时间（秒），默认 600 秒（10分钟）
    
    Returns:
        包含生成结果的字典，result 字段包含图片 URL 列表
    """
    try:
        size = f"{width}*{height}"
        async with WanT2IClient() as client:
            # 步骤1：创建任务
            result = await client.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                size=size,
                seed=seed,
            )
            
            output = result.get('output', {})
            task_id = output.get('task_id')
            task_status = output.get('task_status', 'PENDING')
            
            if not task_id:
                raise ValueError("未能获取任务 ID")
            
            logger.info(f"任务创建成功: task_id={task_id}, status={task_status}")
            
            # 步骤2：轮询获取结果
            if task_status in ['PENDING', 'RUNNING']:
                max_polls = max_wait_time // 10  # 每10秒查询一次
                poll_count = 0
                
                while poll_count < max_polls:
                    await asyncio.sleep(10)  # 等待10秒
                    poll_count += 1
                    
                    try:
                        status_result = await client.get_task_status(task_id)
                        status_output = status_result.get('output', {})
                        current_status = status_output.get('task_status', 'UNKNOWN')
                        
                        logger.debug(f"轮询 [{poll_count}/{max_polls}]: status={current_status}")
                        
                        if current_status == 'SUCCEEDED':
                            # 提取所有图片 URL
                            results = status_output.get('results', [])
                            urls = [img.get('url') for img in results if img.get('url')]
                            
                            logger.info(f"图像生成成功: 共 {len(urls)} 张图片")
                            return {
                                "success": True,
                                "result": urls,  # 只返回 URL 列表
                                "message": f"成功生成 {len(urls)} 张图片",
                            }
                        elif current_status == 'FAILED':
                            error_msg = status_output.get('message', '任务执行失败')
                            logger.error(f"任务失败: {error_msg}")
                            return {
                                "success": False,
                                "error": error_msg,
                                "message": "图像生成失败",
                            }
                        elif current_status in ['PENDING', 'RUNNING']:
                            continue
                        else:
                            logger.warning(f"未知任务状态: {current_status}")
                            break
                    except Exception as e:
                        logger.warning(f"查询任务状态时出错: {e}")
                        if poll_count < max_polls:
                            continue
                        raise
                
                # 轮询超时
                logger.warning(f"轮询超时: task_id={task_id}")
                return {
                    "success": False,
                    "error": f"任务处理超时（已等待 {max_wait_time} 秒）",
                    "message": "请稍后使用 task_id 手动查询结果",
                    "task_id": task_id,
                }
            elif task_status == 'SUCCEEDED':
                # 如果创建时就已经成功（不太可能，但处理一下）
                results = output.get('results', [])
                urls = [img.get('url') for img in results if img.get('url')]
                return {
                    "success": True,
                    "result": urls,
                    "message": f"成功生成 {len(urls)} 张图片",
                }
            else:
                error_msg = output.get('message', f'任务状态异常: {task_status}')
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "图像生成失败",
                }
                
    except Exception as e:
        logger.error(f"图像生成失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "图像生成失败",
        }


@mcp.tool()
async def generate_image_with_google_genai(
    prompt: str,
    aspect_ratio: str = "3:4",
    temperature: float = 1.0,
    model: str = "gemini-3-pro-image-preview",
    reference_image_base64: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict:
    """
    使用 Google GenAI (Gemini) 生成图像（可选工具）
    
    这是可选的图片生成工具，使用 Google GenAI (Gemini) 模型生成图像。
    默认的图片生成工具是 generate_image（使用通义万相 WanT2I）。
    
    特点：
    - 支持参考图片，可保持风格一致
    - 支持多种宽高比
    - 返回 base64 编码的图片数据
    
    Args:
        prompt: 图像生成提示词
        aspect_ratio: 宽高比，支持 "1:1", "3:4", "4:3", "16:9", "9:16"，默认 "3:4"
        temperature: 温度参数，控制生成随机性，范围 0.0-2.0，默认 1.0
        model: 模型名称，默认 "gemini-3-pro-image-preview"
        reference_image_base64: 参考图片（base64 编码），用于保持风格一致（可选）
        api_key: Google GenAI API Key（可选，如果不提供则从配置读取）
        base_url: 自定义 API 端点（可选）
    
    Returns:
        包含生成结果的字典，result 字段包含图片的 base64 编码数据
    """
    try:
        import base64
        
        # 获取配置
        if api_key:
            config = {
                "api_key": api_key,
                "base_url": base_url,
                "model": model,
                "temperature": temperature,
                "default_aspect_ratio": aspect_ratio,
            }
        else:
            genai_config = settings.get_google_genai_config()
            config = {
                "api_key": genai_config.api_key,
                "base_url": base_url or genai_config.base_url,
                "model": model or genai_config.model,
                "temperature": temperature if temperature != 1.0 else genai_config.temperature,
                "default_aspect_ratio": aspect_ratio if aspect_ratio != "3:4" else genai_config.default_aspect_ratio,
            }
        
        # 解析参考图片
        reference_image = None
        if reference_image_base64:
            # 移除可能的 data URL 前缀
            if ',' in reference_image_base64:
                reference_image_base64 = reference_image_base64.split(',')[1]
            reference_image = base64.b64decode(reference_image_base64)
        
        # 创建客户端并生成图片
        client = GoogleGenAIClient(**config)
        image_data = await client.generate_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            temperature=config["temperature"],
            model=config["model"],
            reference_image=reference_image,
        )
        
        # 将图片数据编码为 base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        logger.info(f"Google GenAI 图像生成成功: {len(image_data)} bytes")
        return {
            "success": True,
            "result": image_base64,
            "format": "base64",
            "message": "图像生成成功",
            "size_bytes": len(image_data),
        }
        
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "配置错误，请检查 API Key 设置",
        }
    except Exception as e:
        logger.error(f"Google GenAI 图像生成失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "图像生成失败",
        }


@mcp.tool()
async def generate_images_batch(
    pages: list,
    full_outline: str = "",
    user_topic: str = "",
    user_images_base64: Optional[list] = None,
    max_wait_time: int = 600,
) -> dict:
    """
    批量生成小红书风格的图片
    
    根据页面列表批量生成小红书风格的图文内容图片。使用小红书风格的 prompt 模板，
    先生成封面页，然后使用封面作为参考生成其他页面，确保所有页面风格统一。
    
    生成流程：
    1. 先生成封面页（如果存在）
    2. 使用封面作为参考，生成其他内容页
    3. 直接返回图片 URL，不保存到本地
    
    Args:
        pages: 页面列表，必需参数。每个页面是一个字典，包含以下字段：
            - index (int): 页面索引，从 0 开始，必须唯一且连续
            - type (str): 页面类型，可选值：
                * "cover" - 封面页，通常包含标题和主要视觉元素
                * "content" - 内容页，包含具体的信息和说明
                * "summary" - 总结页，包含总结性内容
            - content (str): 页面内容文本，这是生成图片的主要依据
              示例: "如何在家做拿铁\n1. 准备咖啡豆\n2. 磨豆\n3. 冲泡"
        
        full_outline: 完整的内容大纲文本，可选参数，默认为空字符串。
            用于保持所有页面风格一致。建议传入完整的大纲内容，
            这样生成的图片在配色、设计风格、视觉元素上会更加统一。
            示例: "1. 封面：如何在家做拿铁\n2. 准备材料\n3. 制作步骤\n4. 注意事项"
        
        user_topic: 用户的原始需求或主题，可选参数，默认为空字符串。
            用于保持生成图片的意图一致。建议传入用户最初提出的主题或需求，
            这样生成的图片能更好地符合用户的预期。
            示例: "咖啡制作教程" 或 "秋季显白美甲"
        
        user_images_base64: 用户上传的参考图片列表，可选参数，默认为 None。
            注意：当前实现使用通义万相 WanT2I，不支持参考图片功能，此参数暂未使用。
            格式: ["data:image/png;base64,iVBORw0KG...", ...] 或 ["iVBORw0KG...", ...]
        
        max_wait_time: 最大等待时间（秒），可选参数，默认 600 秒（10分钟）。
            仅在使用通义万相 WanT2I 时有效。由于 WanT2I 是异步任务，
            需要轮询任务状态，此参数控制最大等待时间。
    
    Returns:
        包含生成结果的字典：
        - success (bool): 是否全部成功生成
        - task_id (str): 自动生成的任务ID，用于标识本次生成任务
        - total (int): 总页面数
        - completed (int): 成功生成的页面数
        - failed (int): 失败的页面数
        - images (list): 成功生成的图片列表，每个元素包含：
            * index (int): 页面索引
            * url (str): 图片的 URL 地址，可直接用于访问和下载
            * type (str): 页面类型（"cover"、"content" 或 "summary"）
        - failed_pages (list): 失败的页面列表，每个元素包含：
            * index (int): 页面索引
            * error (str): 错误信息
    
    Example:
        ```python
        result = await generate_images_batch(
            pages=[
                {"index": 0, "type": "cover", "content": "如何在家做拿铁"},
                {"index": 1, "type": "content", "content": "1. 准备咖啡豆\n2. 磨豆"},
                {"index": 2, "type": "content", "content": "3. 冲泡\n4. 拉花"},
            ],
            full_outline="完整的咖啡制作教程大纲",
            user_topic="咖啡制作教程"
        )
        ```
    """
    try:
        import base64

        # 解析用户上传的参考图片
        user_images = None
        if user_images_base64:
            user_images = []
            for img_b64 in user_images_base64:
                # 移除可能的 data URL 前缀
                if ',' in img_b64:
                    img_b64 = img_b64.split(',')[1]
                user_images.append(base64.b64decode(img_b64))

        # 创建图片生成服务
        service = ImageGenerationService()

        # 批量生成图片（默认使用 WanT2I）
        result = await service.generate_images(
            pages=pages,
            full_outline=full_outline,
            user_topic=user_topic,
            user_images=user_images,
            max_wait_time=max_wait_time,
        )

        logger.info(f"批量图片生成完成: task_id={result['task_id']}, 成功={result['completed']}, 失败={result['failed']}")
        return result

    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "参数错误"
        }
    except Exception as e:
        logger.error(f"批量图片生成失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "批量图片生成失败"
        }


@mcp.tool()
def generate_video(prompt: str, duration: int = 5) -> str:
    """
    生成视频
    
    Args:
        prompt: 视频生成提示词
        duration: 视频时长（秒），默认 5 秒
    
    Returns:
        生成的视频路径或 URL
    """
    # TODO: 实现视频生成逻辑
    return f"Generated video for prompt: {prompt} ({duration}s)"


def main():
    """启动 MCP 服务器"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(
        description="图像和视频生成 MCP 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8003")),
        help="MCP 服务器端口 (默认: 8003)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("MCP_HOST", "127.0.0.1"),
        help="MCP 服务器主机 (默认: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("图像和视频生成 MCP 服务启动")
    logger.info(f"服务器地址: http://{args.host}:{args.port}")
    logger.info("=" * 60)
    
    # 启动 FastMCP HTTP 服务器
    mcp.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
