"""
图像和视频生成 MCP 服务主入口
"""

from fastmcp import FastMCP
from loguru import logger

from .clients import WanT2IClient, GoogleGenAIClient, ZImageClient, DashScopeImageClient
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
    full_content: str,
    style: str = "",
    max_wait_time: int = 600,
) -> dict:
    """
    根据完整内容生成小红书风格的图片
    
    根据完整内容文本，使用 LLM 生成图片提示词，然后批量生成小红书风格的图文内容图片。
    使用小红书风格的 prompt 模板，确保生成的图片风格统一。
    
    生成流程：
    1. 使用 LLM 根据完整内容生成图片提示词（可能生成一张或多张图片的提示词）
    2. 根据生成的提示词批量生成图片
    3. 直接返回图片 URL，不保存到本地
    
    Args:
        full_content: 完整的内容文本，必需参数。
            这是生成图片的主要依据，可以是标题、正文、标签等完整内容。
            示例: "标题：如何在家做拿铁\n\n正文：分享几个实用技巧\n\n✅ 核心要点：\n- 准备咖啡豆\n- 磨豆\n- 冲泡\n\n💡 注意事项：\n选择适合的咖啡豆很重要"
        
        style: 图片风格，可选参数，默认为空字符串。
            用户可以指定图片风格，如"真实"、"动漫"、"哥特"、"简约"、"复古"等。
            风格可以是单个词语或描述性句子，例如：
            - "真实"：生成真实场景风格的图片
            - "性感"：生成性感风格的图片
            - "邻家"：生成邻家风格的图片
            - "萝莉"：生成萝莉风格的图片
            - "御姐"：生成御姐风格的图片
            - "女王"：生成女王风格的图片
            - "萝莉"：生成萝莉风格的图片
            - "萝莉"：生成萝莉风格的图片
            - "清新简约的日系风格"：生成清新简约的日系风格图片
            - "动漫风格"：生成动漫风格的图片
            - "哥特式暗黑风格"：生成哥特式暗黑风格的图片
            - "二次元风格"：生成二次元风格的图片
            - "水彩风格"：生成水彩风格的图片
            - "风景风格"：生成风景风格的图片
            - "清新简约的日系风格"：生成清新简约的日系风格图片
            如果不提供此参数或为空字符串，LLM 会根据内容自动选择最合适的风格。
        
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
        # 不指定风格，LLM 自动选择
        result = await generate_images_batch(
            full_content="标题：如何在家做拿铁\n\n正文：分享几个实用技巧\n\n✅ 核心要点：\n- 准备咖啡豆\n- 磨豆\n- 冲泡"
        )
        
        # 指定风格为"真实"
        result = await generate_images_batch(
            full_content="标题：如何在家做拿铁\n\n正文：分享几个实用技巧",
            style="真实"
        )
        
        # 指定风格为"动漫风格"
        result = await generate_images_batch(
            full_content="标题：如何在家做拿铁\n\n正文：分享几个实用技巧",
            style="动漫风格"
        )
        
        # 指定详细风格描述
        result = await generate_images_batch(
            full_content="标题：如何在家做拿铁\n\n正文：分享几个实用技巧",
            style="清新简约的日系风格，温暖色调"
        )
        ```
    """
    try:
        # 检查是否使用 Mock 模式
        if settings.use_mock:
            logger.info("[MOCK模式] 检测到 USE_MOCK=true，使用 Mock 模式生成图片")
            
            # Mock 模式：从 full_content 中提取页面信息，生成简单的 pages 列表
            # 简单实现：根据内容长度估算页面数量（每500字符一页，至少1页）
            content_length = len(full_content)
            estimated_pages = max(1, (content_length // 500) + 1)
            
            # 生成 pages 列表
            pages = []
            for i in range(estimated_pages):
                page_type = "cover" if i == 0 else "content"
                pages.append({
                    "index": i,
                    "type": page_type
                })
            
            logger.info(f"[MOCK模式] 生成 {len(pages)} 个页面的 Mock 数据")
            result = generate_mock_images(pages)
            logger.info(f"[MOCK模式] 批量图片生成完成: task_id={result['task_id']}, 成功={result['completed']}, 失败={result['failed']}")
            return result
        
        # 正常模式：调用实际的图片生成服务
        # 创建图片生成服务（自动初始化通义千问客户端用于生成图片提示词）
        service = ImageGenerationService(auto_init_qwen=True)

        # 批量生成图片（默认使用 z-image-turbo）
        # 会根据 full_content 生成图片提示词
        client = DashScopeImageClient(model="z-image-turbo")
        result = await service.generate_images_from_content(
            full_content=full_content,
            style=style,
            max_wait_time=max_wait_time,
            client=client,  # 使用 z-image-turbo 客户端
        )
        
        # 关闭客户端
        await client.close()

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
