"""
浏览器控制模块

提供基于 Playwright 的浏览器自动化功能，包括：
- 浏览器实例管理
- Cookie 持久化
- 页面操作封装
"""

from .browser_manager import BrowserManager
from .page_controller import PageController

__all__ = ["BrowserManager", "PageController"]