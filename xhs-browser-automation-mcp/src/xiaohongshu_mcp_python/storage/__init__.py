"""
存储模块

提供数据持久化功能，包括：
- Cookie 存储和加载
- 配置文件管理
- 临时文件处理
"""

from .cookie_storage import CookieStorage

__all__ = ["CookieStorage"]