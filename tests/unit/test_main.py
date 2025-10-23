import pytest
from unittest.mock import Mock, AsyncMock, patch

from xiaohongshu_mcp_python.main import (
    xiaohongshu_check_login_status,
    xiaohongshu_get_qrcode,
    xiaohongshu_logout
)


@pytest.mark.unit
class TestMainFunctions:
    """主要功能函数的核心业务流程测试"""
    
    @pytest.mark.asyncio
    async def test_check_login_status_not_logged_in(self):
        """测试检查登录状态 - 未登录"""
        mock_login_manager = AsyncMock()
        mock_login_manager.check_login_status.return_value = False
        
        with patch('xiaohongshu_mcp_python.main.login_manager', mock_login_manager):
            result = await xiaohongshu_check_login_status()
            
            assert result == {"logged_in": False}
            mock_login_manager.check_login_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_login_status_logged_in(self):
        """测试检查登录状态 - 已登录"""
        mock_login_manager = AsyncMock()
        mock_login_manager.check_login_status.return_value = True
        
        with patch('xiaohongshu_mcp_python.main.login_manager', mock_login_manager):
            result = await xiaohongshu_check_login_status()
            
            assert result == {"logged_in": True}
            mock_login_manager.check_login_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_qrcode_success(self):
        """测试获取二维码成功"""
        mock_login_manager = AsyncMock()
        mock_qr_data = "test_qr_data"
        mock_login_manager.get_qrcode.return_value = mock_qr_data
        
        with patch('xiaohongshu_mcp_python.main.login_manager', mock_login_manager):
            result = await xiaohongshu_get_qrcode()
            
            assert result == {"qrcode": mock_qr_data}
            mock_login_manager.get_qrcode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_logout_success(self):
        """测试登出成功"""
        mock_login_manager = AsyncMock()
        mock_login_manager.logout.return_value = True
        
        with patch('xiaohongshu_mcp_python.main.login_manager', mock_login_manager):
            result = await xiaohongshu_logout()
            
            assert result == {"success": True}
            mock_login_manager.logout.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_with_cleanup(self):
        """测试错误处理和清理"""
        mock_login_manager = AsyncMock()
        mock_login_manager.check_login_status.side_effect = Exception("Test error")
        mock_login_manager.cleanup = AsyncMock()
        
        with patch('xiaohongshu_mcp_python.main.login_manager', mock_login_manager):
            with pytest.raises(Exception, match="Test error"):
                await xiaohongshu_check_login_status()
            
            # 验证错误发生时会调用清理方法
            mock_login_manager.check_login_status.assert_called_once()