"""
用户会话管理器

集成用户会话存储和登录会话管理，提供基于用户的会话管理功能。
"""

from typing import Optional, Dict, Any
from loguru import logger

from ..storage.user_session_storage import UserSessionStorage
from ..xiaohongshu.login_session_manager import LoginSessionManager


class UserSessionManager:
    """用户会话管理器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化用户会话管理器
        
        Args:
            storage_path: 用户会话存储文件路径
        """
        self.user_storage = UserSessionStorage(storage_path)
        self.login_session_manager = LoginSessionManager()
        
    async def get_or_create_session(self, username: str, 
                                   headless: bool = True) -> Dict[str, Any]:
        """
        获取或创建用户会话
        
        Args:
            username: 用户名
            headless: 是否使用无头模式
        
        Returns:
            会话信息字典，包含session_id和状态
        """
        logger.info(f"为用户 {username} 获取或创建会话")
        
        # 1. 检查是否存在有效的用户会话
        existing_session = await self.user_storage.get_user_session(username)
        
        if existing_session:
            session_id = existing_session["session_id"]
            logger.info(f"找到用户 {username} 的现有会话: {session_id}")
            
            # 2. 检查会话是否仍然有效
            session_status = await self.login_session_manager.check_session(session_id)
            
            if session_status and session_status[0] in ["waiting", "logged_in"]:
                # 会话仍然有效，更新最后访问时间
                await self.user_storage.update_last_accessed(username)
                logger.info(f"用户 {username} 的会话 {session_id} 仍然有效，状态: {session_status[0]}")
                
                # 根据实际状态返回相应的消息
                if session_status[0] == "logged_in":
                    message = f"用户已登录，使用现有会话 {session_id}"
                else:
                    message = f"使用现有会话 {session_id}"
                
                return {
                    "session_id": session_id,
                    "status": session_status[0],
                    "is_new": False,
                    "message": message
                }
            else:
                # 会话已失效，清理存储
                logger.info(f"用户 {username} 的会话 {session_id} 已失效，将创建新会话")
                await self.user_storage.remove_user_session(username)
                # 清理失效的登录会话
                await self.login_session_manager.remove_session(session_id)
        
        # 3. 创建新会话
        logger.info(f"为用户 {username} 创建新会话")
        session_id = await self.login_session_manager.create_session(headless=headless)
        
        if session_id:
            # 4. 保存用户会话映射
            success = await self.user_storage.set_user_session(username, session_id)
            
            if success:
                logger.info(f"成功为用户 {username} 创建并保存会话 {session_id}")
                return {
                    "session_id": session_id,
                    "status": "initializing",
                    "is_new": True,
                    "message": f"创建新会话 {session_id}"
                }
            else:
                logger.error(f"保存用户 {username} 的会话映射失败")
                # 清理创建的会话
                await self.login_session_manager.remove_session(session_id)
                return {
                    "error": "保存用户会话映射失败"
                }
        else:
            logger.error(f"为用户 {username} 创建会话失败")
            return {
                "error": "创建会话失败"
            }
    
    async def get_user_session_status(self, username: str) -> Optional[Dict[str, Any]]:
        """
        获取用户会话状态
        
        Args:
            username: 用户名
        
        Returns:
            会话状态信息，如果不存在则返回None
        """
        # 1. 获取用户会话信息
        user_session = await self.user_storage.get_user_session(username)
        
        if not user_session:
            logger.info(f"用户 {username} 没有活跃会话")
            return None
        
        session_id = user_session["session_id"]
        
        # 2. 获取登录会话状态
        session_status = await self.login_session_manager.check_session(session_id)
        
        if not session_status:
            # 会话不存在，清理用户会话映射
            logger.info(f"用户 {username} 的会话 {session_id} 不存在，清理映射")
            await self.user_storage.remove_user_session(username)
            return None
        
        # 3. 更新最后访问时间
        await self.user_storage.update_last_accessed(username)
        
        return {
            "session_id": session_id,
            "status": session_status[0],
            "message": session_status[1],
            "cookies_saved": session_status[2],
            "user_info": user_session,
            "logged_in": session_status[0] == "logged_in",
            "initializing": session_status[0] == "initializing"
        }
    
    async def cleanup_user_session(self, username: str) -> bool:
        """
        清理用户会话
        
        Args:
            username: 用户名
        
        Returns:
            是否清理成功
        """
        logger.info(f"清理用户 {username} 的会话")
        
        # 1. 获取用户会话信息
        user_session = await self.user_storage.get_user_session(username)
        
        if user_session:
            session_id = user_session["session_id"]
            
            # 2. 清理登录会话（不保存Cookie）
            await self.login_session_manager.remove_session(session_id, save_cookies=False)
            
            # 3. 清理 cookie 文件（在关闭浏览器之后）
            try:
                from ..storage.cookie_storage import CookieStorage
                cookie_storage = CookieStorage()
                cookie_storage.clear_cookies()
                logger.info(f"成功清理用户 {username} 的 cookie 文件")
            except Exception as e:
                logger.warning(f"清理 cookie 文件失败: {e}")
            
            # 4. 清理用户会话映射
            await self.user_storage.remove_user_session(username)
            
            # 5. 如果没有其他活跃会话，清理共享浏览器
            try:
                remaining_sessions = await self.user_storage.load_user_sessions()
                if not remaining_sessions:
                    # 没有其他用户会话，可以安全关闭共享浏览器（不保存Cookie）
                    await self.login_session_manager.cleanup_all(save_cookies=False)
                    logger.info(f"已清理共享浏览器资源")
            except Exception as e:
                logger.warning(f"清理共享浏览器失败: {e}")
            
            logger.info(f"成功清理用户 {username} 的会话 {session_id}")
            return True
        else:
            logger.info(f"用户 {username} 没有需要清理的会话")
            return True
    
    async def cleanup_all_expired_sessions(self) -> Dict[str, int]:
        """
        清理所有过期的会话
        
        Returns:
            清理统计信息
        """
        logger.info("开始清理所有过期会话")
        
        # 1. 清理用户会话存储中的过期会话
        expired_user_sessions = await self.user_storage.cleanup_expired_sessions()
        
        # 2. 清理登录会话管理器中的过期会话
        expired_login_sessions = await self.login_session_manager.cleanup_expired_sessions()
        
        result = {
            "expired_user_sessions": expired_user_sessions,
            "expired_login_sessions": expired_login_sessions
        }
        
        logger.info(f"清理完成: {result}")
        return result
    
    async def list_all_user_sessions(self) -> Dict[str, Any]:
        """
        列出所有用户会话
        
        Returns:
            所有用户会话信息
        """
        user_sessions = await self.user_storage.load_user_sessions()
        
        # 为每个用户会话添加实时状态信息
        enriched_sessions = {}
        
        for username, session_info in user_sessions.items():
            session_id = session_info["session_id"]
            session_status = await self.login_session_manager.check_status(session_id)
            
            enriched_sessions[username] = {
                **session_info,
                "current_status": session_status.get("status") if session_status else "invalid"
            }
        
        return enriched_sessions
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储信息
        
        Returns:
            存储信息
        """
        return self.user_storage.get_storage_info()