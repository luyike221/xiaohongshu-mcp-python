"""
用户会话存储模块

使用文件模拟数据库，管理用户与会话的映射关系。
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from ..config.settings import get_project_root


class UserSessionStorage:
    """用户会话存储管理器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化用户会话存储
        
        Args:
            storage_path: 存储文件路径，如果为None则使用默认路径
        """
        self.storage_path = self._get_storage_path(storage_path)
        self._ensure_directory()
        
    def _get_storage_path(self, storage_path: Optional[str]) -> Path:
        """
        获取存储文件路径
        
        Args:
            storage_path: 指定的存储路径
        
        Returns:
            存储文件路径
        """
        if storage_path:
            return Path(storage_path)
        
        # 检查环境变量
        env_path = os.getenv("USER_SESSION_STORAGE_PATH")
        if env_path:
            return Path(env_path)
        
        # 默认使用项目根目录下的user_sessions.json
        project_root = get_project_root()
        return project_root / "user_sessions.json"
        
    def _ensure_directory(self) -> None:
        """确保存储文件的目录存在"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
    async def load_user_sessions(self) -> Dict[str, Any]:
        """
        加载用户会话数据
        
        Returns:
            用户会话数据字典
        """
        if not self.storage_path.exists():
            logger.info(f"用户会话存储文件不存在: {self.storage_path}")
            return {}
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"成功加载 {len(data)} 个用户会话记录")
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"用户会话存储文件格式错误: {e}")
            return {}
        except Exception as e:
            logger.error(f"加载用户会话数据失败: {e}")
            return {}
    
    async def save_user_sessions(self, data: Dict[str, Any]) -> bool:
        """
        保存用户会话数据
        
        Args:
            data: 用户会话数据字典
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功保存 {len(data)} 个用户会话记录到: {self.storage_path}")
            return True
        
        except Exception as e:
            logger.error(f"保存用户会话数据失败: {e}")
            return False
    
    async def get_user_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        获取指定用户的会话信息
        
        Args:
            username: 用户名
        
        Returns:
            用户会话信息，如果不存在则返回None
        """
        data = await self.load_user_sessions()
        user_session = data.get(username)
        
        if user_session:
            # 检查会话是否过期
            if self._is_session_expired(user_session):
                logger.info(f"用户 {username} 的会话已过期")
                await self.remove_user_session(username)
                return None
                
        return user_session
    
    async def set_user_session(self, username: str, session_id: str, 
                              expires_in_hours: int = 24) -> bool:
        """
        设置用户会话信息
        
        Args:
            username: 用户名
            session_id: 会话ID
            expires_in_hours: 过期时间（小时）
        
        Returns:
            是否设置成功
        """
        data = await self.load_user_sessions()
        
        # 计算过期时间
        expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).isoformat()
        
        data[username] = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "last_accessed": datetime.now().isoformat()
        }
        
        success = await self.save_user_sessions(data)
        if success:
            logger.info(f"为用户 {username} 设置会话 {session_id}，过期时间: {expires_at}")
        
        return success
    
    async def remove_user_session(self, username: str) -> bool:
        """
        移除用户会话信息
        
        Args:
            username: 用户名
        
        Returns:
            是否移除成功
        """
        data = await self.load_user_sessions()
        
        if username in data:
            del data[username]
            success = await self.save_user_sessions(data)
            if success:
                logger.info(f"已移除用户 {username} 的会话信息")
            return success
        
        return True  # 如果不存在，也认为是成功的
    
    async def update_last_accessed(self, username: str) -> bool:
        """
        更新用户会话的最后访问时间
        
        Args:
            username: 用户名
        
        Returns:
            是否更新成功
        """
        data = await self.load_user_sessions()
        
        if username in data:
            data[username]["last_accessed"] = datetime.now().isoformat()
            success = await self.save_user_sessions(data)
            if success:
                logger.debug(f"已更新用户 {username} 的最后访问时间")
            return success
        
        return False
    
    def _is_session_expired(self, session_info: Dict[str, Any]) -> bool:
        """
        检查会话是否过期
        
        Args:
            session_info: 会话信息
        
        Returns:
            是否过期
        """
        try:
            expires_at = datetime.fromisoformat(session_info["expires_at"])
            return datetime.now() > expires_at
        except (KeyError, ValueError) as e:
            logger.warning(f"检查会话过期时间失败: {e}")
            return True  # 如果无法解析过期时间，认为已过期
    
    async def cleanup_expired_sessions(self) -> int:
        """
        清理所有过期的会话
        
        Returns:
            清理的会话数量
        """
        data = await self.load_user_sessions()
        expired_users = []
        
        for username, session_info in data.items():
            if self._is_session_expired(session_info):
                expired_users.append(username)
        
        for username in expired_users:
            del data[username]
        
        if expired_users:
            await self.save_user_sessions(data)
            logger.info(f"清理了 {len(expired_users)} 个过期会话: {expired_users}")
        
        return len(expired_users)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储文件信息
        
        Returns:
            存储文件信息
        """
        if not self.storage_path.exists():
            return {
                "exists": False,
                "path": str(self.storage_path),
                "size": 0,
                "modified": None
            }
        
        stat = self.storage_path.stat()
        return {
            "exists": True,
            "path": str(self.storage_path),
            "size": stat.st_size,
            "modified": stat.st_mtime
        }