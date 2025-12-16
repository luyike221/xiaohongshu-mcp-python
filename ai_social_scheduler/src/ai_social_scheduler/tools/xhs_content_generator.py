"""根据简介生成小红书内容工具

将工作流封装为 LangChain tool
"""

import asyncio
import json

from langchain_core.tools import tool

from ..workflows import generate_xhs_content_workflow


@tool
def generate_xhs_content_from_description(
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
        result = generate_xhs_content_from_description(
            description="分享一道简单易做的家常菜",
            image_count=3,
            publish=True
        )
    """
    # 由于 tool 装饰器不支持 async，我们需要在同步函数中运行异步代码
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        generate_xhs_content_workflow(
            description=description,
            image_count=image_count,
            publish=publish,
        )
    )
    
    return json.dumps(result, ensure_ascii=False, indent=2)

