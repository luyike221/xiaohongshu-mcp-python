"""
浏览器管理器

负责 Playwright 浏览器实例的创建、配置和生命周期管理。
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger

from ..storage.cookie_storage import CookieStorage


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        user_data_dir: Optional[Path] = None,
        cookie_storage: Optional[CookieStorage] = None
    ):
        """
        初始化浏览器管理器
        
        Args:
            headless: 是否无头模式
            browser_type: 浏览器类型 (chromium, firefox, webkit)
            user_data_dir: 用户数据目录
            cookie_storage: Cookie 存储实例
        """
        self.headless = headless
        self.browser_type = browser_type
        self.user_data_dir = user_data_dir
        self.cookie_storage = cookie_storage or CookieStorage()
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
    
    def is_started(self) -> bool:
        """检查浏览器是否已启动"""
        return self._playwright is not None and self._browser is not None
    
    async def start(self) -> None:
        """启动浏览器"""
        if self._playwright is not None:
            logger.warning("浏览器已经启动")
            return
        
        logger.info(f"启动浏览器 (headless={self.headless}, type={self.browser_type})")
        
        self._playwright = await async_playwright().start()
        
        # 获取浏览器类型
        browser_launcher = getattr(self._playwright, self.browser_type)
        
        # 浏览器启动参数
        launch_options = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        }
        
        # 如果指定了用户数据目录
        if self.user_data_dir:
            launch_options["user_data_dir"] = str(self.user_data_dir)
        
        self._browser = await browser_launcher.launch(**launch_options)
        
        # 创建浏览器上下文
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        
        self._context = await self._browser.new_context(**context_options)
        
        # 加载 cookies
        await self._load_cookies()
        
        # 创建页面
        self._page = await self._context.new_page()
        
        logger.info("浏览器启动成功")
    
    async def stop(self) -> None:
        """停止浏览器"""
        if self._playwright is None:
            return
        
        logger.info("停止浏览器")
        
        # 保存 cookies
        await self._save_cookies()
        
        if self._page:
            await self._page.close()
            self._page = None
        
        if self._context:
            await self._context.close()
            self._context = None
        
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("浏览器已停止")
    
    async def get_page(self) -> Page:
        """获取页面实例"""
        if self._page is None:
            await self.start()
        return self._page
    
    async def new_page(self) -> Page:
        """创建新页面"""
        if self._context is None:
            await self.start()
        return await self._context.new_page()
    
    async def load_cookies(self) -> None:
        """加载 cookies（公共方法）"""
        await self._load_cookies()
    
    async def save_cookies(self) -> bool:
        """保存 cookies（公共方法）"""
        return await self._save_cookies()
    
    async def _save_cookies(self) -> bool:
        """保存 cookies"""
        if self._context is None:
            return False
        
        try:
            cookies = await self._context.cookies()
            ok = await self.cookie_storage.save_cookies(cookies)
            logger.info(f"保存了 {len(cookies)} 个 cookies")
            return ok
        except Exception as e:
            logger.error(f"保存 cookies 失败: {e}")
            return False
    
    async def _load_cookies(self) -> None:
        """加载 cookies"""
        if self._context is None:
            return
        
        try:
            cookies = await self.cookie_storage.load_cookies()
            if cookies:
                await self._context.add_cookies(cookies)
                logger.info(f"加载了 {len(cookies)} 个 cookies")
        except Exception as e:
            logger.warning(f"加载 cookies 失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()