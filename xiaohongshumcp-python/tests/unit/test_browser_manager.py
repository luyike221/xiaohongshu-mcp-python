import pytest
from unittest.mock import Mock, AsyncMock, patch

from xiaohongshu_mcp_python.browser.browser_manager import BrowserManager


@pytest.mark.unit
class TestBrowserManager:
    """BrowserManager 核心业务流程测试"""
    
    def test_init_default(self):
        """测试默认初始化"""
        manager = BrowserManager()
        assert manager.headless is False
        assert manager.browser is None
        assert manager.context is None
        assert manager.page is None
    
    def test_init_custom_headless(self):
        """测试自定义headless模式初始化"""
        manager = BrowserManager(headless=False)
        assert manager.headless is False
    
    @pytest.mark.asyncio
    async def test_start_success(self):
        """测试成功启动浏览器"""
        manager = BrowserManager()
        
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_playwright_instance = AsyncMock()
            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            
            await manager.start()
            
            assert manager.browser == mock_browser
            assert manager.context == mock_context
            assert manager.page == mock_page
    
    @pytest.mark.asyncio
    async def test_stop_success(self):
        """测试成功停止浏览器"""
        manager = BrowserManager()
        manager.browser = AsyncMock()
        manager.context = AsyncMock()
        manager.page = AsyncMock()
        
        await manager.stop()
        
        manager.browser.close.assert_called_once()
        assert manager.browser is None
        assert manager.context is None
        assert manager.page is None
    
    @pytest.mark.asyncio
    async def test_get_page_started(self):
        """测试获取页面（已启动）"""
        manager = BrowserManager()
        mock_page = AsyncMock()
        manager.page = mock_page
        
        page = await manager.get_page()
        assert page == mock_page
    
    @pytest.mark.asyncio
    async def test_get_page_not_started(self):
        """测试获取页面（未启动）"""
        manager = BrowserManager()
        
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_playwright_instance = AsyncMock()
            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            
            page = await manager.get_page()
            
            assert page == mock_page
            assert manager.page == mock_page
    
    def test_is_started_true(self):
        """测试浏览器已启动状态"""
        manager = BrowserManager()
        manager.browser = Mock()
        
        assert manager.is_started() is True
    
    def test_is_started_false(self):
        """测试浏览器未启动状态"""
        manager = BrowserManager()
        
        assert manager.is_started() is False
    
    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self):
        """测试上下文管理器"""
        manager = BrowserManager()
        
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_playwright_instance = AsyncMock()
            mock_playwright.return_value.__aenter__ = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.chromium.launch.return_value = mock_browser
            
            async with manager as mgr:
                assert mgr == manager
                assert manager.browser == mock_browser
            
            # 验证退出时关闭浏览器
            mock_browser.close.assert_called_once()