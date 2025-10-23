"""
pytest配置和共享fixtures
"""
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from xiaohongshu_mcp_python.storage.cookie_storage import CookieStorage
from xiaohongshu_mcp_python.browser.browser_manager import BrowserManager
from xiaohongshu_mcp_python.xiaohongshu.login_manager import LoginManager
from xiaohongshu_mcp_python.xiaohongshu.login_types import LoginStatus


@pytest.fixture
def temp_cookie_file(tmp_path):
    """临时cookie文件"""
    return tmp_path / "test_cookies.json"


@pytest.fixture
def mock_cookie_storage(temp_cookie_file):
    """模拟的cookie存储"""
    storage = CookieStorage(temp_cookie_file)
    return storage


@pytest.fixture
def mock_browser_manager():
    """模拟的浏览器管理器"""
    manager = MagicMock(spec=BrowserManager)
    manager.get_browser = AsyncMock()
    manager.close = AsyncMock()
    return manager


@pytest.fixture
def mock_login_manager():
    """模拟的登录管理器"""
    manager = MagicMock(spec=LoginManager)
    manager.check_login_status = AsyncMock(return_value=LoginStatus.NOT_LOGGED_IN)
    manager.get_qr_code = AsyncMock(return_value="mock_qr_code_data")
    manager.wait_for_login = AsyncMock(return_value=LoginStatus.LOGGED_IN)
    manager.login = AsyncMock(return_value=LoginStatus.LOGGED_IN)
    manager.logout = AsyncMock(return_value=LoginStatus.NOT_LOGGED_IN)
    return manager


@pytest.fixture
def mock_components(mock_cookie_storage, mock_browser_manager, mock_login_manager):
    """所有模拟组件的集合"""
    return {
        'cookie_storage': mock_cookie_storage,
        'browser_manager': mock_browser_manager,
        'login_manager': mock_login_manager
    }


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()