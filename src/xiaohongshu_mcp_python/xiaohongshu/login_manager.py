"""
小红书登录管理器

提供完整的登录功能，包括状态检查、二维码获取、登录等待等。
"""

import asyncio
import base64
import traceback
from typing import Optional
from loguru import logger

from ..browser.browser_manager import BrowserManager
from ..browser.page_controller import PageController
from ..storage.cookie_storage import CookieStorage
from .login_types import LoginStatus, QRCodeInfo, LoginResult, LoginConfig


class LoginManager:
    """小红书登录管理器"""
    
    def __init__(
        self, 
        browser_manager: BrowserManager,
        cookie_storage: CookieStorage,
        config: Optional[LoginConfig] = None
    ):
        """
        初始化登录管理器
        
        Args:
            browser_manager: 浏览器管理器
            cookie_storage: Cookie存储
            config: 登录配置
        """
        self.browser_manager = browser_manager
        self.cookie_storage = cookie_storage
        self.config = config or LoginConfig()
        self.page_controller: Optional[PageController] = None
    
    async def initialize(self) -> None:
        """初始化登录管理器"""
        if not self.browser_manager.is_started():
            await self.browser_manager.start()
        
        # 获取页面控制器
        page = await self.browser_manager.get_page()
        self.page_controller = PageController(page)
        
        # 加载已保存的Cookie
        await self.browser_manager.load_cookies()
        
        logger.info("登录管理器初始化完成")
    
    async def check_login_status(self, navigate: bool = True) -> LoginStatus:
        """
        检查登录状态
        
        使用更精确的XPath选择器来判断登录状态：
        1. 检查页面是否加载完毕（通过封面或遮罩层判断）
        2. 检查是否存在"登录"按钮 - 存在则未登录
        3. 检查是否存在遮罩层 - 存在则未登录  
        4. 检查是否存在"我"链接 - 存在则已登录
        
        Returns:
            登录状态
        """
        if not self.page_controller:
            await self.initialize()
        
        try:
            # 可选导航到小红书探索页面（避免打断扫码流程）
            if navigate:
                logger.info(f"开始导航到: {self.config.xiaohongshu_url}")
                logger.debug("准备调用 page_controller.navigate 方法")
                await self.page_controller.navigate(
                    self.config.xiaohongshu_url,
                    wait_until="domcontentloaded"
                )
                logger.info("导航完成，页面已加载")
                logger.debug("navigate 方法调用成功，继续执行后续代码")
            else:
                logger.debug("跳过导航，保持当前页面进行快速登录检查")
            
            # 等待页面基本加载完成
            logger.debug("准备执行 asyncio.sleep(1)")
            try:
                if navigate:
                    await asyncio.sleep(1)
                    logger.debug("asyncio.sleep(1) 执行成功")
                else:
                    logger.debug("快速检查模式跳过初始延迟")
            except asyncio.CancelledError as cancel:
                logger.warning(f"asyncio.sleep(1) 被取消: {cancel}")
                if navigate:
                    raise
                else:
                    logger.debug("快速检查模式下忽略取消，继续检查")
            except BaseException as sleep_error:
                logger.error(f"asyncio.sleep(1) 出现异常: {sleep_error}")
                logger.error(f"异常类型: {type(sleep_error).__name__}")
                logger.error(f"完整异常信息: {traceback.format_exc()}")
                if navigate:
                    raise
                else:
                    logger.debug("快速检查模式下忽略异常，继续检查")
            
            logger.info("等待页面基本加载完成")
            logger.debug("asyncio.sleep(1) 执行完成")
            
            # 首先检查页面是否加载完毕 - 通过封面或遮罩层判断
            page_loaded = False
            logger.debug("开始检查页面是否加载完毕")
            try:
                # 检查是否存在封面元素（表示页面内容已加载）
                logger.debug("准备检查封面元素")
                cover_locator = self.page_controller.page.locator('//section[1]//a[contains(@class, "cover")]')
                logger.debug("封面元素定位器创建成功，准备等待元素可见")
                await cover_locator.wait_for(state="visible", timeout=2000)
                logger.debug("封面元素等待成功")
                page_loaded = True
                logger.debug("检测到封面元素，页面内容已加载")
            except Exception as cover_error:
                logger.debug(f"封面元素检查失败: {cover_error}")
                logger.debug(f"封面检查异常类型: {type(cover_error).__name__}")
                try:
                    # 检查是否存在遮罩层（表示页面结构已加载）
                    logger.debug("准备检查遮罩层元素")
                    mask_locator = self.page_controller.page.locator('//i[@class="reds-mask"]')
                    logger.debug("遮罩层元素定位器创建成功，准备等待元素可见")
                    await mask_locator.wait_for(state="visible", timeout=2000)
                    logger.debug("遮罩层元素等待成功")
                    page_loaded = True
                    logger.debug("检测到遮罩层，页面结构已加载")
                except Exception as mask_error:
                    logger.debug(f"遮罩层检查失败: {mask_error}")
                    logger.debug(f"遮罩层检查异常类型: {type(mask_error).__name__}")
                    logger.debug("页面可能还在加载中，继续检查登录状态")
            
            # 如果页面未完全加载，但仍然尝试检查登录状态
            if not page_loaded:
                logger.debug("页面加载状态不明确，但继续检查登录状态")
            
            # 1. 检查是否存在"登录"按钮 - 存在则未登录
            try:
                login_button = self.page_controller.page.locator('//ul/div[contains(@class, "channel-list-content")]//button[normalize-space(.)="登录"]')
                await login_button.wait_for(state="visible", timeout=1000)
                logger.info("检测到登录按钮，用户未登录")
                return LoginStatus.NOT_LOGGED_IN
            except Exception:
                pass  # 登录按钮不存在，继续检查其他元素
            
            # 2. 检查是否存在遮罩层 - 存在则未登录
            try:
                mask = self.page_controller.page.locator('//i[@class="reds-mask"]')
                await mask.wait_for(state="visible", timeout=1000)
                logger.info("检测到遮罩层，用户未登录")
                return LoginStatus.NOT_LOGGED_IN
            except Exception:
                pass  # 遮罩层不存在，继续检查其他元素
            
            # 3. 检查是否存在"我"链接 - 存在则已登录
            try:
                # 先用 CSS 选择器快速判断（更稳定）
                if await self.page_controller.has_element(self.config.login_success_selector, timeout=2000):
                    logger.info("检测到用户链接（CSS），用户已登录")
                    return LoginStatus.LOGGED_IN
                
                # 再用 XPath 作为兼容兜底
                user_link = self.page_controller.page.locator('//ul/div[contains(@class, "channel-list-content")]/li//a[normalize-space(.)="我"][contains(@class, "link-wrapper")]')
                await user_link.wait_for(state="visible", timeout=1500)
                logger.info("检测到用户链接（XPath），用户已登录")
                return LoginStatus.LOGGED_IN
            except Exception:
                pass  # 用户链接不存在
            
            # 如果页面已加载但未检测到明确状态，可能是其他情况
            if page_loaded:
                logger.debug("页面已加载但未检测到明确的登录状态指示元素")
            else:
                logger.debug("页面可能还在加载中，未检测到明确的登录状态指示元素")
            
            # 额外的 cookie 信号：如果有有效的登录 cookie（如 xhs_sso 或 webId），也认为已登录
            try:
                cookies = await self.page_controller.get_cookies()
                has_login_cookie = any(c.get('name') in ['xhs_sso', 'webId', 'xsec_token'] for c in cookies)
                if has_login_cookie:
                    logger.info("检测到登录相关 Cookie，判断为已登录")
                    return LoginStatus.LOGGED_IN
            except Exception as ce:
                logger.debug(f"读取 Cookie 失败: {ce}")
            
            return LoginStatus.UNKNOWN
        
        except Exception as e:
            if isinstance(e, asyncio.CancelledError):
                logger.warning(f"检查登录状态任务被取消: {e}")
                raise
            logger.error(f"检查登录状态失败: {e}")
            logger.error(f"异常类型: {type(e).__name__}")
            logger.error(f"异常消息: {str(e)}")
            logger.error(f"完整异常信息: {traceback.format_exc()}")
            return LoginStatus.UNKNOWN

    async def get_qrcode(self) -> Optional[QRCodeInfo]:
        """
        获取登录二维码
        
        Returns:
            二维码信息，如果获取失败返回None
        """
        if not self.page_controller:
            await self.initialize()
        
        try:
            # 确保在正确的页面
            await self.page_controller.navigate(
                self.config.xiaohongshu_url,
                wait_until="domcontentloaded"
            )
            
            # 检查是否已经登录（快速检查，避免再次导航）
            status = await self.check_login_status(navigate=False)
            if status == LoginStatus.LOGGED_IN:
                logger.info("用户已登录，无需获取二维码")
                return None
            
            # 如果未登录，需要触发登录弹窗
            # 先检查是否存在登录按钮，如果存在则点击
            try:
                login_button = self.page_controller.page.locator('//ul/div[contains(@class, "channel-list-content")]//button[normalize-space(.)="登录"]')
                await login_button.wait_for(state="visible", timeout=5000)
                await login_button.click()
                logger.info("点击登录按钮，触发登录弹窗")
                
                # 等待登录弹窗出现
                await asyncio.sleep(2)
            except Exception as e:
                logger.debug(f"未找到登录按钮或点击失败: {e}")
            
            # 等待二维码元素出现
            logger.info("等待二维码加载...")
            try:
                # 优先使用 CSS 选择器，避免 XPath 变化带来的不稳定
                if await self.page_controller.has_element('.login-container .qrcode-img', timeout=self.config.qrcode_timeout * 1000):
                    image_url = await self.page_controller.get_attribute('.login-container .qrcode-img', 'src')
                else:
                    qrcode_locator = self.page_controller.page.locator(self.config.qrcode_selector)
                    await qrcode_locator.wait_for(state="visible", timeout=self.config.qrcode_timeout * 1000)
                    image_url = await self.page_controller.get_attribute(self.config.qrcode_selector, "src")
                logger.info("二维码元素已出现")
            except Exception as e:
                logger.error(f"二维码元素未找到，可能页面结构已变化: {e}")
                return None
            
            if not image_url:
                logger.error("无法获取二维码图片URL")
                return None
            
            logger.info(f"成功获取二维码: {image_url}")
            
            # 如果是base64格式，直接解码
            image_data = None
            if image_url.startswith("data:image"):
                try:
                    base64_data = image_url.split(",")[1]
                    image_data = base64.b64decode(base64_data)
                    logger.info("成功解码base64二维码图片")
                except Exception as e:
                    logger.warning(f"解码base64图片失败: {e}")
            
            return QRCodeInfo(
                image_url=image_url,
                image_data=image_data
            )
        except Exception as e:
            logger.error(f"获取二维码失败: {e}")
            return None
    
    async def wait_for_login(self, timeout: Optional[int] = None) -> LoginResult:
        """
        等待用户扫码登录
        """
        if not self.page_controller:
            await self.initialize()
        
        timeout = timeout or self.config.login_wait_timeout
        check_interval = self.config.login_check_interval / 1000
        
        logger.info(f"开始等待用户登录，超时时间: {timeout}秒，检查间隔: {check_interval}秒")
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            
            if current_time - start_time > timeout:
                logger.warning("等待登录超时")
                return LoginResult.failure_result("等待登录超时")
            
            try:
                status = await self.check_login_status(navigate=False)
                
                if status == LoginStatus.LOGGED_IN:
                    logger.info("用户登录成功")
                    
                    cookies_saved = await self.browser_manager.save_cookies()
                    
                    return LoginResult.success_result(
                        message="登录成功",
                        cookies_saved=cookies_saved
                    )
                elif status == LoginStatus.UNKNOWN:
                    logger.debug("登录状态检查失败，继续等待")
                else:
                    logger.debug(f"当前登录状态: {status.value}，继续等待")
                
                await asyncio.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"等待登录过程中出错: {e}")
                await asyncio.sleep(check_interval)
    
    async def login(self, headless: bool = False) -> LoginResult:
        """
        执行完整的登录流程
        
        Args:
            headless: 是否使用无头模式
        
        Returns:
            登录结果
        """
        try:
            # 设置浏览器模式
            self.browser_manager.headless = headless
            
            # 初始化
            await self.initialize()
            
            # 检查当前登录状态
            status = await self.check_login_status()
            if status == LoginStatus.LOGGED_IN:
                return LoginResult.success_result("用户已登录")
            

            
            # 获取二维码
            qrcode_info = await self.get_qrcode()
            if not qrcode_info:
                return LoginResult.failure_result("无法获取登录二维码")
            
            logger.info("请使用小红书APP扫描二维码登录")
            
            # 等待用户登录
            result = await self.wait_for_login()
            
            return result
        
        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            return LoginResult.failure_result(f"登录失败: {str(e)}")
    
    async def logout(self) -> bool:
        """
        登出（清除Cookie）
        
        Returns:
            是否成功
        """
        try:
            # 清除Cookie文件
            success = self.cookie_storage.clear_cookies()
            
            # 如果浏览器已启动，也清除浏览器中的Cookie
            if self.browser_manager.is_started():
                page = await self.browser_manager.get_page()
                context = page.context
                await context.clear_cookies()
            
            logger.info("登出成功")
            return success
        
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return False
    
    async def cleanup(self) -> None:
        """清理资源"""
        if self.browser_manager.is_started():
            await self.browser_manager.stop()
        logger.info("登录管理器资源清理完成")