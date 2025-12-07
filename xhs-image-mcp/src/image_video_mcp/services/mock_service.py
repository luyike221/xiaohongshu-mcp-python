"""
Mock 图片生成服务

用于测试和开发环境，直接返回固定的图片文件。
"""

import uuid
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any


def generate_mock_images(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Mock 模式：生成模拟图片结果
    
    直接返回固定的图片文件，用于测试和开发环境。
    
    Args:
        pages: 页面列表，每个页面是一个字典，包含 index 和 type 字段
    
    Returns:
        包含生成结果的字典，格式与正常模式一致：
        - success (bool): 是否成功
        - task_id (str): 任务ID
        - total (int): 总页面数
        - completed (int): 成功生成的页面数
        - failed (int): 失败的页面数
        - images (list): 生成的图片列表
        - failed_pages (list): 失败的页面列表
    """
    logger.info(f"[MOCK模式] 使用 mock 数据，返回固定图片文件")
    mock_image_path = Path("/root/project/ai_project/yx_运营/xhs_小红书运营/docs/image.png")
    
    if not mock_image_path.exists():
        logger.error(f"[MOCK模式] Mock 图片文件不存在: {mock_image_path}")
        return {
            "success": False,
            "error": f"Mock 图片文件不存在: {mock_image_path}",
            "message": "Mock 模式失败"
        }
    
    # 生成任务ID
    task_id = f"mock_{uuid.uuid4().hex[:8]}"
    
    # 为每个页面生成 mock 结果
    generated_images = []
    for page in pages:
        page_index = page.get("index", 0)
        page_type = page.get("type", "content")
        
        # 直接返回绝对路径（Linux 下 file:// 格式无法被正确识别）
        image_url = str(mock_image_path.absolute())
        
        generated_images.append({
            "index": page_index,
            "url": image_url,
            "type": page_type
        })
    
    # 按index排序
    generated_images.sort(key=lambda x: x.get("index", 0))
    
    result = {
        "success": True,
        "task_id": task_id,
        "total": len(pages),
        "completed": len(generated_images),
        "failed": 0,
        "images": generated_images,
        "failed_pages": []
    }
    
    logger.info(f"[MOCK模式] 批量图片生成完成: task_id={task_id}, 成功={result['completed']}, 失败={result['failed']}")
    return result
