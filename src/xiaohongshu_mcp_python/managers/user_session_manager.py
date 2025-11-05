"""
用户会话管理器

集成用户会话存储和登录会话管理，提供基于用户的会话管理功能。
"""

import asyncio
from typing import Optional, Dict, Any
from loguru import logger

from ..storage.user_session_storage import UserSessionStorage
from ..auth.login_session_manager import LoginSessionManager


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
                                   headless: bool = True,
                                   wait_for_completion: bool = False) -> Dict[str, Any]:
        """
        获取或创建用户会话（基于本地 cookies）
        
        Args:
            username: 用户名
            headless: 是否使用无头模式
            wait_for_completion: 是否等待登录完成（阻塞模式），默认False
        
        Returns:
            会话信息字典，包含session_id和状态
        """
        logger.info(f"为用户 {username} 获取或创建会话（基于本地 cookies）")
        
        # 1. 检查本地 cookies 是否存在且有效
        session_status = await self.get_user_session_status(username)
        
        if session_status and session_status.get("status") == "logged_in":
            # 本地 cookies 有效，直接返回已登录状态
            logger.info(f"用户 {username} 的本地 cookies 有效，已登录")
            return {
                "session_id": f"cookie_based_{username}",  # 使用基于 cookies 的标识
                "status": "logged_in",
                "is_new": False,
                "message": "使用本地 cookies，已登录",
                "cookies_saved": True
            }
        
        # 2. cookies 不存在或已失效，需要创建新登录会话
        if session_status and session_status.get("status") == "expired":
            logger.info(f"用户 {username} 的登录已失效，将创建新会话")
        else:
            logger.info(f"用户 {username} 没有有效的 cookies，将创建新会话")
        
        # 3. 创建新登录会话
        session_id = await self.login_session_manager.create_session(
            headless=headless,
            wait_for_completion=wait_for_completion,
            username=username
        )
        
        if session_id:
            # 4. 保存用户会话映射（用于跟踪登录流程）
            success = await self.user_storage.set_user_session(username, session_id)
            
            if success:
                # 如果等待完成，检查最终的登录状态
                if wait_for_completion:
                    # 再次检查本地 cookies（登录完成后应该已保存）
                    final_status = await self.get_user_session_status(username)
                    if final_status and final_status.get("status") == "logged_in":
                        logger.info(f"成功为用户 {username} 创建登录会话并保存 cookies")
                        
                        # 登录成功后关闭浏览器实例（再次保存cookies以确保不丢失）
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
                            "message": "登录成功，cookies 已保存",
                            "cookies_saved": True
                        }
                    else:
                        # 登录失败或超时，也需要关闭浏览器实例（不保存cookies，因为登录失败）
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
                            "cookies_saved": False
                        }
                
                logger.info(f"成功为用户 {username} 创建登录会话 {session_id}")
                return {
                    "session_id": session_id,
                    "status": "waiting",
                    "is_new": True,
                    "message": f"创建新登录会话 {session_id}，请扫描二维码登录"
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
    
    async def _check_login_expired(self, username: str) -> bool:
        """
        检查登录是否失效（通过 XPath 判断）
        
        Args:
            username: 用户名
        
        Returns:
            如果登录失效返回 True，否则返回 False
        """
        try:
            from ..storage.cookie_storage import CookieStorage
            from ..browser import BrowserManager
            
            # 创建 cookie 存储
            cookie_storage = CookieStorage(f"cookies_{username}.json")
            
            # 如果 cookies 文件不存在，直接返回失效
            if not cookie_storage.has_cookies():
                logger.info(f"用户 {username} 的 cookies 文件不存在")
                return True
            
            # 创建临时浏览器实例检查登录状态
            browser_manager = BrowserManager(cookie_storage=cookie_storage)
            await browser_manager.start()
            
            try:
                page = await browser_manager.get_page()
                
                # 导航到小红书主页
                await page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=30000)
                
                # 等待页面加载，但不强制等待 networkidle（可能超时）
                # 使用更宽松的等待策略
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    # 如果 networkidle 超时，继续等待页面基本加载完成
                    logger.debug(f"等待 networkidle 超时，继续检查登录状态")
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)
                
                # 等待页面稳定
                await asyncio.sleep(1)
                
                # 首先进行正向检查：检查是否存在"我"的链接（已登录标识）
                # 如果存在，说明已登录，直接返回 False（未失效）
                try:
                    user_link_xpath = "//ul/div[contains(@class, 'channel-list-content')]/li//a[normalize-space(.)=\"我\"][contains(@class, 'link-wrapper')]"
                    user_link = page.locator(user_link_xpath)
                    await user_link.wait_for(state="visible", timeout=2000)
                    logger.info(f"检测到'我'的链接，用户 {username} 已登录")
                    return False  # 已登录，未失效
                except Exception:
                    pass
                
                # 正向检查失败，进行负向检查：检查登录失效的多个条件
                # 如果检测到任意一个未登录标识，说明登录失效
                
                # 1. 检查登录失效标识: //div[@class="css-jjnw1w"]
                try:
                    expired_element = page.locator('//div[@class="css-jjnw1w"]')
                    await expired_element.wait_for(state="visible", timeout=2000)
                    logger.warning(f"检测到登录失效标识（css-jjnw1w），用户 {username} 的登录已失效")
                    return True
                except Exception:
                    pass
                
                # 2. 检查登录按钮: //ul//button[normalize-space(.)="登录"]
                try:
                    login_button = page.locator('//ul//button[normalize-space(.)="登录"]')
                    await login_button.wait_for(state="visible", timeout=2000)
                    logger.warning(f"检测到登录按钮，用户 {username} 未登录")
                    return True
                except Exception:
                    pass
                
                # 3. 检查登录容器右侧: //div[@class="login-container"]/div[3][@class="right"]
                try:
                    login_container = page.locator('//div[@class="login-container"]/div[3][@class="right"]')
                    await login_container.wait_for(state="visible", timeout=2000)
                    logger.warning(f"检测到登录容器右侧元素，用户 {username} 未登录")
                    return True
                except Exception:
                    pass
                
                # 所有检查都未通过，说明登录状态不确定
                # 保守处理：不删除 cookies，返回 False（认为未失效）
                logger.warning(f"无法确定用户 {username} 的登录状态，保持 cookies 不变")
                return False
                    
            finally:
                await browser_manager.stop(save_cookies=False)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"检查登录状态时出错: {e}")
            
            # 如果是超时错误，可能是页面加载慢，但 cookies 可能仍然有效
            # 如果是其他错误（如网络错误），也不应该直接删除 cookies
            # 但在 cookies 文件已被清理的情况下，应该返回 True（失效）
            # 检查 cookies 文件是否还存在
            try:
                from ..storage.cookie_storage import CookieStorage
                cookie_storage = CookieStorage(f"cookies_{username}.json")
                if not cookie_storage.has_cookies():
                    # cookies 文件不存在，说明已被清理，返回 True（失效）
                    logger.info(f"用户 {username} 的 cookies 文件不存在（可能已被清理），返回失效")
                    return True
            except Exception:
                pass
            
            # cookies 文件存在但检查出错，保守处理：不删除 cookies，返回 False（认为未失效）
            # 这样可以避免因为网络问题、超时等问题误删有效的 cookies
            logger.warning(f"检查登录状态出错，但 cookies 文件存在，保持用户 {username} 的 cookies 不变")
            return False
    
    async def get_user_session_status(self, username: str) -> Optional[Dict[str, Any]]:
        """
        获取用户会话状态（基于本地 cookies 文件）
        
        Args:
            username: 用户名
        
        Returns:
            会话状态信息，如果不存在则返回None
        """
        from ..storage.cookie_storage import CookieStorage
        
        # 1. 检查本地 cookies 文件是否存在
        cookie_storage = CookieStorage(f"cookies_{username}.json")
        
        if not cookie_storage.has_cookies():
            logger.info(f"用户 {username} 的本地 cookies 文件不存在")
            return None
        
        logger.info(f"用户 {username} 的本地 cookies 文件存在，检查登录状态")
        
        # 2. 检查登录是否失效
        is_expired = await self._check_login_expired(username)
        
        if is_expired:
            # 登录失效，清空本地数据
            logger.info(f"用户 {username} 的登录已失效，清空本地数据")
            cookie_storage.clear_cookies()
            await self.user_storage.remove_user_session(username)
            
            return {
                "success": False,
                "status": "expired",
                "message": "登录已失效，请重新登录",
                "error": "LOGIN_EXPIRED"
            }
        
        # 3. 登录有效，返回成功状态
        logger.info(f"用户 {username} 的登录状态有效")
        await self.user_storage.update_last_accessed(username)
        
        return {
            "status": "logged_in",
            "message": "登录状态有效",
            "logged_in": True,
            "cookies_saved": True
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
            
            # 3. 清理用户会话映射
            await self.user_storage.remove_user_session(username)
            
            logger.info(f"成功清理用户 {username} 的会话 {session_id}")
        else:
            logger.info(f"用户 {username} 没有需要清理的会话记录")
        
        # 4. 无论是否有会话记录，都要清理 cookie 文件
        try:
            from ..storage.cookie_storage import CookieStorage
            import os
            from pathlib import Path
            
            # 使用与保存时相同的路径逻辑
            cookie_filename = f"cookies_{username}.json"
            cookie_storage = CookieStorage(cookie_filename)
            
            # 获取实际的文件路径（可能是绝对路径或相对路径）
            cookie_path = cookie_storage.cookie_path
            logger.info(f"准备清理用户 {username} 的 cookie 文件: {cookie_path.absolute()}")
            
            if cookie_storage.has_cookies():
                success = cookie_storage.clear_cookies()
                if success:
                    # 验证文件是否真的被删除
                    if cookie_storage.has_cookies():
                        logger.error(f"清理后 cookie 文件仍然存在: {cookie_path.absolute()}")
                        return False
                    else:
                        logger.info(f"成功清理用户 {username} 的 cookie 文件: {cookie_path.absolute()}")
                else:
                    logger.warning(f"清理用户 {username} 的 cookie 文件失败")
                    return False
            else:
                logger.info(f"用户 {username} 的 cookie 文件不存在: {cookie_path.absolute()}")
        except Exception as e:
            logger.error(f"清理 cookie 文件时出错: {e}", exc_info=True)
            return False
        
        logger.info(f"用户 {username} 的会话清理完成")
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


# 全局用户会话管理器实例
_global_user_session_manager: Optional[UserSessionManager] = None


def get_user_session_manager() -> UserSessionManager:
    """获取全局用户会话管理器实例"""
    global _global_user_session_manager
    if _global_user_session_manager is None:
        _global_user_session_manager = UserSessionManager()
    return _global_user_session_manager