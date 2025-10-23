"""
登录相关的数据类型定义

定义登录状态、二维码信息等数据结构。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class LoginStatus(Enum):
    """登录状态枚举"""
    UNKNOWN = "unknown"          # 未知状态
    NOT_LOGGED_IN = "not_logged_in"  # 未登录
    LOGGED_IN = "logged_in"      # 已登录
    LOGIN_EXPIRED = "login_expired"  # 登录已过期


@dataclass
class QRCodeInfo:
    """二维码信息"""
    image_url: str              # 二维码图片URL
    image_data: Optional[bytes] = None  # 二维码图片数据
    qr_token: Optional[str] = None      # 二维码令牌（如果有）
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.image_url:
            raise ValueError("二维码图片URL不能为空")


@dataclass
class LoginResult:
    """登录结果"""
    success: bool               # 是否成功
    status: LoginStatus         # 登录状态
    message: str               # 结果消息
    cookies_saved: bool = False # 是否已保存Cookie
    
    @classmethod
    def success_result(cls, message: str = "登录成功", cookies_saved: bool = True) -> "LoginResult":
        """创建成功结果"""
        return cls(
            success=True,
            status=LoginStatus.LOGGED_IN,
            message=message,
            cookies_saved=cookies_saved
        )
    
    @classmethod
    def failure_result(cls, message: str, status: LoginStatus = LoginStatus.NOT_LOGGED_IN) -> "LoginResult":
        """创建失败结果"""
        return cls(
            success=False,
            status=status,
            message=message,
            cookies_saved=False
        )


@dataclass
class LoginConfig:
    """登录配置"""
    xiaohongshu_url: str = "https://www.xiaohongshu.com/explore"
    login_check_selector: str = ".main-container .user .link-wrapper .channel"
    qrcode_selector: str = ".login-container .qrcode-img"
    login_success_selector: str = ".main-container .user .link-wrapper .channel"
    
    # 超时配置（秒）
    page_load_timeout: int = 30
    login_wait_timeout: int = 300  # 5分钟
    qrcode_timeout: int = 60
    
    # 轮询间隔（毫秒）
    login_check_interval: int = 500
    
    # 重试配置
    max_retries: int = 3
    retry_delay: int = 2  # 秒