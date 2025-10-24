"""
简化版小红书登录管理器

目标：提供稳定、简洁、可依赖的登录流程：
- 初始化/清理
- 打开登录弹窗并获取二维码
- 轮询等待登录完成（不导航，不打断扫码）
- 快速判断是否已登录（基于Cookie或关键元素）
"""

import asyncio
from typing import Optional, Tuple
from loguru import logger

from ..browser.browser_manager import BrowserManager
from ..browser.page_controller import PageController
from ..storage.cookie_storage import CookieStorage


class SimpleLoginManager:
    """简化版登录管理器"""

    XHS_URL = "https://www.xiaohongshu.com/explore"
    QR_CSS = ".login-container .qrcode-img"
    QR_XPATH = "//img[contains(@class, 'qrcode-img')]"
    LOGIN_BUTTON_CSS = "button:has-text(\"登录\")"
    USER_LINK_CSS = ".main-container .user .link-wrapper .channel"
    LOGIN_COOKIES = {"xhs_sso", "xsec_token", "webId"}
    USER_LINK_XPATH = "//ul/div[contains(@class, 'channel-list-content')]/li//a[normalize-space(.)=\"我\"][contains(@class, 'link-wrapper')]"
    MASK_CSS = "i.reds-mask"

    def __init__(self, browser_manager: BrowserManager, cookie_storage: CookieStorage, shared_browser: bool = False):
        self.browser_manager = browser_manager
        self.cookie_storage = cookie_storage
        self.page_controller: Optional[PageController] = None
        self.shared_browser = shared_browser  # 标记是否使用共享浏览器

    async def initialize(self) -> None:
        """启动浏览器并准备页面控制器"""
        if not self.browser_manager.is_started():
            await self.browser_manager.start()
        page = await self.browser_manager.get_page()
        self.page_controller = PageController(page)
        # 不在此处主动加载 cookies，避免重复加载
        logger.info("简化登录管理器初始化完成")

    async def cleanup(self) -> None:
        """关闭浏览器并清理资源"""
        # 如果是共享浏览器，不要关闭它
        if not self.shared_browser and self.browser_manager.is_started():
            await self.browser_manager.stop()
        logger.info("简化登录管理器资源清理完成")

    async def is_logged_in(self, navigate: bool = False) -> bool:
        """仅通过 DOM 检查是否已登录；可选是否导航到探索页"""
        if not self.page_controller:
            await self.initialize()
        try:
            if navigate:
                await self.page_controller.navigate(self.XHS_URL, wait_until="domcontentloaded")
            # 负向检查：出现“登录”按钮通常表示未登录
            try:
                if await self.page_controller.has_element(self.LOGIN_BUTTON_CSS, timeout=1000):
                    logger.debug("检测到登录按钮，判定为未登录")
                    return False
            except Exception:
                pass
            # 负向信号（不强制返回）：遮罩层可能存在但不代表未登录，继续正向检查
            try:
                if await self.page_controller.has_element(self.MASK_CSS, timeout=1000):
                    logger.debug("检测到遮罩层，继续进行登录态正向检查")
            except Exception:
                pass
            # 正向检查：CSS 可见
            try:
                await self.page_controller.wait_for_element(self.USER_LINK_CSS, timeout=2000, state="visible")
                logger.info("检测到用户链接元素（CSS可见），判断为已登录")
                return True
            except Exception:
                pass
            # 正向检查：XPath 附加（在弹窗遮挡下更稳）
            try:
                await self.page_controller.wait_for_element(self.USER_LINK_XPATH, timeout=2000, state="attached")
                logger.info("检测到用户链接元素（XPath附加），判断为已登录")
                return True
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"登录状态 DOM 检查失败: {e}")
        return False

    async def open_login_modal(self) -> bool:
        """导航到探索页，打开登录弹窗，如果已登录则返回 False"""
        if not self.page_controller:
            await self.initialize()
        await self.page_controller.navigate(self.XHS_URL, wait_until="domcontentloaded")
        if await self.is_logged_in(navigate=False):
            logger.info("已登录，跳过打开登录弹窗")
            return False
        # 点击“登录”按钮，触发弹窗
        try:
            await self.page_controller.click_element(self.LOGIN_BUTTON_CSS, timeout=8000)
            logger.info("已点击登录按钮，等待弹窗与二维码")
        except Exception as e:
            logger.warning(f"未找到或无法点击登录按钮: {e}")
        return True

    async def get_qrcode(self) -> Optional[str]:
        """确保弹窗打开并返回二维码图片 URL；如果已登录返回 None"""
        if not self.page_controller:
            await self.initialize()
        opened = await self.open_login_modal()
        if not opened and await self.is_logged_in(navigate=False):
            return None
        # 等待二维码元素出现
        try:
            if await self.page_controller.has_element(self.QR_CSS, timeout=90000):
                src = await self.page_controller.get_attribute(self.QR_CSS, "src")
            else:
                src = await self.page_controller.get_attribute(self.QR_XPATH, "src")
            if src:
                logger.info("二维码已获取")
                return src
        except Exception as e:
            logger.error(f"二维码元素未找到或获取失败: {e}")
            return None
        return None

    async def wait_for_login(self, timeout: int = 60, interval: float = 2.0, fresh: bool = False) -> Tuple[bool, str, bool]:
        """轮询等待登录成功；返回 (success, message, cookies_saved)
        如果 fresh=True，会在等待前清空 cookies，确保不会被旧会话误判为已登录。
        """
        if not self.page_controller:
            await self.initialize()
        # fresh 模式：清空 cookies（文件和上下文）- 但在共享浏览器模式下跳过
        if fresh and not self.shared_browser:
            try:
                self.cookie_storage.clear_cookies()
                page = await self.browser_manager.get_page()
                await page.context.clear_cookies()
                logger.info("已清空 cookies，开始干净的登录等待")
            except Exception as ce:
                logger.warning(f"清空 cookies 失败: {ce}")
        logger.info(f"开始等待用户登录，超时={timeout}s, 间隔={interval}s")
        start = asyncio.get_event_loop().time()
        while True:
            # 超时判断
            if asyncio.get_event_loop().time() - start > timeout:
                logger.warning("等待登录超时")
                return False, "等待登录超时", False
            # 状态检查（不导航，不打断扫码）
            try:
                if await self.is_logged_in(navigate=False):
                    ok = await self.browser_manager.save_cookies()
                    logger.info("登录成功，已保存 cookies")
                    return True, "登录成功", ok
                else:
                    # 兜底：在 fresh 会话下，使用登录相关 Cookie 作为成功信号
                    try:
                        cookies = await self.page_controller.get_cookies()
                        has_login_cookie = any(c.get('name') in self.LOGIN_COOKIES and c.get('value') for c in cookies)
                        if fresh and has_login_cookie:
                            ok = await self.browser_manager.save_cookies()
                            logger.info("检测到登录相关 Cookies（fresh会话），判断为登录成功")
                            return True, "登录成功", ok
                    except Exception as ce:
                        logger.debug(f"读取 Cookie 失败: {ce}")
            except asyncio.CancelledError:
                # 忽略会话切换导致的取消
                logger.debug("等待循环被取消，继续轮询")
            except Exception as e:
                logger.debug(f"等待期间检查失败: {e}")
            await asyncio.sleep(interval)

    async def login(self, headless: bool = False, timeout: int = 300, fresh: bool = True) -> Tuple[bool, str, bool]:
        """完整登录：打开弹窗→等待登录；返回 (success, message, cookies_saved)
        默认 fresh=True，强制清空 cookies，确保需要扫码而不是复用旧会话。
        """
        try:
            # 在启动前设置 headless
            self.browser_manager.headless = headless
            await self.initialize()
            # fresh 模式：清空 cookies（文件和上下文）- 但在共享浏览器模式下跳过
            if fresh and not self.shared_browser:
                try:
                    self.cookie_storage.clear_cookies()
                    page = await self.browser_manager.get_page()
                    await page.context.clear_cookies()
                    logger.info("已清空 cookies，开始干净的登录流程")
                except Exception as ce:
                    logger.warning(f"清空 cookies 失败: {ce}")
            # 导航后通过 DOM 检查当前是否已登录
            if await self.is_logged_in(navigate=True):
                ok = await self.browser_manager.save_cookies()
                return True, "用户已登录", ok
            # 打开登录弹窗并等待扫码登录
            await self.open_login_modal()
            success, message, saved = await self.wait_for_login(timeout=timeout, interval=2.0, fresh=fresh)
            return success, message, saved
        except Exception as e:
            logger.error(f"登录流程失败: {e}")
            return False, f"登录失败: {e}", False

    async def logout(self) -> bool:
        """清除本地与浏览器中的 Cookie"""
        try:
            ok = self.cookie_storage.clear_cookies()
            if self.browser_manager.is_started():
                page = await self.browser_manager.get_page()
                await page.context.clear_cookies()
            logger.info("已清除 cookies")
            return ok
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return False

    async def save_cookies(self) -> bool:
        """保存当前浏览器的 cookies"""
        try:
            if self.browser_manager.is_started():
                ok = await self.browser_manager.save_cookies()
                logger.info("已保存 cookies")
                return ok
            else:
                logger.warning("浏览器未启动，无法保存 cookies")
                return False
        except Exception as e:
            logger.error(f"保存 cookies 失败: {e}")
            return False