import pytest
from unittest.mock import Mock, AsyncMock, patch

from xiaohongshu_mcp_python.browser.browser_manager import BrowserManager


@pytest.mark.unit
class TestBrowserManager:
    """BrowserManager 核心业务流程测试"""

    def test_init_default(self):
        manager = BrowserManager()
        assert manager.headless is False
        assert manager.browser is None
        assert manager.context is None
        assert manager.page is None

    def test_init_custom_headless(self):
        manager = BrowserManager(headless=False)
        assert manager.headless is False

    @pytest.mark.asyncio
    async def test_start_success(self, tmp_path):
        ud = tmp_path / "chrome-prof"
        manager = BrowserManager(user_data_dir=ud)

        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.browser = mock_browser
        mock_context.pages = [mock_page]

        mock_pw_driver = AsyncMock()
        mock_pw_driver.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)

        mock_cm = AsyncMock()
        mock_cm.start = AsyncMock(return_value=mock_pw_driver)

        with patch(
            "xiaohongshu_mcp_python.browser.browser_manager.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value = mock_cm

            with patch.object(BrowserManager, "_apply_stealth", new_callable=AsyncMock):
                await manager.start()

        assert manager.browser == mock_browser
        assert manager.context == mock_context
        assert manager.page == mock_page

    @pytest.mark.asyncio
    async def test_stop_success(self):
        manager = BrowserManager()
        manager._playwright = AsyncMock()
        manager._browser = AsyncMock()
        manager._context = AsyncMock()
        manager._page = AsyncMock()

        await manager.stop()

        manager._page.close.assert_called_once()
        manager._context.close.assert_called_once()
        manager._browser.close.assert_called_once()
        manager._playwright.stop.assert_called_once()
        assert manager.browser is None
        assert manager.context is None
        assert manager.page is None

    @pytest.mark.asyncio
    async def test_get_page_started(self):
        manager = BrowserManager()
        mock_page = AsyncMock()
        manager._playwright = Mock()
        manager._browser = Mock()
        manager._browser.is_connected = Mock(return_value=True)
        manager._context = Mock()
        manager._page = mock_page

        page = await manager.get_page()
        assert page == mock_page

    @pytest.mark.asyncio
    async def test_get_page_not_started(self, tmp_path):
        manager = BrowserManager(user_data_dir=tmp_path / "p")

        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.browser = mock_browser
        mock_context.pages = []
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_pw_driver = AsyncMock()
        mock_pw_driver.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)

        mock_cm = AsyncMock()
        mock_cm.start = AsyncMock(return_value=mock_pw_driver)

        with patch(
            "xiaohongshu_mcp_python.browser.browser_manager.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value = mock_cm

            with patch.object(BrowserManager, "_apply_stealth", new_callable=AsyncMock):
                page = await manager.get_page()

                assert page == mock_page
                assert manager.page == mock_page

    def test_is_started_true(self):
        manager = BrowserManager()
        manager._playwright = Mock()
        manager._context = Mock()

        assert manager.is_started() is True

    def test_is_started_false(self):
        manager = BrowserManager()

        assert manager.is_started() is False

    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self, tmp_path):
        manager = BrowserManager(user_data_dir=tmp_path / "cx")

        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.browser = mock_browser
        mock_context.pages = [mock_page]

        mock_pw_driver = AsyncMock()
        mock_pw_driver.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)

        mock_cm = AsyncMock()
        mock_cm.start = AsyncMock(return_value=mock_pw_driver)

        with patch(
            "xiaohongshu_mcp_python.browser.browser_manager.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value = mock_cm

            with patch.object(BrowserManager, "_apply_stealth", new_callable=AsyncMock):
                async with manager as mgr:
                    assert mgr == manager
                    assert manager.browser == mock_browser

                mock_context.close.assert_called_once()
