"""
小红书 MCP 服务的数据类型定义
基于 Go 版本的设计，定义 Python 版本的数据结构
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============ HTTP API 响应类型 ============

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# ============ MCP 工具结果类型 ============

class MCPContent(BaseModel):
    """MCP 内容"""
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class MCPToolResult(BaseModel):
    """MCP 工具结果"""
    content: List[MCPContent]
    isError: bool = False


# ============ 小红书数据结构 ============

class User(BaseModel):
    """用户信息"""
    user_id: str
    nickname: str
    avatar: Optional[str] = None
    desc: Optional[str] = None
    gender: Optional[int] = None
    ip_location: Optional[str] = None


class InteractInfo(BaseModel):
    """互动信息"""
    liked: bool = False
    liked_count: str = "0"
    collected: bool = False
    collected_count: str = "0"
    comment_count: str = "0"
    share_count: str = "0"


class Cover(BaseModel):
    """封面信息"""
    url: str
    width: int
    height: int
    file_id: Optional[str] = None


class ImageInfo(BaseModel):
    """图片信息"""
    url: str
    width: int
    height: int
    file_id: Optional[str] = None


class VideoCapability(BaseModel):
    """视频能力"""
    adaptive_type: int
    media_type: int
    profile: str
    quality_type: int


class Video(BaseModel):
    """视频信息"""
    media: Dict[str, Any]
    video_id: str
    duration: int
    width: int
    height: int
    master_url: str
    backup_urls: List[str]
    stream: Dict[str, Any]
    h264: List[VideoCapability]
    h265: List[VideoCapability]
    av1: List[VideoCapability]


class NoteCard(BaseModel):
    """笔记卡片"""
    type: str
    display_title: str
    user: User
    interact_info: InteractInfo
    cover: Cover
    images_list: Optional[List[ImageInfo]] = None
    video: Optional[Video] = None


class Feed(BaseModel):
    """动态信息"""
    id: str
    model_type: str
    note_card: NoteCard
    track_id: Optional[str] = None


class FeedData(BaseModel):
    """动态数据"""
    items: List[Feed]
    cursor_score: Optional[str] = None
    has_more: bool = False


class FeedResponse(BaseModel):
    """动态响应"""
    success: bool
    code: int
    msg: str
    data: FeedData


# ============ 动态详情页数据结构 ============

class DetailImageInfo(BaseModel):
    """详情页图片信息"""
    url: str
    width: int
    height: int
    file_id: Optional[str] = None
    live_photo: Optional[Dict[str, Any]] = None
    format: Optional[str] = None


class FeedDetail(BaseModel):
    """动态详情"""
    note_id: str
    title: str
    desc: str
    type: str
    user: User
    interact_info: InteractInfo
    image_list: Optional[List[DetailImageInfo]] = None
    video: Optional[Video] = None
    tag_list: Optional[List[Dict[str, Any]]] = None
    at_user_list: Optional[List[Dict[str, Any]]] = None
    collected_count: str = "0"
    comment_count: str = "0"
    liked_count: str = "0"
    share_count: str = "0"
    time: int = 0
    last_update_time: int = 0


class FeedDetailResponse(BaseModel):
    """动态详情响应"""
    success: bool
    code: int
    msg: str
    data: FeedDetail


# ============ 评论数据结构 ============

class Comment(BaseModel):
    """评论"""
    id: str
    content: str
    create_time: int
    ip_location: Optional[str] = None
    like_count: int = 0
    user: User
    sub_comments: Optional[List['Comment']] = None
    sub_comment_count: int = 0
    target_comment: Optional['Comment'] = None


class CommentList(BaseModel):
    """评论列表"""
    comments: List[Comment]
    cursor: Optional[str] = None
    has_more: bool = False
    time: int = 0


# ============ 用户资料数据结构 ============

class UserBasicInfo(BaseModel):
    """用户基本信息"""
    user_id: str
    nickname: str
    avatar: Optional[str] = None
    desc: Optional[str] = None
    gender: Optional[int] = None
    ip_location: Optional[str] = None
    red_id: Optional[str] = None


class UserInteractions(BaseModel):
    """用户互动数据"""
    follows: str = "0"
    fans: str = "0"
    interaction: str = "0"


class UserPageData(BaseModel):
    """用户页面数据"""
    basic_info: UserBasicInfo
    interactions: UserInteractions
    tags: Optional[List[Dict[str, Any]]] = None


class UserProfileResponse(BaseModel):
    """用户资料响应"""
    success: bool
    code: int
    msg: str
    data: UserPageData


# ============ 发布相关数据结构 ============

class PublishImageContent(BaseModel):
    """发布图文内容"""
    title: str = Field(..., min_length=1, max_length=20, description="标题，1-20个字符")
    content: str = Field(..., description="正文内容")
    images: List[str] = Field(..., min_items=1, max_items=9, description="图片路径列表，1-9张图片")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")


class PublishVideoContent(BaseModel):
    """发布视频内容"""
    title: str = Field(..., min_length=1, max_length=20, description="标题，1-20个字符")
    video_path: str = Field(..., description="视频文件路径")
    cover_path: Optional[str] = Field(default=None, description="封面图片路径")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")


class PublishResponse(BaseModel):
    """发布响应"""
    success: bool
    message: str
    note_id: Optional[str] = None
    error: Optional[str] = None


# ============ 搜索相关数据结构 ============

class SearchResult(BaseModel):
    """搜索结果"""
    items: List[Feed]
    has_more: bool = False
    cursor: Optional[str] = None
    total: int = 0


# ============ 服务响应数据结构 ============

class FeedsListResponse(BaseModel):
    """推荐列表响应"""
    success: bool
    feeds: List[Feed]
    has_more: bool = False
    cursor_score: Optional[str] = None
    error: Optional[str] = None


# 更新前向引用
Comment.model_rebuild()