"""
认证相关工具函数
负责用户登录状态检查等认证相关功能
"""

from typing import Dict, Any
from loguru import logger

from ..managers.user_session_manager import get_user_session_manager


async def check_user_login_status(username: str) -> Dict[str, Any]:
    """
    检查用户登录状态（统一处理函数，基于本地 cookies）
    
    Args:
        username: 用户名
    
    Returns:
        如果登录有效返回 {"valid": True, "status": ...}，否则返回错误信息字典
    """
    user_session_manager = get_user_session_manager()
    user_session_status = await user_session_manager.get_user_session_status(username)
    
    if not user_session_status:
        return {
            "valid": False,
            "success": False,
            "error": "用户未登录",
            "message": f"用户 {username} 未登录，请先使用 xiaohongshu_start_login_session 登录"
        }
    
    # 检查登录是否失效
    if user_session_status.get("status") == "expired" or user_session_status.get("error") == "LOGIN_EXPIRED":
        return {
            "valid": False,
            "success": False,
            "error": "登录已失效",
            "message": f"用户 {username} 的登录已失效，请重新登录"
        }
    
    # 检查登录状态
    if user_session_status.get("status") != "logged_in" or not user_session_status.get("logged_in", False):
        return {
            "valid": False,
            "success": False,
            "error": "用户未登录",
            "message": f"用户 {username} 未登录，请先使用 xiaohongshu_start_login_session 登录"
        }
    
    return {
        "valid": True,
        "status": user_session_status
    }

