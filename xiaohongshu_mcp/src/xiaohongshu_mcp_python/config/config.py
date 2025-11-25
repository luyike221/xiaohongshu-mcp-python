"""
小红书 MCP 服务配置文件
定义 URL、选择器和其他常量
"""

from typing import Dict, Any
from pathlib import Path
from .settings import get_project_root


# ============ 小红书 URL 配置 ============

class XiaohongshuUrls:
    """小红书 URL 配置"""
    
    # 基础 URL
    BASE_URL = "https://www.xiaohongshu.com"
    HOME_URL = "https://www.xiaohongshu.com"  # 首页URL，与BASE_URL相同
    
    # 登录相关
    LOGIN_URL = "https://www.xiaohongshu.com"
    QR_CODE_URL = "https://www.xiaohongshu.com/api/sns/web/v1/login/qrcode/create"
    QR_STATUS_URL = "https://www.xiaohongshu.com/api/sns/web/v1/login/qrcode/status"
    
    # 创作者中心
    CREATOR_URL = "https://creator.xiaohongshu.com"
    PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?source=official"
    
    # 搜索
    SEARCH_URL = "https://www.xiaohongshu.com/search_result"
    
    # 推荐页面
    EXPLORE_URL = "https://www.xiaohongshu.com/explore"
    
    # 用户资料
    USER_PROFILE_URL = "https://www.xiaohongshu.com/user/profile/{user_id}"
    
    # 笔记详情
    NOTE_DETAIL_URL = "https://www.xiaohongshu.com/discovery/item/{note_id}"


# ============ CSS 选择器配置 ============

class XiaohongshuSelectors:
    """小红书页面元素选择器"""
    
    # 登录相关
    LOGIN_BUTTON = ".login-btn"
    QR_CODE_IMAGE = ".qr-img img"
    LOGIN_SUCCESS_INDICATOR = ".user-info"
    
    # 发布页面
    PUBLISH_TAB = '//div[3][normalize-space(.)="上传图文"][contains(@class, "creator-tab")]'
    VIDEO_PUBLISH_TAB = '//div[normalize-space(.)="上传视频"][contains(@class, "creator-tab")]'
    UPLOAD_INPUT = ".upload-input"
    UPLOADED_IMAGE = ".img-preview-area .pr"
    
    # 内容输入
    TITLE_INPUT = '//input[@class="d-text"]'  # 标题输入框
    CONTENT_TEXTAREA = '//div[contains(@class, "tiptap")][contains(@class, "ProseMirror")]'  # 正文编辑器（Quill编辑器）
    
    # 标签联想容器
    TOPIC_SUGGEST_CONTAINER = '//div[@id="creator-editor-topic-container"]'  # 话题联想容器
    TOPIC_SUGGEST_ITEM = '//div[contains(@class, "is-selected")]/span[@class="name"]'  # 话题联想项
    
    # 发布按钮（注意：图文和视频发布按钮不同，不能混用）
    IMAGE_PUBLISH_BUTTON = '//button/div[normalize-space(.)="发布"]'  # 图文发布按钮
    VIDEO_PUBLISH_BUTTON = "button.publishBtn"  # 视频发布按钮（保持原有选择器）
    CANCEL_BUTTON = '//button[contains(@class, "d-button")][contains(@class, "d-button-large")][contains(@class, "cancelBtn")]'  # 暂存离开按钮
    
    # 搜索相关
    SEARCH_INPUT = "input[placeholder*='搜索']"
    SEARCH_RESULT_ITEM = ".note-item"
    
    # 推荐页面
    FEED_ITEM = ".note-item"
    FEED_TITLE = ".title"
    FEED_AUTHOR = ".author"
    FEED_COVER = ".cover img"
    
    # 弹窗和遮罩
    POPUP_CLOSE = ".close-btn, .popup-close"
    MODAL_MASK = ".modal-mask"
    
    # 加载状态
    LOADING_INDICATOR = ".loading"
    
    # 错误提示
    ERROR_MESSAGE = ".error-message, .toast-error"


# ============ 浏览器配置 ============

class BrowserConfig:
    """浏览器配置"""
    
    # 默认超时时间（毫秒）
    DEFAULT_TIMEOUT = 30000
    
    # 页面加载超时时间
    PAGE_LOAD_TIMEOUT = 120000
    
    # 元素等待超时时间
    ELEMENT_TIMEOUT = 10000
    
    # 上传等待超时时间
    UPLOAD_TIMEOUT = 120000
    
    # 视窗大小配置
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # 浏览器启动参数 - 优化反检测
    BROWSER_ARGS = [
        "--disable-blink-features=AutomationControlled",
        "--exclude-switches=enable-automation",
        "--disable-extensions",
        "--disable-plugins-discovery",
        "--no-first-run",
        "--no-service-autorun",
        "--password-store=basic",
        "--use-mock-keychain",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--mute-audio",
        "--no-zygote",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--disable-hang-monitor",
        "--disable-client-side-phishing-detection",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-report-upload",
        "--safebrowsing-disable-auto-update",
        "--enable-automation=false",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "--disable-features=VizDisplayCompositor"
    ]
    
    # 用户代理 - 使用最新版本
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    
    # 额外的反检测配置
    STEALTH_CONFIG = {
        "webdriver": False,
        "chrome_app": False,
        "chrome_csi": False,
        "chrome_load_times": False,
        "chrome_runtime": False,
        "iframe_content_window": False,
        "media_codecs": False,
        "navigator_languages": False,
        "navigator_permissions": False,
        "navigator_plugins": False,
        "navigator_webdriver": False,
        "webgl_vendor": False,
        "window_outerdimensions": False,
    }


# ============ 发布配置 ============

class PublishConfig:
    """发布配置"""
    
    # 标题长度限制
    TITLE_MIN_LENGTH = 1
    TITLE_MAX_LENGTH = 20
    
    # 图片数量限制
    IMAGE_MIN_COUNT = 1
    IMAGE_MAX_COUNT = 9
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv"]
    
    # 最大文件大小（字节）
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_VIDEO_SIZE = 1024 * 1024 * 1024  # 1GB
    
    # 标签前缀
    TAG_PREFIX = "#"
    
    # 上传重试次数
    UPLOAD_RETRY_COUNT = 3
    
    # 上传间隔时间（秒）
    UPLOAD_INTERVAL = 1


# ============ 存储配置 ============

class StorageConfig:
    """存储配置"""
    
    # 项目根目录
    _project_root = get_project_root()
    
    # Cookie 存储路径（相对于项目根目录）
    COOKIE_DIR = _project_root / "cookies"
    
    # 会话存储路径（相对于项目根目录）
    SESSION_DIR = _project_root / "sessions"
    
    # 临时文件路径（相对于项目根目录）
    TEMP_DIR = _project_root / "temp"
    
    # 下载文件路径（相对于项目根目录）
    DOWNLOAD_DIR = _project_root / "downloads"
    
    # 数据目录（相对于项目根目录）
    DATA_DIR = _project_root / "data"
    
    # 日志目录（相对于项目根目录）
    LOG_DIR = _project_root / "logs"
    
    # Cookie 过期时间（秒）
    COOKIE_EXPIRE_TIME = 30 * 24 * 3600  # 30天
    
    # 会话过期时间（秒）
    SESSION_EXPIRE_TIME = 24 * 3600  # 24小时


# ============ API 配置 ============

class ApiConfig:
    """API 配置"""
    
    # 请求头
    DEFAULT_HEADERS = {
        "User-Agent": BrowserConfig.USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    
    # 请求超时时间（秒）
    REQUEST_TIMEOUT = 30
    
    # 重试次数
    RETRY_COUNT = 3
    
    # 重试间隔（秒）
    RETRY_INTERVAL = 1


# ============ 日志配置 ============

class LogConfig:
    """日志配置"""
    
    # 项目根目录
    _project_root = get_project_root()
    
    # 日志级别
    LOG_LEVEL = "INFO"
    
    # 日志格式
    LOG_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | "
        "{name}:{function}:{line} - {message}"
    )
    
    # 日志文件路径（相对于项目根目录）
    LOG_FILE = _project_root / "logs" / "xiaohongshu_mcp.log"
    
    # 日志文件大小限制（字节）
    LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # 日志文件保留数量
    LOG_FILE_COUNT = 5


# ============ 全局配置 ============

class GlobalConfig:
    """全局配置"""
    
    # 项目根目录
    _project_root = get_project_root()
    
    # 默认用户名
    DEFAULT_USERNAME = "default_user"
    
    # 是否启用调试模式
    DEBUG = False
    
    # 是否启用详细日志
    VERBOSE = False
    
    # 数据目录（相对于项目根目录）
    DATA_DIR = _project_root / "data"
    
    # 配置文件路径
    CONFIG_FILE = "config.json"


# 导出所有配置类
__all__ = [
    "XiaohongshuUrls",
    "XiaohongshuSelectors", 
    "BrowserConfig",
    "PublishConfig",
    "StorageConfig",
    "ApiConfig",
    "LogConfig",
    "GlobalConfig",
]