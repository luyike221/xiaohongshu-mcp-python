"""
登录会话管理器
用于支持会话化的短轮询登录流程，避免 MCP Inspector 的长时间等待超时问题
"""

import asyncio
import uuid
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from .xiaohongshu_login import XiaohongshuLogin
from ..browser.browser_manager import BrowserManager
from ..storage.cookie_storage import CookieStorage
from .login_types import LoginStatus


class LoginSession:
    """登录会话"""
    
    def __init__(self, session_id: str, login_manager: XiaohongshuLogin):
        self.session_id = session_id
        self.login_manager = login_manager
        self.created_at = datetime.now()
        self.last_check = datetime.now()
        self.status = "waiting"  # waiting, logged_in, failed, expired
        self.message = "等待登录中"
        self.cookies_saved = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def check_status(self) -> Tuple[str, str, bool]:
        """检查登录状态"""
        try:
            self.last_check = datetime.now()
            
            # 检查是否已登录
            logged_in = await self.login_manager.is_logged_in(navigate=False)
            
            if logged_in:
                self.status = "logged_in"
                self.message = "登录成功"
                # 保存 cookies
                try:
                    await self.login_manager.save_cookies()
                    self.cookies_saved = True
                except Exception as e:
                    logger.warning(f"保存 cookies 失败: {e}")
                    
            return self.status, self.message, self.cookies_saved
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            self.status = "failed"
            self.message = f"检查失败: {str(e)}"
            return self.status, self.message, False
    
    async def cleanup(self, save_cookies: bool = True):
        """
        清理会话资源
        
        Args:
            save_cookies: 是否保存cookies，默认为True
        """
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
            await self.login_manager.cleanup(save_cookies=save_cookies)
        except Exception as e:
            logger.error(f"清理登录会话失败: {e}")
    
    def is_expired(self, timeout_minutes: int = 10) -> bool:
        """检查会话是否过期"""
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)


class LoginSessionManager:
    """登录会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, LoginSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期清理任务失败: {e}")
    
    async def _cleanup_expired_sessions(self):
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.remove_session(session_id)
            logger.info(f"清理过期登录会话: {session_id}")
        
        return len(expired_sessions)
    
    async def cleanup_expired_sessions(self):
        """公开的清理过期会话方法"""
        return await self._cleanup_expired_sessions()
    
    async def create_session(self, headless: bool = False, fresh: bool = True, wait_for_completion: bool = False, username: Optional[str] = None) -> str:
        """
        创建新的登录会话（每个会话使用独立的浏览器实例）
        
        Args:
            headless: 是否无头模式
            fresh: 是否清空cookies
            wait_for_completion: 是否等待登录完成（阻塞模式），默认False（后台异步）
            username: 用户名（用于创建独立的cookie文件），如果为None则使用session_id
        
        Returns:
            会话ID
        """
        session_id = str(uuid.uuid4())
        
        try:
            # 为每个会话创建独立的浏览器管理器和Cookie存储
            # 如果提供了用户名，使用用户名作为cookie文件名；否则使用session_id
            if username:
                cookie_path = f"cookies_{username}.json"
            else:
                cookie_path = f"cookies_{session_id}.json"
            
            cookie_storage = CookieStorage(cookie_path)
            browser_manager = BrowserManager(
                browser_type="chromium", 
                headless=headless,
                cookie_storage=cookie_storage
            )
            login_manager = XiaohongshuLogin(browser_manager, cookie_storage)
            
            # 创建会话对象（状态为initializing）
            session = LoginSession(session_id, login_manager)
            session.status = "initializing"
            session.message = "正在初始化浏览器..."
            self.sessions[session_id] = session
            
            if wait_for_completion:
                # 同步等待模式：直接执行初始化，阻塞直到登录完成
                logger.info(f"创建登录会话: {session_id} (同步等待模式，独立浏览器)")
                await self._initialize_session_async(session_id, fresh)
            else:
                # 异步模式：启动后台初始化任务
                asyncio.create_task(self._initialize_session_async(session_id, fresh))
                logger.info(f"创建登录会话: {session_id} (后台初始化中，独立浏览器)")
            
            return session_id
            
        except Exception as e:
            logger.error(f"创建登录会话失败: {e}")
            raise

    async def _initialize_session_async(self, session_id: str, fresh: bool = True):
        """后台异步初始化会话"""
        session = self.sessions.get(session_id)
        if not session:
            return
            
        try:
            # 初始化登录管理器
            session.status = "initializing"
            session.message = "正在启动浏览器..."
            
            # 确保浏览器有效，如果无效则重启
            try:
                await session.login_manager.initialize()
            except Exception as e:
                error_msg = str(e)
                if "浏览器已关闭" in error_msg or "需要重新初始化" in error_msg:
                    logger.warning(f"会话 {session_id}: 浏览器已关闭，尝试重启")
                    # 在fresh模式下重启时不加载cookies
                    await session.login_manager.browser_manager.restart(load_cookies=not fresh)
                    await session.login_manager.initialize()
                    logger.info(f"会话 {session_id}: 浏览器重启后重新初始化成功")
                else:
                    raise
            
            # 检查是否已有有效的登录状态（仅在非fresh模式时）
            if not fresh:
                try:
                    session.message = "正在检查登录状态..."
                    # 导航到网站检查登录状态
                    if await session.login_manager.is_logged_in(navigate=True):
                        session.status = "logged_in"
                        session.message = "已登录，无需重新登录"
                        logger.info(f"会话 {session_id}: 检测到已有登录状态，跳过登录流程")
                        return
                except Exception as e:
                    logger.warning(f"会话 {session_id}: 检查登录状态失败: {e}")
            
            # fresh 模式：清空 cookies（每个会话独立，可以安全清空）
            if fresh:
                try:
                    session.message = "正在清空cookies..."
                    session.login_manager.cookie_storage.clear_cookies()
                    page = await session.login_manager.browser_manager.get_page()
                    await page.context.clear_cookies()
                    logger.info(f"会话 {session_id}: 已清空 cookies")
                except Exception as ce:
                    logger.warning(f"会话 {session_id}: 清空 cookies 失败: {ce}")
            
            # 打开登录弹窗
            try:
                session.message = "正在打开登录弹窗..."
                await session.login_manager.open_login_modal()
                session.status = "waiting"
                session.message = "请扫描二维码登录"
                logger.info(f"会话 {session_id}: 已打开登录弹窗")
            except Exception as e:
                error_msg = str(e)
                if "浏览器已关闭" in error_msg or "需要重新初始化" in error_msg:
                    logger.warning(f"会话 {session_id}: 打开登录弹窗时浏览器已关闭，尝试重启")
                    # 在fresh模式下重启时不加载cookies
                    await session.login_manager.browser_manager.restart(load_cookies=not fresh)
                    await session.login_manager.initialize()
                    await session.login_manager.open_login_modal()
                    session.status = "waiting"
                    session.message = "请扫描二维码登录"
                    logger.info(f"会话 {session_id}: 浏览器重启后成功打开登录弹窗")
                else:
                    session.status = "failed"
                    session.message = f"打开登录弹窗失败: {str(e)}"
                    logger.warning(f"会话 {session_id}: 打开登录弹窗失败: {e}")
                    return
            
            # 阻塞等待登录完成（登录框消失且"我的"按钮出现）
            try:
                session.status = "waiting"
                session.message = "等待登录完成..."
                logger.info(f"会话 {session_id}: 开始阻塞等待登录完成（超时90秒）")
                
                # 调用 wait_for_login，阻塞直到登录框消失且"我的"按钮出现
                success, message, cookies_saved = await session.login_manager.wait_for_login(
                    timeout=90
                )
                
                if success:
                    session.status = "logged_in"
                    session.message = message
                    session.cookies_saved = cookies_saved
                    logger.info(f"会话 {session_id}: 登录成功")
                else:
                    session.status = "failed"
                    session.message = message
                    logger.warning(f"会话 {session_id}: 登录失败 - {message}")
                    
            except Exception as e:
                session.status = "failed"
                session.message = f"等待登录过程中出错: {str(e)}"
                logger.error(f"会话 {session_id}: 等待登录过程中出错: {e}")
            
        except Exception as e:
            session.status = "failed"
            session.message = f"初始化失败: {str(e)}"
            logger.error(f"会话 {session_id} 初始化失败: {e}")
    
    async def check_session(self, session_id: str) -> Optional[Tuple[str, str, bool]]:
        """检查会话登录状态"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if session.is_expired():
            await self.remove_session(session_id)
            return None
        
        # 如果还在初始化中，直接返回当前状态
        if session.status == "initializing":
            return session.status, session.message, False
        
        return await session.check_status()
    
    async def remove_session(self, session_id: str, save_cookies: bool = True):
        """
        移除会话（每个会话独立，清理时会关闭浏览器）
        
        Args:
            session_id: 会话ID
            save_cookies: 是否保存cookies，默认为True
        """
        session = self.sessions.get(session_id)
        if session:
            await session.cleanup(save_cookies=save_cookies)
            del self.sessions[session_id]
            logger.info(f"移除登录会话: {session_id}（浏览器已关闭）")
    
    async def cleanup_all(self, save_cookies: bool = True):
        """
        清理所有会话（每个会话独立，清理时会关闭各自的浏览器）
        
        Args:
            save_cookies: 是否保存cookies，默认为True
        """
        for session_id in list(self.sessions.keys()):
            await self.remove_session(session_id, save_cookies=save_cookies)
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


# 全局会话管理器实例
_session_manager: Optional[LoginSessionManager] = None

def get_session_manager() -> LoginSessionManager:
    """获取全局会话管理器实例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = LoginSessionManager()
    return _session_manager