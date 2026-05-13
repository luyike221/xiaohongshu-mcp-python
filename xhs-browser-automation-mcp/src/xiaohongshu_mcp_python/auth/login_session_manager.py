"""
登录会话管理器：支持会话化短轮询登录流程。
每个会话使用独立持久化 User Data 目录（或有用户名时的 browser-profile-users）。
"""

import asyncio
import shutil
import uuid
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from .xiaohongshu_login import XiaohongshuLogin
from ..browser.browser_manager import BrowserManager
from ..browser.profile_paths import login_session_user_data_dir


class LoginSession:
    """登录会话"""

    def __init__(self, session_id: str, login_manager: XiaohongshuLogin):
        self.session_id = session_id
        self.login_manager = login_manager
        self.created_at = datetime.now()
        self.last_check = datetime.now()
        self.status = "waiting"
        self.message = "等待登录中"
        self.cookies_saved = False
        self._cleanup_task: Optional[asyncio.Task] = None

    async def check_status(self) -> Tuple[str, str, bool]:
        try:
            self.last_check = datetime.now()
            logged_in = await self.login_manager.is_logged_in(navigate=False)

            if logged_in:
                self.status = "logged_in"
                self.message = "登录成功"
                try:
                    await self.login_manager.save_cookies()
                    self.cookies_saved = True
                except Exception as e:
                    logger.warning(f"记录登录状态失败: {e}")

            return self.status, self.message, self.cookies_saved

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            self.status = "failed"
            self.message = f"检查失败: {str(e)}"
            return self.status, self.message, False

    async def cleanup(self, save_cookies: bool = True):
        """关闭浏览器。save_cookies 仅保留参数兼容。"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
            await self.login_manager.cleanup(save_cookies=save_cookies)
        except Exception as e:
            logger.error(f"清理登录会话失败: {e}")

    def is_expired(self, timeout_minutes: int = 10) -> bool:
        return datetime.now() - self.created_at > timedelta(minutes=timeout_minutes)


class LoginSessionManager:
    """登录会话管理器"""

    def __init__(self):
        self.sessions: Dict[str, LoginSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        while True:
            try:
                await asyncio.sleep(60)
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
        return await self._cleanup_expired_sessions()

    async def create_session(
        self,
        headless: bool = False,
        fresh: bool = True,
        wait_for_completion: bool = False,
        username: Optional[str] = None,
    ) -> str:
        session_id = str(uuid.uuid4())

        try:
            user_data_dir = login_session_user_data_dir(session_id, username)
            if fresh and user_data_dir.exists():
                shutil.rmtree(user_data_dir, ignore_errors=True)

            browser_manager = BrowserManager(
                browser_type="chromium",
                headless=headless,
                user_data_dir=user_data_dir,
            )
            login_manager = XiaohongshuLogin(browser_manager)

            session = LoginSession(session_id, login_manager)
            session.status = "initializing"
            session.message = "正在初始化浏览器..."
            self.sessions[session_id] = session

            if wait_for_completion:
                logger.info(f"创建登录会话: {session_id} (同步等待模式，独立浏览器)")
                await self._initialize_session_async(session_id, fresh)
            else:
                asyncio.create_task(self._initialize_session_async(session_id, fresh))
                logger.info(f"创建登录会话: {session_id} (后台初始化中，独立浏览器)")

            return session_id

        except Exception as e:
            logger.error(f"创建登录会话失败: {e}")
            raise

    async def _initialize_session_async(self, session_id: str, fresh: bool = True):
        session = self.sessions.get(session_id)
        if not session:
            return

        try:
            session.status = "initializing"
            session.message = "正在启动浏览器..."

            try:
                await session.login_manager.initialize()
            except Exception as e:
                error_msg = str(e)
                if "浏览器已关闭" in error_msg or "需要重新初始化" in error_msg:
                    logger.warning(f"会话 {session_id}: 浏览器已关闭，尝试重启")
                    await session.login_manager.browser_manager.restart(reset_profile=False)
                    await session.login_manager.initialize()
                    logger.info(f"会话 {session_id}: 浏览器重启后重新初始化成功")
                else:
                    raise

            if not fresh:
                try:
                    session.message = "正在检查登录状态..."
                    if await session.login_manager.is_logged_in(navigate=True):
                        session.status = "logged_in"
                        session.message = "已登录，无需重新登录"
                        logger.info(f"会话 {session_id}: 检测到已有登录状态，跳过登录流程")
                        return
                except Exception as e:
                    logger.warning(f"会话 {session_id}: 检查登录状态失败: {e}")

            if fresh:
                try:
                    session.message = "正在清空会话 Cookie..."
                    page = await session.login_manager.browser_manager.get_page()
                    await page.context.clear_cookies()
                    logger.info(f"会话 {session_id}: 已清空上下文 Cookie")
                except Exception as ce:
                    logger.warning(f"会话 {session_id}: 清空 Cookie 失败: {ce}")

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
                    await session.login_manager.browser_manager.restart(reset_profile=False)
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

            try:
                session.status = "waiting"
                session.message = "等待登录完成..."
                logger.info(f"会话 {session_id}: 开始阻塞等待登录完成（超时90秒）")

                success, message, cookies_saved = await session.login_manager.wait_for_login()

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
        session = self.sessions.get(session_id)
        if not session:
            return None

        if session.is_expired():
            await self.remove_session(session_id)
            return None

        if session.status == "initializing":
            return session.status, session.message, False

        return await session.check_status()

    async def remove_session(self, session_id: str, save_cookies: bool = True):
        session = self.sessions.get(session_id)
        if session:
            await session.cleanup(save_cookies=save_cookies)
            del self.sessions[session_id]
            logger.info(f"移除登录会话: {session_id}（浏览器已关闭）")

    async def cleanup_all(self, save_cookies: bool = True):
        for session_id in list(self.sessions.keys()):
            await self.remove_session(session_id, save_cookies=save_cookies)

        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None


_session_manager: Optional[LoginSessionManager] = None


def get_session_manager() -> LoginSessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = LoginSessionManager()
    return _session_manager
