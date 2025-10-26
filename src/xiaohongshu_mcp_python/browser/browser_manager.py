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
    
    def is_valid(self) -> bool:
        """检查浏览器是否仍然有效（未关闭）"""
        try:
            if not self.is_started():
                return False
            # 检查浏览器是否已关闭
            if self._browser and hasattr(self._browser, 'is_connected'):
                return self._browser.is_connected()
            # 检查页面是否有效
            if self._page and hasattr(self._page, 'is_closed'):
                return not self._page.is_closed()
            return True
        except Exception:
            return False
    
    async def ensure_started(self) -> None:
        """确保浏览器已启动且有效，如果无效则重启"""
        if not self.is_valid():
            logger.warning("浏览器无效或已关闭，正在重启...")
            await self.restart()
    
    async def restart(self, load_cookies: bool = True) -> None:
        """
        重启浏览器
        
        Args:
            load_cookies: 是否在重启后加载cookies，默认为True
        """
        logger.info("重启浏览器")
        await self.stop()
        
        # 临时保存原始的cookie_storage，以便在不加载cookies时使用空的存储
        original_cookie_storage = None
        if not load_cookies:
            original_cookie_storage = self.cookie_storage
            # 创建一个临时的空cookie存储
            from ..storage.cookie_storage import CookieStorage
            self.cookie_storage = CookieStorage(cookie_path="/tmp/empty_cookies.json")
        
        await self.start()
        
        # 恢复原始的cookie_storage
        if original_cookie_storage:
            self.cookie_storage = original_cookie_storage
        
        logger.info("浏览器重启完成")
    
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
        from ..config import BrowserConfig
        launch_options = {
            "headless": self.headless,
            "args": BrowserConfig.BROWSER_ARGS
        }
        
        # 如果指定了用户数据目录
        if self.user_data_dir:
            launch_options["user_data_dir"] = str(self.user_data_dir)
        
        self._browser = await browser_launcher.launch(**launch_options)
        
        # 创建浏览器上下文
        context_options = {
            "viewport": {"width": BrowserConfig.VIEWPORT_WIDTH, "height": BrowserConfig.VIEWPORT_HEIGHT},
            "user_agent": BrowserConfig.USER_AGENT
        }
        
        self._context = await self._browser.new_context(**context_options)
        
        # 加载 cookies
        await self._load_cookies()
        
        # 创建页面
        self._page = await self._context.new_page()
        
        logger.info("浏览器启动成功")
    
    async def stop(self, save_cookies: bool = True) -> None:
        """
        停止浏览器
        
        Args:
            save_cookies: 是否保存cookies，默认为True
        """
        if not self.is_started():
            return
        
        logger.info("停止浏览器")
        
        # 根据参数决定是否保存 cookies
        if save_cookies:
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
        await self.ensure_started()
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
    
    async def clear_all_data(self) -> bool:
        """
        清除浏览器的所有数据（cookies、缓存、本地存储等）
        
        Returns:
            是否清除成功
        """
        if not self.is_started():
            logger.warning("浏览器未启动，无法清除数据")
            return False
        
        try:
            # 清除浏览器上下文中的所有数据
            if self._context:
                # 清除 cookies
                await self._context.clear_cookies()
                
                # 清除本地存储和会话存储
                if self._page:
                    # 清除 localStorage
                    await self._page.evaluate("() => { localStorage.clear(); }")
                    # 清除 sessionStorage
                    await self._page.evaluate("() => { sessionStorage.clear(); }")
                    # 清除 indexedDB
                    await self._page.evaluate("""
                        () => {
                            if (window.indexedDB) {
                                return new Promise((resolve) => {
                                    const databases = indexedDB.databases ? indexedDB.databases() : Promise.resolve([]);
                                    databases.then(dbs => {
                                        const deletePromises = dbs.map(db => {
                                            return new Promise((deleteResolve) => {
                                                const deleteReq = indexedDB.deleteDatabase(db.name);
                                                deleteReq.onsuccess = () => deleteResolve();
                                                deleteReq.onerror = () => deleteResolve();
                                            });
                                        });
                                        Promise.all(deletePromises).then(() => resolve());
                                    }).catch(() => resolve());
                                });
                            }
                        }
                    """)
                
                # 清除缓存（如果支持）
                try:
                    await self._context.clear_permissions()
                except Exception as e:
                    logger.debug(f"清除权限失败（可能不支持）: {e}")
            
            # 清除本地 cookie 文件
            if self.cookie_storage:
                self.cookie_storage.clear_cookies()
            
            logger.info("已清除浏览器的所有数据")
            return True
            
        except Exception as e:
            logger.error(f"清除浏览器数据失败: {e}")
            return False
    
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
    
    async def cleanup(self) -> None:
        """清理浏览器资源（别名方法）"""
        await self.stop()