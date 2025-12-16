"""小红书内容生成工作流

包含完整的内容生成、图片生成和发布流程
"""

from typing import Any, Optional

from ..mcp.xhs import (
    create_xhs_content_generator_service,
    create_image_video_mcp_service,
    create_xiaohongshu_browser_mcp_service,
)
from ..tools.logging import get_logger

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


async def generate_xhs_content_workflow(
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
        包含生成结果的字典：
        - success: 是否成功
        - content: 生成的内容（title, content, tags）
        - images: 生成的图片URL列表
        - publish: 发布结果（如果publish=True）
        - error: 错误信息（如果失败）
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
            # 单个生成
            for i in range(image_count):
                image_result = await image_service.generate_image(
                    prompt=f"{description} - 图片{i+1}",
                )
                if image_result.get('success') and image_result.get('url'):
                    image_urls.append(image_result['url'])
        
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

