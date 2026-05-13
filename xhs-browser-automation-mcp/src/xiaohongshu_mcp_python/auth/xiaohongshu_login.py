"""
小红书登录管理器：浏览器初始化、登录弹窗、阻塞等待登录完成、DOM 登录态检查。
登录态仅写入持久化 Chrome User Data，不使用 cookies JSON。
"""

import asyncio
from typing import Optional, Tuple
from loguru import logger
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from ..browser.browser_manager import BrowserManager
from ..browser.page_controller import PageController
from ..config import settings
from ..config.xhs_xpath import XHSXPath


class XiaohongshuLogin:
    """小红书登录管理器"""

    XHS_URL = XHSXPath.XHS_URL
    QR_CSS = XHSXPath.QR_CSS
    QR_XPATH = XHSXPath.QR_XPATH
    LOGIN_BUTTON_XPATH = XHSXPath.LOGIN_BUTTON_XPATH
    USER_LINK_XPATH = XHSXPath.USER_LINK_XPATH
    MASK_CSS = XHSXPath.MASK_CSS
    LOGIN_MODAL_CSS = XHSXPath.LOGIN_MODAL_CSS
    LOGIN_MODAL_XPATH = XHSXPath.LOGIN_MODAL_XPATH
    LOGIN_MODAL_SUBMIT_XPATH = XHSXPath.LOGIN_MODAL_SUBMIT_XPATH
    LOGIN_COOKIES = XHSXPath.LOGIN_COOKIES

    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.page_controller: Optional[PageController] = None

    async def initialize(self) -> None:
        if not self.browser_manager.is_started():
            await self.browser_manager.start()
        page = await self.browser_manager.get_page()
        self.page_controller = PageController(page)
        logger.info("小红书登录管理器初始化完成")

    async def cleanup(self, save_cookies: bool = True) -> None:
        """关闭浏览器。save_cookies 参数保留兼容，已无 JSON 可保存。"""
        if self.browser_manager.is_started():
            await self.browser_manager.stop()
        logger.info("小红书登录管理器资源清理完成（浏览器已关闭）")

    async def is_logged_in(self, navigate: bool = False) -> bool:
        if not self.page_controller:
            await self.initialize()
        try:
            if navigate:
                try:
                    await self.page_controller.navigate(self.XHS_URL, wait_until="domcontentloaded")
                except Exception as nav_err:
                    err_s = str(nav_err).lower()
                    try:
                        cur = (self.page_controller.page.url or "").lower()
                    except Exception:
                        cur = ""
                    if "xiaohongshu.com" in cur and (
                        "err_aborted" in err_s or "net::" in err_s
                    ):
                        logger.warning(
                            "导航探索页异常但当前已在小红书域内，改为在当前页检测登录态: {}",
                            nav_err,
                        )
                    else:
                        raise

            try:
                await self.page_controller.wait_for_element(self.USER_LINK_XPATH, timeout=2000, state="visible")
                logger.info("检测到用户链接元素，判断为已登录")
                return True
            except Exception:
                pass

            try:
                if await self.page_controller.has_element(self.LOGIN_BUTTON_XPATH, timeout=2000):
                    logger.debug("检测到顶栏登录按钮，判定为未登录")
                    return False
            except Exception:
                pass
            try:
                if await self.page_controller.has_element(self.LOGIN_MODAL_SUBMIT_XPATH, timeout=2000):
                    logger.debug("检测到登录弹窗内提交按钮，判定为未登录")
                    return False
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"登录状态 DOM 检查失败: {e}")
        return False

    async def open_login_modal(self) -> bool:
        if not self.page_controller:
            await self.initialize()
        await self.page_controller.navigate(self.XHS_URL, wait_until="domcontentloaded")
        if await self.is_logged_in(navigate=False):
            logger.info("已登录，跳过打开登录弹窗")
            return False
        try:
            await self.page_controller.click_element(self.LOGIN_BUTTON_XPATH, timeout=8000)
            logger.info("已点击登录按钮，等待弹窗与二维码")
        except Exception as e:
            logger.warning(f"未找到或无法点击登录按钮: {e}")
        return True

    async def get_qrcode(self) -> Optional[str]:
        if not self.page_controller:
            await self.initialize()
        opened = await self.open_login_modal()
        if not opened and await self.is_logged_in(navigate=False):
            return None
        try:
            if await self.page_controller.has_element(self.QR_CSS, timeout=settings.LOGIN_QR_WAIT_MS):
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

    async def wait_for_login(self, timeout: Optional[int] = None) -> Tuple[bool, str, bool]:
        if not self.page_controller:
            await self.initialize()

        page = await self.browser_manager.get_page()
        effective_timeout = settings.LOGIN_WAIT_TIMEOUT if timeout is None else timeout

        try:
            await page.wait_for_selector(
                self.USER_LINK_XPATH,
                state="visible",
                timeout=effective_timeout * 1000,
            )
            logger.info("登录成功，会话已写入持久化 Chrome User Data")
            return True, "登录成功", True
        except PlaywrightTimeoutError:
            logger.warning(f"等待登录超时（{effective_timeout}秒）")
            return False, f"超时（{effective_timeout}秒）", False

    async def login(
        self, headless: bool = False, timeout: Optional[int] = None, fresh: bool = True
    ) -> Tuple[bool, str, bool]:
        try:
            self.browser_manager.headless = headless
            await self.initialize()
            if fresh:
                try:
                    page = await self.browser_manager.get_page()
                    await page.context.clear_cookies()
                    logger.info("已清空当前上下文 Cookie，开始干净登录流程")
                except Exception as ce:
                    logger.warning(f"清空 Cookie 失败: {ce}")
            if await self.is_logged_in(navigate=True):
                return True, "用户已登录", True
            await self.open_login_modal()
            success, message, saved = await self.wait_for_login(timeout=timeout)
            return success, message, saved
        except Exception as e:
            logger.error(f"登录流程失败: {e}")
            return False, f"登录失败: {e}", False

    async def logout(self) -> bool:
        try:
            if self.browser_manager.is_started():
                page = await self.browser_manager.get_page()
                await page.context.clear_cookies()
            logger.info("已清除当前上下文 Cookie（磁盘 profile 仍保留，需手动删目录可彻底退出）")
            return True
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return False

    async def save_cookies(self) -> bool:
        """兼容旧接口：登录态已由持久化 User Data 保存。"""
        logger.info("登录态由持久化 Chrome User Data 维护（无 cookies JSON）")
        return True
