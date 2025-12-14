"""
Mock 图片生成服务

用于测试和开发环境，直接返回固定的图片文件。
"""

import uuid
import os
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any

from ..config import settings


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
    
    # 获取 Mock 图片路径（从环境变量或使用默认值）
    if settings.mock_image_path:
        # 如果配置了路径，使用配置的路径
        mock_image_path = Path(settings.mock_image_path)
        # 如果是相对路径，尝试相对于项目根目录
        if not mock_image_path.is_absolute():
            # 获取项目根目录（向上查找包含 pyproject.toml 的目录）
            current_file = Path(__file__).resolve()
            project_root = None
            for parent in current_file.parents:
                if (parent / "pyproject.toml").exists():
                    project_root = parent
                    break
            if project_root:
                # 相对路径相对于项目根目录的父目录（xhs_小红书运营 目录）
                mock_image_path = project_root.parent / mock_image_path
    else:
        # 默认路径：尝试查找项目内的图片文件
        current_file = Path(__file__).resolve()
        # 向上查找项目根目录
        project_root = None
        for parent in current_file.parents:
            if (parent / "pyproject.toml").exists():
                project_root = parent
                break
        
        if project_root:
            # 尝试在项目根目录的父目录的 docs 目录下查找
            # project_root 是 xhs-image-mcp，parent 是 xhs_小红书运营 目录
            default_path = project_root.parent / "docs" / "image.png"
            if default_path.exists() and os.access(default_path, os.R_OK):
                mock_image_path = default_path
                logger.info(f"[MOCK模式] 找到默认图片文件: {mock_image_path}")
            else:
                # 如果找不到，使用项目内的资源
                mock_image_path = project_root / "data" / "image.png"
                logger.info(f"[MOCK模式] 使用项目内资源: {mock_image_path}")
        else:
            # 最后的 fallback
            mock_image_path = Path("/data/project/ai_project/yy_运营/xhs_小红书运营/docs/image.png")
    
    # 检查文件是否存在
    if not mock_image_path.exists():
        logger.error(f"[MOCK模式] Mock 图片文件不存在: {mock_image_path}")
        return {
            "success": False,
            "error": f"Mock 图片文件不存在: {mock_image_path}",
            "message": "Mock 模式失败：请检查 MOCK_IMAGE_PATH 配置或确保默认路径存在"
        }
    
    # 检查文件是否可读
    if not os.access(mock_image_path, os.R_OK):
        logger.error(f"[MOCK模式] Mock 图片文件无读取权限: {mock_image_path}")
        return {
            "success": False,
            "error": f"Mock 图片文件无读取权限: {mock_image_path}",
            "message": f"Mock 模式失败：文件权限不足，请检查文件权限（当前用户: {os.getenv('USER', 'unknown')}）"
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
