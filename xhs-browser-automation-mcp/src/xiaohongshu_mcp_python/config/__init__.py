"""
配置模块
包含配置文件、设置和类型定义
"""

from .config import (
    XiaohongshuUrls,
    XiaohongshuSelectors,
    BrowserConfig,
    PublishConfig,
    StorageConfig,
    ApiConfig,
)
from .xhs_xpath import XHSXPath
from .settings import settings, Settings
from .types import (
    # HTTP API 响应类型
    ErrorResponse,
    SuccessResponse,
    # MCP 工具结果类型
    MCPContent,
    MCPToolResult,
    # 小红书数据结构
    User,
    Feed,
    Comment,
    # 数据结构组件
    InteractInfo,
    Cover,
    ImageInfo,
    DetailImageInfo,
    Video,
    VideoCapability,
    NoteCard,
    # 发布相关
    PublishImageContent,
    PublishVideoContent,
    PublishResponse,
    # 搜索相关
    SearchResult,
    # 推荐相关
    FeedsListResponse,
    FeedData,
    FeedDetailResponse,
    FeedDetail,
    FeedDetailData,
    CommentList,
    # 用户相关
    UserProfileResponse,
    UserPageData,
    UserBasicInfo,
    UserInteractions,
)

__all__ = [
    # 配置类
    "XiaohongshuUrls",
    "XiaohongshuSelectors",
    "BrowserConfig",
    "PublishConfig",
    "StorageConfig",
    "ApiConfig",
    "XHSXPath",
    # 设置
    "settings",
    "Settings",
    # 类型定义
    "ErrorResponse",
    "SuccessResponse",
    "MCPContent",
    "MCPToolResult",
    "User",
    "Feed",
    "Comment",
    # 数据结构组件
    "InteractInfo",
    "Cover",
    "ImageInfo",
    "DetailImageInfo",
    "Video",
    "VideoCapability",
    "NoteCard",
    # 发布相关
    "PublishImageContent",
    "PublishVideoContent",
    "PublishResponse",
    # 搜索相关
    "SearchResult",
    # 推荐相关
    "FeedsListResponse",
    "FeedData",
    "FeedDetailResponse",
    "FeedDetail",
    "FeedDetailData",
    "CommentList",
    # 用户相关
    "UserProfileResponse",
    "UserPageData",
    "UserBasicInfo",
    "UserInteractions",
]

