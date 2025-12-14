"""
图像和视频生成 MCP 服务主入口
"""

from fastmcp import FastMCP
from loguru import logger

from .clients import WanT2IClient, GoogleGenAIClient, ZImageClient
from .config import settings
from .prompts import register_prompts
from .resources import register_resources, register_resource_templates
from .services import ImageGenerationService, generate_mock_images

# 创建 MCP 应用实例
mcp = FastMCP("Image Video MCP")

# 注册所有 Resource 资源（必须先注册，因为 Template 会使用它们）
register_resources(mcp)

# 注册所有 Resource Template 模板
register_resource_templates(mcp)

# 注册所有 Prompt 模板
register_prompts(mcp)


@mcp.tool()
async def generate_images_batch(
    pages: list,
    full_outline: str = "",
    user_topic: str = "",
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
        
        max_wait_time: 最大等待时间（秒），可选参数，默认 600 秒（10分钟）。
            Z-Image 为同步调用，此参数暂未使用。
    Returns:
        包含生成结果的字典：
        - success (bool): 是否全部成功生成
        - task_id (str): 自动生成的任务ID，用于标识本次生成任务
        - total (int): 总页面数
        - completed (int): 成功生成的页面数
        - failed (int): 失败的页面数
        - images (list): 成功生成的图片列表，每个元素包含：
            * index (int): 页面索引
            * url (str): 图片的文件路径（Z-Image 返回本地文件路径），可直接用于访问和下载
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
        # Mock 模式：直接返回固定的图片文件（通过环境变量 USE_MOCK 控制）
        if settings.use_mock:
            logger.info("使用 Mock 模式：直接返回固定的图片文件")
            return generate_mock_images(pages)

        # 正常模式：调用实际的图片生成服务
        # 创建图片生成服务（自动初始化通义千问客户端用于 LLM 预处理）
        service = ImageGenerationService(auto_init_qwen=True)

        # 批量生成图片（默认使用 Z-Image）
        result = await service.generate_images(
            pages=pages,
            full_outline=full_outline,
            user_topic=user_topic,
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
