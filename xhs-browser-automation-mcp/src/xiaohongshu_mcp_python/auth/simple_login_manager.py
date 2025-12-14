"""
小红书登录管理器

提供稳定、可靠的登录流程：
- 浏览器初始化和资源清理
- 打开登录弹窗并获取二维码
- 阻塞等待登录完成（登录框消失且"我的"按钮出现）
- 登录状态检查（基于DOM元素和Cookie）
"""

import asyncio
from typing import Optional, Tuple
from loguru import logger

from ..browser.browser_manager import BrowserManager
from ..browser.page_controller import PageController
from ..storage.cookie_storage import CookieStorage
from ..config.xhs_xpath import XHSXPath


class XiaohongshuLogin:
    """小红书登录管理器"""
    
    # 使用配置文件中的选择器
    XHS_URL = XHSXPath.XHS_URL
    QR_CSS = XHSXPath.QR_CSS
    QR_XPATH = XHSXPath.QR_XPATH
    LOGIN_BUTTON_CSS = XHSXPath.LOGIN_BUTTON_CSS
    USER_LINK_CSS = XHSXPath.USER_LINK_CSS
    USER_LINK_XPATH = XHSXPath.USER_LINK_XPATH_STRICT  # 使用更精确的版本
    MASK_CSS = XHSXPath.MASK_CSS
    LOGIN_MODAL_CSS = XHSXPath.LOGIN_MODAL_CSS
    LOGIN_MODAL_XPATH = XHSXPath.LOGIN_MODAL_XPATH
    LOGIN_COOKIES = XHSXPath.LOGIN_COOKIES

    def __init__(self, browser_manager: BrowserManager, cookie_storage: CookieStorage):
        self.browser_manager = browser_manager
        self.cookie_storage = cookie_storage
        self.page_controller: Optional[PageController] = None

    async def initialize(self) -> None:
        """启动浏览器并准备页面控制器"""
        if not self.browser_manager.is_started():
            await self.browser_manager.start()
        page = await self.browser_manager.get_page()
        self.page_controller = PageController(page)
        # 不在此处主动加载 cookies，避免重复加载
        logger.info("小红书登录管理器初始化完成")

    async def cleanup(self, save_cookies: bool = True) -> None:
        """
        关闭浏览器并清理资源
        
        Args:
            save_cookies: 是否保存cookies，默认为True
        """
        if self.browser_manager.is_started():
            await self.browser_manager.stop(save_cookies=save_cookies)
        logger.info("小红书登录管理器资源清理完成（浏览器已关闭）")

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

    async def wait_for_login(self, timeout: int = 90, interval: float = 0.5, fresh: bool = False) -> Tuple[bool, str, bool]:
        """
        阻塞等待登录成功：直到登录框消失且"我的"按钮出现
        返回 (success, message, cookies_saved)
        
        Args:
            timeout: 超时时间（秒），默认90秒
            interval: 检查间隔（秒），默认0.5秒
            fresh: 如果为True，会在等待前清空 cookies，确保不会被旧会话误判为已登录
        
        Returns:
            (success, message, cookies_saved) 元组
        """
        if not self.page_controller:
            await self.initialize()
        
        # fresh 模式：清空 cookies（文件和上下文）
        if fresh:
            try:
                self.cookie_storage.clear_cookies()
                page = await self.browser_manager.get_page()
                await page.context.clear_cookies()
                logger.info("已清空 cookies，开始干净的登录等待")
            except Exception as ce:
                logger.warning(f"清空 cookies 失败: {ce}")
        
        logger.info(f"开始阻塞等待登录完成，超时={timeout}s, 检查间隔={interval}s")
        logger.info("等待条件：1) 登录框消失 2) '我的'按钮出现")
        
        start_time = asyncio.get_event_loop().time()
        last_log_time = start_time
        
        while True:
            # 超时判断
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            if elapsed > timeout:
                logger.warning(f"等待登录超时（{timeout}秒）")
                return False, f"等待登录超时（{timeout}秒）", False
            
            try:
                # 检查条件1：登录框是否消失（使用CSS和XPath两种方式）
                login_modal_exists = False
                page = await self.browser_manager.get_page()
                try:
                    # 尝试使用CSS选择器检查
                    locator_css = page.locator(self.LOGIN_MODAL_CSS)
                    await locator_css.wait_for(state="visible", timeout=500)
                    login_modal_exists = True
                except Exception:
                    try:
                        # 如果CSS失败，尝试使用XPath
                        locator_xpath = page.locator(self.LOGIN_MODAL_XPATH)
                        await locator_xpath.wait_for(state="visible", timeout=500)
                        login_modal_exists = True
                    except Exception:
                        # 如果都失败，假设登录框不存在
                        login_modal_exists = False
                
                # 检查条件2："我的"按钮是否出现
                user_button_exists = False
                try:
                    # 尝试使用XPath检查"我的"按钮（更可靠）
                    locator_xpath = page.locator(self.USER_LINK_XPATH)
                    await locator_xpath.wait_for(state="visible", timeout=500)
                    user_button_exists = True
                except Exception:
                    try:
                        # 如果XPath失败，尝试使用CSS
                        locator_css = page.locator(self.USER_LINK_CSS)
                        await locator_css.wait_for(state="visible", timeout=500)
                        user_button_exists = True
                    except Exception:
                        user_button_exists = False
                
                # 两个条件都满足：登录框消失且"我的"按钮出现
                if not login_modal_exists and user_button_exists:
                    logger.info("登录完成：登录框已消失且'我的'按钮已出现")
                    ok = await self.browser_manager.save_cookies()
                    logger.info("登录成功，已保存 cookies")
                    return True, "登录成功：登录框已消失且'我的'按钮已出现", ok
                
                # 每5秒记录一次当前状态（用于调试）
                if current_time - last_log_time >= 5.0:
                    logger.debug(
                        f"等待中... (已等待 {elapsed:.1f}s / {timeout}s) - "
                        f"登录框存在: {login_modal_exists}, "
                        f"'我的'按钮存在: {user_button_exists}"
                    )
                    last_log_time = current_time
                    
            except asyncio.CancelledError:
                logger.debug("等待循环被取消，继续轮询")
            except Exception as e:
                logger.debug(f"等待期间检查失败: {e}")
            
            await asyncio.sleep(interval)

    async def login(self, headless: bool = False, timeout: int = 90, fresh: bool = True) -> Tuple[bool, str, bool]:
        """
        完整登录：打开弹窗→阻塞等待登录完成（登录框消失且"我的"按钮出现）
        返回 (success, message, cookies_saved)
        
        默认 fresh=True，强制清空 cookies，确保需要扫码而不是复用旧会话。
        默认 timeout=90秒，阻塞等待直到登录框消失且"我的"按钮出现。
        """
        try:
            # 在启动前设置 headless
            self.browser_manager.headless = headless
            await self.initialize()
            # fresh 模式：清空 cookies（文件和上下文）
            if fresh:
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
            # 打开登录弹窗并阻塞等待登录完成
            await self.open_login_modal()
            success, message, saved = await self.wait_for_login(timeout=timeout, interval=0.5, fresh=fresh)
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