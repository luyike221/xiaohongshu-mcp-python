"""根据简介生成小红书内容工具

基于 test_content_publish.py 的工作流，封装为 LangChain tool
"""

import asyncio
from typing import Any, Optional

from langchain_core.tools import tool

from ...mcp.xhs import (
    create_xhs_content_generator_service,
    create_image_video_mcp_service,
    create_xiaohongshu_browser_mcp_service,
)
from ..logging import get_logger

logger = get_logger(__name__)

# 全局服务实例（懒加载）
_content_service: Optional[Any] = None
_image_service: Optional[Any] = None
_publish_service: Optional[Any] = None


async def _get_services():
    """获取或初始化服务实例（懒加载）"""
    global _content_service, _image_service, _publish_service
    
    if _content_service is None:
        _content_service = await create_xhs_content_generator_service()
        logger.info("Content service initialized")
    
    if _image_service is None:
        _image_service = await create_image_video_mcp_service()
        logger.info("Image service initialized")
    
    if _publish_service is None:
        _publish_service = await create_xiaohongshu_browser_mcp_service()
        logger.info("Publish service initialized")
    
    return _content_service, _image_service, _publish_service


async def _generate_content_workflow(
    description: str,
    image_count: int = 3,
    publish: bool = True,
) -> dict:
    """根据简介生成内容的完整工作流
    
    Args:
        description: 内容简介/描述
        image_count: 需要生成的图片数量，默认3张
        publish: 是否发布到小红书，默认True
    
    Returns:
        包含生成结果的字典
    """
    try:
        # 获取服务
        content_service, image_service, publish_service = await _get_services()
        
        # 步骤1: 生成内容大纲
        logger.info("Generating content outline", description=description[:50])
        content_result = await content_service.generate_outline(
            topic=description,
            provider_type="alibaba_bailian",
            temperature=0.7,
        )
        
        if not content_result.get('success'):
            return {
                "success": False,
                "error": f"内容生成失败: {content_result.get('error', 'Unknown error')}",
            }
        
        # 提取标题、内容和标签
        title = content_result.get('title', '') or description[:20]
        content = content_result.get('content', '') or content_result.get('outline', '')
        tags = content_result.get('tags', [])
        pages = content_result.get('pages', [])
        
        # 步骤2: 生成图片
        logger.info("Generating images", count=image_count)
        image_urls = []
        
        if pages:
            # 使用批量生成
            image_result = await image_service.generate_images_batch(
                pages=pages[:image_count],
                full_outline=content_result.get('outline', ''),
                user_topic=description,
                max_wait_time=600,
            )
            if image_result.get('success'):
                image_urls = [img.get('url') for img in image_result.get('images', []) if img.get('url')]
        else:
            # 如果没有 pages，构造 pages 使用批量生成接口
            constructed_pages = [
                {
                    "index": i,
                    "type": "content",
                    "content": f"{description} - 图片{i+1}"
                }
                for i in range(image_count)
            ]
            image_result = await image_service.generate_images_batch(
                pages=constructed_pages,
                full_outline=content_result.get('outline', '') or description,
                user_topic=description,
                max_wait_time=600,
            )
            if image_result.get('success'):
                image_urls = [img.get('url') for img in image_result.get('images', []) if img.get('url')]
        
        result = {
            "success": True,
            "content": {
                "title": title,
                "content": content[:1200] if len(content) > 1200 else content,  # 限制内容长度
                "tags": tags,
            },
            "images": image_urls,
            "publish": None,
        }
        
        # 步骤3: 发布到小红书（如果需要）
        if publish and image_urls:
            logger.info("Publishing to Xiaohongshu")
            publish_result = await publish_service.publish_content(
                title=title,
                content=result["content"]["content"],
                images=image_urls,
                tags=tags,
            )
            result["publish"] = publish_result
            result["success"] = publish_result.get("success", False)
            # 如果发布失败，传递错误信息
            if not result["success"]:
                # 优先使用 error 字段，其次使用 message 字段
                error_msg = publish_result.get("error") or publish_result.get("message") or "发布失败，原因未知"
                result["error"] = error_msg
                logger.error("Publish failed", error=error_msg, publish_result=publish_result)
        elif publish and not image_urls:
            result["success"] = False
            result["error"] = "没有可用的图片，无法发布"
        
        return result
        
    except Exception as e:
        logger.error("Content generation workflow failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "error": f"工作流执行失败: {str(e)}",
        }


@tool
def generate_content_from_description(
    description: str,
    image_count: int = 3,
    publish: bool = True,
) -> str:
    """根据简介生成小红书内容
    
    这个工具可以根据用户提供的简介，自动生成小红书内容（包括标题、正文、标签），
    生成相应的配图，并可选择是否发布到小红书平台。
    
    Args:
        description: 内容简介/描述，例如："我想发布一篇关于家常菜制作的图文笔记，主题是红烧肉的做法"
        image_count: 需要生成的图片数量，默认为3张
        publish: 是否发布到小红书平台，默认为True
    
    Returns:
        JSON格式的字符串，包含：
        - success: 是否成功
        - content: 生成的内容（title, content, tags）
        - images: 生成的图片URL列表
        - publish: 发布结果（如果publish=True）
        - error: 错误信息（如果失败）
    
    Example:
        result = generate_content_from_description(
            description="分享一道简单易做的家常菜",
            image_count=3,
            publish=True
        )
    """
    import json
    
    # 由于 tool 装饰器不支持 async，我们需要在同步函数中运行异步代码
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        _generate_content_workflow(
            description=description,
            image_count=image_count,
            publish=publish,
        )
    )
    
    return json.dumps(result, ensure_ascii=False, indent=2)

