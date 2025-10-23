"""
小红书登录管理器

提供完整的登录功能，包括状态检查、二维码获取、登录等待等。
"""

import asyncio
import base64
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
    
    async def check_login_status(self) -> LoginStatus:
        """
        检查登录状态
        
        Returns:
            登录状态
        """
        if not self.page_controller:
            await self.initialize()
        
        try:
            # 导航到小红书探索页面
            await self.page_controller.navigate(
                self.config.xiaohongshu_url,
                wait_until="domcontentloaded"
            )
            
            # 等待页面稳定
            await self.page_controller.wait_for_stable(timeout=5000)
            
            # 检查登录状态元素
            is_logged_in = await self.page_controller.has_element(
                self.config.login_check_selector,
                timeout=5000
            )
            
            if is_logged_in:
                logger.info("用户已登录")
                return LoginStatus.LOGGED_IN
            else:
                logger.info("用户未登录")
                return LoginStatus.NOT_LOGGED_IN
        
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
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
            
            # 检查是否已经登录
            status = await self.check_login_status()
            if status == LoginStatus.LOGGED_IN:
                logger.info("用户已登录，无需获取二维码")
                return None
            
            # 等待二维码元素出现
            try:
                await self.page_controller.wait_for_element(
                    self.config.qrcode_selector,
                    timeout=self.config.qrcode_timeout * 1000
                )
            except Exception:
                logger.error("二维码元素未找到，可能页面结构已变化")
                return None
            
            # 获取二维码图片URL
            image_url = await self.page_controller.get_attribute(
                self.config.qrcode_selector,
                "src"
            )
            
            if not image_url:
                logger.error("无法获取二维码图片URL")
                return None
            
            logger.info(f"成功获取二维码: {image_url}")
            
            # 如果是base64格式，直接解码
            image_data = None
            if image_url.startswith("data:image"):
                try:
                    # 提取base64数据
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
        
        Args:
            timeout: 超时时间（秒），如果为None则使用配置中的默认值
        
        Returns:
            登录结果
        """
        if not self.page_controller:
            await self.initialize()
        
        timeout = timeout or self.config.login_wait_timeout
        check_interval = self.config.login_check_interval / 1000  # 转换为秒
        
        logger.info(f"开始等待用户登录，超时时间: {timeout}秒")
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            
            # 检查超时
            if current_time - start_time > timeout:
                logger.warning("等待登录超时")
                return LoginResult.failure_result("等待登录超时")
            
            try:
                # 检查登录状态
                status = await self.check_login_status()
                
                if status == LoginStatus.LOGGED_IN:
                    logger.info("用户登录成功")
                    
                    # 保存Cookie
                    cookies_saved = await self.browser_manager.save_cookies()
                    
                    return LoginResult.success_result(
                        message="登录成功",
                        cookies_saved=cookies_saved
                    )
                
                elif status == LoginStatus.UNKNOWN:
                    logger.warning("登录状态检查失败，继续等待")
                
                # 等待下次检查
                await asyncio.sleep(check_interval)
            
            except Exception as e:
                logger.error(f"等待登录过程中出错: {e}")
                await asyncio.sleep(check_interval)
    
    async def login(self, headless: bool = True) -> LoginResult:
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