"""
浏览器控制模块：浏览器实例管理、持久化 User Data、页面操作封装。
"""

from .browser_manager import BrowserManager
from .page_controller import PageController

__all__ = ["BrowserManager", "PageController"]