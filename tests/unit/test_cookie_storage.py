import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json

from xiaohongshu_mcp_python.storage.cookie_storage import CookieStorage


@pytest.mark.unit
class TestCookieStorage:
    """CookieStorage 核心业务流程测试"""
    
    def test_init_default(self):
        """测试默认初始化"""
        storage = CookieStorage()
        assert storage.cookie_path.name == "cookies.json"
    
    def test_init_custom_path(self):
        """测试自定义路径初始化"""
        custom_path = Path("/tmp/custom_cookies.json")
        storage = CookieStorage(cookie_path=custom_path)
        assert storage.cookie_path == custom_path
    
    @pytest.mark.asyncio
    async def test_load_cookies_success(self):
        """测试成功加载cookies"""
        storage = CookieStorage()
        test_cookies = [{"name": "test", "value": "value"}]
        
        with patch("builtins.open", mock_open(read_data=json.dumps(test_cookies))):
            with patch.object(storage.cookie_path, "exists", return_value=True):
                cookies = await storage.load_cookies()
                assert cookies == test_cookies
    
    @pytest.mark.asyncio
    async def test_load_cookies_not_exists(self):
        """测试加载不存在的cookies文件"""
        storage = CookieStorage()
        
        with patch.object(storage.cookie_path, "exists", return_value=False):
            cookies = await storage.load_cookies()
            assert cookies == []
    
    @pytest.mark.asyncio
    async def test_save_cookies_success(self):
        """测试成功保存cookies"""
        storage = CookieStorage()
        test_cookies = [{"name": "test", "value": "value", "domain": ".test.com"}]
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(storage.cookie_path.parent, "mkdir"):
                result = await storage.save_cookies(test_cookies)
                assert result is True
                mock_file.assert_called_once()
    
    def test_has_cookies_exists(self):
        """测试检查cookies文件存在"""
        storage = CookieStorage()
        
        with patch.object(storage.cookie_path, "exists", return_value=True):
            with patch.object(storage.cookie_path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 100
                assert storage.has_cookies() is True
    
    def test_has_cookies_not_exists(self):
        """测试检查cookies文件不存在"""
        storage = CookieStorage()
        
        with patch.object(storage.cookie_path, "exists", return_value=False):
            assert storage.has_cookies() is False
    
    def test_clear_cookies_success(self):
        """测试清除cookies"""
        storage = CookieStorage()
        
        with patch.object(storage.cookie_path, "exists", return_value=True):
            with patch.object(storage.cookie_path, "unlink") as mock_unlink:
                result = storage.clear_cookies()
                assert result is True
                mock_unlink.assert_called_once()
    
    def test_get_cookie_info_exists(self):
        """测试获取cookies信息"""
        storage = CookieStorage()
        
        with patch.object(storage.cookie_path, "exists", return_value=True):
            with patch.object(storage.cookie_path, "stat") as mock_stat:
                mock_stat.return_value.st_size = 1024
                mock_stat.return_value.st_mtime = 1234567890.0
                
                info = storage.get_cookie_info()
                assert info["exists"] is True
                assert info["size"] == 1024
                assert info["modified"] == 1234567890.0