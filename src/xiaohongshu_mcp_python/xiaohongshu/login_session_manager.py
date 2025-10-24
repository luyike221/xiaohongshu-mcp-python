"""
登录会话管理器
用于支持会话化的短轮询登录流程，避免 MCP Inspector 的长时间等待超时问题
"""

import asyncio
import uuid
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from .simple_login_manager import SimpleLoginManager
from ..browser.browser_manager import BrowserManager
from ..storage.cookie_storage import CookieStorage
from .login_types import LoginStatus


class LoginSession:
    """登录会话"""
    
    def __init__(self, session_id: str, login_manager: SimpleLoginManager):
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
    
    async def cleanup(self):
        """清理会话资源"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
            await self.login_manager.cleanup()
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
        # 共享的浏览器管理器和Cookie存储，避免每次创建新实例
        self._shared_cookie_storage: Optional[CookieStorage] = None
        self._shared_browser_manager: Optional[BrowserManager] = None
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
    
    def _get_shared_instances(self, headless: bool = False):
        """获取共享的浏览器管理器和Cookie存储实例"""
        if self._shared_cookie_storage is None:
            self._shared_cookie_storage = CookieStorage("cookies.json")
        
        if self._shared_browser_manager is None:
            self._shared_browser_manager = BrowserManager(
                browser_type="chromium", 
                headless=headless,
                cookie_storage=self._shared_cookie_storage
            )
        
        return self._shared_browser_manager, self._shared_cookie_storage
    
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
    
    async def create_session(self, headless: bool = False, fresh: bool = True) -> str:
        """创建新的登录会话（快速返回，后台初始化）"""
        session_id = str(uuid.uuid4())
        
        try:
            # 使用共享的浏览器管理器和Cookie存储
            browser_manager, cookie_storage = self._get_shared_instances(headless)
            login_manager = SimpleLoginManager(browser_manager, cookie_storage, shared_browser=True)
            
            # 创建会话对象（状态为initializing）
            session = LoginSession(session_id, login_manager)
            session.status = "initializing"
            session.message = "正在初始化浏览器..."
            self.sessions[session_id] = session
            
            # 启动后台初始化任务
            asyncio.create_task(self._initialize_session_async(session_id, fresh))
            
            logger.info(f"创建登录会话: {session_id} (后台初始化中)")
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
            session.message = "正在启动浏览器..."
            await session.login_manager.initialize()
            
            # 检查是否已有有效的登录状态（仅在非fresh模式或共享浏览器时）
            if not fresh or self._shared_browser_manager:
                try:
                    session.message = "正在检查登录状态..."
                    if await session.login_manager.is_logged_in(navigate=True):
                        session.status = "logged_in"
                        session.message = "已登录，无需重新登录"
                        logger.info(f"会话 {session_id}: 检测到已有登录状态，跳过登录流程")
                        return
                except Exception as e:
                    logger.warning(f"会话 {session_id}: 检查登录状态失败: {e}")
            
            # fresh 模式：清空 cookies（仅在非共享浏览器时）
            if fresh and not self._shared_browser_manager:
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
                session.status = "failed"
                session.message = f"打开登录弹窗失败: {str(e)}"
                logger.warning(f"会话 {session_id}: 打开登录弹窗失败: {e}")
            
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
    
    async def remove_session(self, session_id: str):
        """移除会话"""
        session = self.sessions.get(session_id)
        if session:
            await session.cleanup()
            del self.sessions[session_id]
            logger.info(f"移除登录会话: {session_id}")
    
    async def cleanup_all(self):
        """清理所有会话"""
        for session_id in list(self.sessions.keys()):
            await self.remove_session(session_id)
        
        # 清理共享的浏览器管理器
        if self._shared_browser_manager and self._shared_browser_manager.is_started():
            await self._shared_browser_manager.stop()
            self._shared_browser_manager = None
            self._shared_cookie_storage = None
        
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