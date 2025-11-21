"""
小红书 MCP 服务的 Python 实现

提供小红书内容发布、搜索、用户管理等功能的 MCP 服务。
"""

__version__ = "0.1.0"
__author__ = "xiaohongshu-mcp-python"
__description__ = "小红书 MCP 服务的 Python 实现，提供小红书内容发布、搜索、用户管理等功能"

# 向后兼容性导入
from .main import main, cli_main
from .server import app, mcp, AppServer
from .services import XiaohongshuService
from .managers.user_session_manager import get_user_session_manager

# 为了向后兼容，将 MCP 工具函数导出
# 注意：这些函数实际上在 server.mcp_tools 中定义
from .server.mcp_tools import (
    xiaohongshu_start_login_session,
    xiaohongshu_check_login_session,
    xiaohongshu_cleanup_login_session,
    xiaohongshu_publish_content,
    xiaohongshu_publish_video,
    xiaohongshu_search_feeds,
    xiaohongshu_get_feeds,
    xiaohongshu_list_feeds,
    xiaohongshu_get_user_profile,
    xiaohongshu_get_feed_detail,
)

# 向后兼容的别名
xiaohongshu_publish_image = xiaohongshu_publish_content
xiaohongshu_search = xiaohongshu_search_feeds

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "main",
    "cli_main",
    "app",
    "mcp",
    "AppServer",
    "XiaohongshuService",
    "get_user_session_manager",
    "xiaohongshu_start_login_session",
    "xiaohongshu_check_login_session",
    "xiaohongshu_cleanup_login_session",
    "xiaohongshu_publish_content",
    "xiaohongshu_publish_video",
    "xiaohongshu_publish_image",  # 别名
    "xiaohongshu_search_feeds",
    "xiaohongshu_search",  # 别名
    "xiaohongshu_get_feeds",
    "xiaohongshu_list_feeds",
    "xiaohongshu_get_user_profile",
    "xiaohongshu_get_feed_detail",
]