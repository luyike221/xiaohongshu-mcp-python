"""
用户会话管理器：用户与会话映射（user_sessions.json）+ 登录会话流程。
是否已登录以持久化 Chrome profile 内真实会话为准；user_sessions 仅作辅助记录。
"""

import asyncio
import shutil
import time
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from ..storage.user_session_storage import UserSessionStorage
from ..auth.login_session_manager import LoginSessionManager
from ..browser.profile_paths import resolve_profile_user_data_dir
from ..config.settings import Settings


_PROFILE_LOGIN_CACHE: Dict[str, Tuple[float, bool]] = {}
_PROFILE_LOGIN_CACHE_TTL_SEC = 90.0


class UserSessionManager:
    """用户会话管理器"""

    def __init__(self, storage_path: Optional[str] = None):
        self.user_storage = UserSessionStorage(storage_path)
        self.login_session_manager = LoginSessionManager()

    def invalidate_profile_login_cache(self, username: str) -> None:
        _PROFILE_LOGIN_CACHE.pop(username, None)

    async def is_logged_in_via_persistent_profile(self, username: str) -> bool:
        """用该用户对应 User Data 启动浏览器并在小红书页做 DOM 校验（带短 TTL 缓存）。"""
        now = time.monotonic()
        cached = _PROFILE_LOGIN_CACHE.get(username)
        if cached and (now - cached[0]) < _PROFILE_LOGIN_CACHE_TTL_SEC:
            return cached[1]

        from ..browser.browser_manager import BrowserManager
        from ..auth.xiaohongshu_login import XiaohongshuLogin

        browser_manager = BrowserManager(
            headless=Settings.BROWSER_HEADLESS,
            profile_user=username,
        )
        ok = False
        try:
            await browser_manager.start()
            await asyncio.sleep(0.35)
            login = XiaohongshuLogin(browser_manager)
            ok = await login.is_logged_in(navigate=True)
        except Exception as e:
            logger.warning(f"校验用户 {username} 的 profile 登录态失败: {e}")
            ok = False
        finally:
            try:
                await browser_manager.stop()
            except Exception:
                pass

        _PROFILE_LOGIN_CACHE[username] = (time.monotonic(), ok)
        if ok:
            logger.info(f"用户 {username} 在持久化 profile 中校验为已登录")
        else:
            logger.info(f"用户 {username} 在持久化 profile 中校验为未登录")
        return ok

    async def get_or_create_session(
        self,
        username: str,
        headless: bool = True,
        wait_for_completion: bool = False,
        fresh: bool = True,
    ) -> Dict[str, Any]:
        logger.info(f"为用户 {username} 获取或创建会话（基于持久化浏览器 profile）")

        session_status = await self.get_user_session_status(username)

        if session_status and session_status.get("status") == "logged_in":
            logger.info(f"用户 {username} 已通过持久化 profile 校验为已登录")
            return {
                "session_id": f"profile_session_{username}",
                "status": "logged_in",
                "is_new": False,
                "message": "使用本地浏览器 profile，已登录",
                "cookies_saved": True,
            }

        if session_status and session_status.get("status") == "expired":
            logger.info(f"用户 {username} 的会话记录已过期，将创建新会话")
        else:
            logger.info(f"用户 {username} 无有效会话记录，将创建新会话")

        session_id = await self.login_session_manager.create_session(
            headless=headless,
            fresh=fresh,
            wait_for_completion=wait_for_completion,
            username=username,
        )

        if session_id:
            if wait_for_completion:
                sess = self.login_session_manager.sessions.get(session_id)
                logged_in = sess is not None and sess.status == "logged_in"
                if logged_in:
                    success = await self.user_storage.set_user_session(username, session_id)
                    if not success:
                        await self.login_session_manager.remove_session(session_id)
                        return {"error": "保存用户会话映射失败"}
                    logger.info(f"成功为用户 {username} 创建登录会话")
                    try:
                        login_session = self.login_session_manager.sessions.get(session_id)
                        if login_session:
                            await login_session.cleanup(save_cookies=True)
                            logger.info(f"已关闭用户 {username} 的浏览器实例")
                    except Exception as e:
                        logger.warning(f"关闭浏览器实例时出错: {e}")

                    return {
                        "session_id": session_id,
                        "status": "logged_in",
                        "is_new": True,
                        "message": "登录成功，会话已写入浏览器 profile",
                        "cookies_saved": True,
                    }

                try:
                    login_session = self.login_session_manager.sessions.get(session_id)
                    if login_session:
                        await login_session.cleanup(save_cookies=False)
                        logger.info(f"登录失败，已关闭用户 {username} 的浏览器实例")
                except Exception as e:
                    logger.warning(f"关闭浏览器实例时出错: {e}")

                return {
                    "session_id": session_id,
                    "status": "failed",
                    "is_new": True,
                    "message": "登录失败或超时",
                    "cookies_saved": False,
                }

            success = await self.user_storage.set_user_session(username, session_id)
            if success:
                logger.info(f"成功为用户 {username} 创建登录会话 {session_id}")
                return {
                    "session_id": session_id,
                    "status": "waiting",
                    "is_new": True,
                    "message": f"创建新登录会话 {session_id}，请扫描二维码登录",
                }

            logger.error(f"保存用户 {username} 的会话映射失败")
            await self.login_session_manager.remove_session(session_id)
            return {"error": "保存用户会话映射失败"}

        logger.error(f"为用户 {username} 创建会话失败")
        return {"error": "创建会话失败"}

    async def get_user_session_status(self, username: str) -> Optional[Dict[str, Any]]:
        if not await self.is_logged_in_via_persistent_profile(username):
            logger.info(f"用户 {username} 持久化 profile 中未检测到已登录")
            return None

        data = await self.user_storage.load_user_sessions()
        if username not in data:
            await self.user_storage.set_user_session(
                username,
                f"profile_session_{username}",
                expires_in_hours=24 * 365,
            )
        else:
            await self.user_storage.update_last_accessed(username)

        return {
            "status": "logged_in",
            "message": "登录状态有效（持久化 Chrome profile）",
            "logged_in": True,
            "cookies_saved": True,
        }

    async def cleanup_user_session(self, username: str) -> bool:
        logger.info(f"清理用户 {username} 的会话")

        user_session = await self.user_storage.get_user_session(username)

        if user_session:
            session_id = user_session["session_id"]
            if not session_id.startswith("profile_session_"):
                await self.login_session_manager.remove_session(session_id, save_cookies=False)
            await self.user_storage.remove_user_session(username)
            logger.info(f"成功清理用户 {username} 的会话记录")
        else:
            logger.info(f"用户 {username} 没有需要清理的会话记录")

        try:
            sub = resolve_profile_user_data_dir(username)
            if sub.exists():
                shutil.rmtree(sub, ignore_errors=True)
                logger.info(f"已删除用户 {username} 的浏览器 profile 目录: {sub}")
        except Exception as e:
            logger.error(f"删除 profile 目录时出错: {e}")
            return False

        self.invalidate_profile_login_cache(username)
        logger.info(f"用户 {username} 的会话清理完成")
        return True

    async def cleanup_all_expired_sessions(self) -> Dict[str, int]:
        logger.info("开始清理所有过期会话")
        expired_user_sessions = await self.user_storage.cleanup_expired_sessions()
        expired_login_sessions = await self.login_session_manager.cleanup_expired_sessions()
        result = {
            "expired_user_sessions": expired_user_sessions,
            "expired_login_sessions": expired_login_sessions,
        }
        logger.info(f"清理完成: {result}")
        return result

    async def list_all_user_sessions(self) -> Dict[str, Any]:
        user_sessions = await self.user_storage.load_user_sessions()
        enriched_sessions = {}

        for username, session_info in user_sessions.items():
            session_id = session_info["session_id"]
            if session_id.startswith("profile_session_"):
                current = "logged_in"
            else:
                st = await self.login_session_manager.check_session(session_id)
                current = st[0] if st else "invalid"

            enriched_sessions[username] = {
                **session_info,
                "current_status": current,
            }

        return enriched_sessions

    def get_storage_info(self) -> Dict[str, Any]:
        return self.user_storage.get_storage_info()


_global_user_session_manager: Optional[UserSessionManager] = None


def get_user_session_manager() -> UserSessionManager:
    global _global_user_session_manager
    if _global_user_session_manager is None:
        _global_user_session_manager = UserSessionManager()
    return _global_user_session_manager
