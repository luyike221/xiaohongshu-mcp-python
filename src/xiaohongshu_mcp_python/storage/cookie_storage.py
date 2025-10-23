"""
Cookie存储模块

提供Cookie的持久化功能，支持保存和加载浏览器Cookie。
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger


class CookieStorage:
    """Cookie存储管理器"""
    
    def __init__(self, cookie_path: Optional[str] = None):
        """
        初始化Cookie存储
        
        Args:
            cookie_path: Cookie文件路径，如果为None则使用默认路径
        """
        self.cookie_path = self._get_cookie_path(cookie_path)
        self._ensure_directory()
    
    def _get_cookie_path(self, cookie_path: Optional[str]) -> Path:
        """
        获取Cookie文件路径
        
        Args:
            cookie_path: 指定的Cookie路径
        
        Returns:
            Cookie文件路径
        """
        if cookie_path:
            return Path(cookie_path)
        
        # 检查环境变量
        env_path = os.getenv("COOKIES_PATH")
        if env_path:
            return Path(env_path)
        
        # 检查/tmp/cookies.json是否存在（向后兼容）
        tmp_path = Path("/tmp/cookies.json")
        if tmp_path.exists():
            return tmp_path
        
        # 默认使用当前目录下的cookies.json
        return Path("cookies.json")
    
    def _ensure_directory(self) -> None:
        """确保Cookie文件的目录存在"""
        self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def load_cookies(self) -> List[Dict[str, Any]]:
        """
        加载Cookie
        
        Returns:
            Cookie列表
        """
        if not self.cookie_path.exists():
            logger.info(f"Cookie文件不存在: {self.cookie_path}")
            return []
        
        try:
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            logger.info(f"成功加载 {len(cookies)} 个Cookie")
            return cookies
        
        except json.JSONDecodeError as e:
            logger.error(f"Cookie文件格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载Cookie失败: {e}")
            return []
    
    async def save_cookies(self, cookies: List[Dict[str, Any]]) -> bool:
        """
        保存Cookie
        
        Args:
            cookies: Cookie列表
        
        Returns:
            是否保存成功
        """
        try:
            # 过滤掉无效的Cookie
            valid_cookies = self._filter_valid_cookies(cookies)
            
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(valid_cookies, f, indent=2, ensure_ascii=False)
            
            logger.info(f"成功保存 {len(valid_cookies)} 个Cookie到: {self.cookie_path}")
            return True
        
        except Exception as e:
            logger.error(f"保存Cookie失败: {e}")
            return False
    
    def _filter_valid_cookies(self, cookies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤有效的Cookie
        
        Args:
            cookies: 原始Cookie列表
        
        Returns:
            有效的Cookie列表
        """
        valid_cookies = []
        
        for cookie in cookies:
            # 检查必需的字段
            if not all(key in cookie for key in ['name', 'value', 'domain']):
                logger.warning(f"跳过无效Cookie: {cookie}")
                continue
            
            # 过滤掉空值
            if not cookie['name'] or not cookie['value']:
                logger.warning(f"跳过空Cookie: {cookie}")
                continue
            
            valid_cookies.append(cookie)
        
        return valid_cookies
    
    def clear_cookies(self) -> bool:
        """
        清除Cookie文件
        
        Returns:
            是否清除成功
        """
        try:
            if self.cookie_path.exists():
                self.cookie_path.unlink()
                logger.info(f"已清除Cookie文件: {self.cookie_path}")
            return True
        except Exception as e:
            logger.error(f"清除Cookie失败: {e}")
            return False
    
    def has_cookies(self) -> bool:
        """
        检查是否存在Cookie文件
        
        Returns:
            是否存在Cookie文件
        """
        return self.cookie_path.exists() and self.cookie_path.stat().st_size > 0
    
    def get_cookie_info(self) -> Dict[str, Any]:
        """
        获取Cookie文件信息
        
        Returns:
            Cookie文件信息
        """
        if not self.cookie_path.exists():
            return {
                "exists": False,
                "path": str(self.cookie_path),
                "size": 0,
                "modified": None
            }
        
        stat = self.cookie_path.stat()
        return {
            "exists": True,
            "path": str(self.cookie_path),
            "size": stat.st_size,
            "modified": stat.st_mtime
        }
    
    async def backup_cookies(self, backup_path: Optional[str] = None) -> bool:
        """
        备份Cookie文件
        
        Args:
            backup_path: 备份文件路径，如果为None则使用默认命名
        
        Returns:
            是否备份成功
        """
        if not self.cookie_path.exists():
            logger.warning("Cookie文件不存在，无法备份")
            return False
        
        try:
            if backup_path is None:
                backup_path = f"{self.cookie_path}.backup"
            
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件内容
            with open(self.cookie_path, 'rb') as src, open(backup_file, 'wb') as dst:
                dst.write(src.read())
            
            logger.info(f"Cookie备份成功: {backup_file}")
            return True
        
        except Exception as e:
            logger.error(f"Cookie备份失败: {e}")
            return False