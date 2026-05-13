"""
浏览器管理器

负责 Playwright 浏览器实例的创建、配置和生命周期管理。
登录态仅依赖持久化 Chrome User Data 目录，不再使用 cookies JSON。
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth
from loguru import logger

from .profile_paths import resolve_profile_user_data_dir


class BrowserManager:
    """浏览器管理器"""

    def __init__(
        self,
        headless: bool = False,
        browser_type: str = "chromium",
        user_data_dir: Optional[Path] = None,
        profile_user: Optional[str] = None,
        executable_path: Optional[str] = None,
    ):
        """
        Args:
            headless: 是否无头模式
            browser_type: 浏览器类型（当前仅支持 chromium 持久化上下文）
            user_data_dir: 用户数据目录；省略则按 profile_user / GLOBAL_USER 解析
            profile_user: 非 GLOBAL_USER 时使用独立子目录 browser-profile-users/<user>
            executable_path: 本地浏览器可执行文件；省略则从配置读取或使用 Playwright Chromium
        """
        self.headless = headless
        self.browser_type = browser_type

        from ..config.settings import Settings, get_project_root

        if user_data_dir is not None:
            raw = Path(user_data_dir)
            p = raw.expanduser()
            if not p.is_absolute():
                p = get_project_root() / p
            self.user_data_dir = p
        else:
            self.user_data_dir = resolve_profile_user_data_dir(profile_user)

        self._chrome_profile_directory = Settings.BROWSER_CHROME_PROFILE_DIRECTORY

        if executable_path is None:
            executable_path = Settings.BROWSER_EXECUTABLE_PATH
        self.executable_path = executable_path

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    @property
    def browser(self) -> Optional[Browser]:
        return self._browser

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._context

    @property
    def page(self) -> Optional[Page]:
        return self._page

    def is_started(self) -> bool:
        return self._playwright is not None and self._context is not None

    def is_valid(self) -> bool:
        try:
            if not self.is_started():
                return False
            if self._browser and hasattr(self._browser, "is_connected"):
                return self._browser.is_connected()
            if self._page and hasattr(self._page, "is_closed"):
                return not self._page.is_closed()
            return True
        except Exception:
            return False

    async def ensure_started(self) -> None:
        if not self.is_valid():
            logger.warning("浏览器无效或已关闭，正在重启...")
            await self.restart()

    async def restart(self, *, reset_profile: bool = False) -> None:
        """
        重启浏览器。

        Args:
            reset_profile: 若为 True，在启动前删除当前 user_data_dir（慎用，等同清空该自动化配置）。
        """
        logger.info("重启浏览器")
        await self.stop()
        if reset_profile and self.user_data_dir and self.user_data_dir.exists():
            import shutil

            shutil.rmtree(self.user_data_dir, ignore_errors=True)
        await self.start()
        logger.info("浏览器重启完成")

    async def start(self) -> None:
        if self._playwright is not None:
            logger.warning("浏览器已经启动")
            return

        if self.browser_type != "chromium":
            raise ValueError("当前仅支持 chromium 与持久化 User Data，请使用 browser_type='chromium'")

        logger.info(f"启动浏览器 (headless={self.headless}, type={self.browser_type})")
        if self.executable_path:
            logger.info(f"使用本地浏览器: {self.executable_path}")

        ud_resolved = self.user_data_dir.resolve()
        ud_low = str(ud_resolved).lower()
        if "google" in ud_low and "chrome" in ud_low and "user data" in ud_low:
            logger.warning(
                "BROWSER_USER_DATA_DIR 指向系统 Chrome 的 User Data，易与日常浏览器抢锁。"
                "请改为自建专用目录，示例见 .env.example。"
            )
        else:
            logger.info("使用持久化 User Data（登录态写入该目录，不再使用 cookies JSON）")

        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()
        browser_launcher = getattr(self._playwright, self.browser_type)

        from ..config import BrowserConfig

        extra_args = list(BrowserConfig.BROWSER_ARGS)
        if self._chrome_profile_directory:
            extra_args.append(f"--profile-directory={self._chrome_profile_directory}")

        context_options = {
            "viewport": {"width": BrowserConfig.VIEWPORT_WIDTH, "height": BrowserConfig.VIEWPORT_HEIGHT},
            "user_agent": BrowserConfig.USER_AGENT,
            "java_script_enabled": True,
            "accept_downloads": True,
            "ignore_https_errors": True,
        }

        channel: Optional[str] = None
        executable_path_opt: Optional[str] = None
        if self.executable_path and self.browser_type == "chromium":
            exe_name = Path(self.executable_path).name.lower()
            if exe_name == "chrome.exe":
                channel = "chrome"
                logger.info("检测到 Chrome，使用 channel=chrome 启动（由 Playwright 解析本机 Chrome）")
            else:
                executable_path_opt = self.executable_path
        elif self.executable_path:
            executable_path_opt = self.executable_path

        persist_ctx_opts = {k: v for k, v in context_options.items() if k != "viewport"}
        persist_kw: Dict[str, Any] = {
            "user_data_dir": str(ud_resolved),
            "headless": self.headless,
            "args": extra_args,
            "no_viewport": True,
            "ignore_default_args": ["--disable-extensions"],
            **persist_ctx_opts,
        }
        if channel:
            persist_kw["channel"] = channel
        if executable_path_opt:
            persist_kw["executable_path"] = executable_path_opt

        try:
            self._context = await browser_launcher.launch_persistent_context(**persist_kw)
        except Exception as e:
            logger.error(
                "Chrome 持久化启动失败（检查目录是否为专用路径、勿指向系统 User Data）: {}",
                e,
            )
            raise

        self._browser = self._context.browser

        if self._context.pages:
            self._page = self._context.pages[0]
        else:
            self._page = await self._context.new_page()

        await self._apply_stealth(self._page)
        logger.info("浏览器启动成功")

    async def stop(self) -> None:
        if not self.is_started():
            return

        logger.info("停止浏览器")

        if self._page:
            await self._page.close()
            self._page = None

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("浏览器已停止")

    async def get_page(self) -> Page:
        await self.ensure_started()
        if self._page is None:
            await self.start()
        return self._page

    async def new_page(self) -> Page:
        if self._context is None:
            await self.start()
        page = await self._context.new_page()
        await self._apply_stealth(page)
        return page

    async def clear_all_data(self) -> bool:
        if not self.is_started():
            logger.warning("浏览器未启动，无法清除数据")
            return False

        try:
            if self._context:
                await self._context.clear_cookies()
                if self._page:
                    await self._page.evaluate("() => { localStorage.clear(); }")
                    await self._page.evaluate("() => { sessionStorage.clear(); }")
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
                try:
                    await self._context.clear_permissions()
                except Exception as e:
                    logger.debug(f"清除权限失败（可能不支持）: {e}")

            logger.info("已清除当前上下文中的站点数据（持久化文件仍在 User Data 目录内）")
            return True

        except Exception as e:
            logger.error(f"清除浏览器数据失败: {e}")
            return False

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def cleanup(self) -> None:
        await self.stop()

    async def _apply_stealth(self, page: Page) -> None:
        try:
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            logger.debug("已应用 playwright-stealth 反检测脚本")
        except Exception as e:
            logger.warning(f"应用反检测脚本失败: {e}，继续执行")
