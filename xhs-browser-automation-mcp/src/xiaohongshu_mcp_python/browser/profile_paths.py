"""持久化 Chrome User Data 目录解析（与 cookies JSON 脱钩）。"""

import re
from pathlib import Path
from typing import Optional

from ..config.settings import Settings, get_project_root


def _safe_profile_segment(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", name.strip())
    return s or "user"


def resolve_settings_user_data_dir() -> Path:
    """解析 .env 中的主自动化目录（相对路径相对于项目根）。"""
    root = get_project_root()
    raw = (Settings.BROWSER_USER_DATA_DIR or "browser-profile").strip()
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = root / p
    return p


def resolve_profile_user_data_dir(for_username: Optional[str]) -> Path:
    """
    解析用于自动化的小红书登录态目录。
    - GLOBAL_USER：使用 Settings 中的主目录（默认 browser-profile）。
    - 其他用户名：使用 browser-profile-users/<safe>，避免与主目录冲突。
    """
    root = get_project_root()
    main = resolve_settings_user_data_dir()
    user = for_username or Settings.GLOBAL_USER
    if user == Settings.GLOBAL_USER:
        return main
    return root / "browser-profile-users" / _safe_profile_segment(user)


def login_session_user_data_dir(session_id: str, username: Optional[str]) -> Path:
    """登录会话专用目录：有名用户走 resolve_profile_user_data_dir，匿名走 sessions 子目录。"""
    root = get_project_root()
    if username:
        return resolve_profile_user_data_dir(username)
    return root / "browser-profile-sessions" / session_id
