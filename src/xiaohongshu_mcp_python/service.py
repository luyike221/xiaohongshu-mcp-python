"""
小红书服务层
提供小红书相关功能的高级接口
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from loguru import logger

try:
    from fastmcp import Context
except ImportError:
    Context = None

from .types import (
    PublishImageContent,
    PublishVideoContent,
    PublishResponse,
    FeedsListResponse,
    SearchResult,
    UserProfileResponse,
    FeedDetailResponse,
    CommentList,
)
from .browser.browser_manager import BrowserManager
from .xiaohongshu.publish import PublishAction
from .xiaohongshu.search import SearchAction
from .xiaohongshu.feeds import FeedsAction
from .xiaohongshu.user import UserAction
# from .xiaohongshu.comment import CommentAction
# from .xiaohongshu.like import LikeAction
# from .xiaohongshu.favorite import FavoriteAction
from .utils.image_processor import ImageProcessor
from .config import PublishConfig, XiaohongshuUrls


class XiaohongshuService:
    """小红书服务类"""
    
    def __init__(self, browser_manager: BrowserManager):
        """
        初始化小红书服务
        
        Args:
            browser_manager: 浏览器管理器实例
        """
        self.browser_manager = browser_manager
        self.image_processor = ImageProcessor()
        
    async def publish_content(
        self,
        content: PublishImageContent,
        username: Optional[str] = None,
        context: Optional[Context] = None
    ) -> PublishResponse:
        """
        发布图文内容
        
        Args:
            content: 发布内容
            username: 用户名
            
        Returns:
            发布结果
        """
        try:
            # 验证标题长度
            if len(content.title) < PublishConfig.TITLE_MIN_LENGTH:
                return PublishResponse(
                    success=False,
                    message="标题不能为空",
                    error="TITLE_TOO_SHORT"
                )
            
            if len(content.title) > PublishConfig.TITLE_MAX_LENGTH:
                return PublishResponse(
                    success=False,
                    message=f"标题不能超过{PublishConfig.TITLE_MAX_LENGTH}个字符",
                    error="TITLE_TOO_LONG"
                )
            
            # 验证图片数量
            if len(content.images) < PublishConfig.IMAGE_MIN_COUNT:
                return PublishResponse(
                    success=False,
                    message="至少需要1张图片",
                    error="NOT_ENOUGH_IMAGES"
                )
            
            if len(content.images) > PublishConfig.IMAGE_MAX_COUNT:
                return PublishResponse(
                    success=False,
                    message=f"最多只能上传{PublishConfig.IMAGE_MAX_COUNT}张图片",
                    error="TOO_MANY_IMAGES"
                )
            
            # 处理图片（下载URL图片或验证本地图片）
            logger.info(f"开始处理 {len(content.images)} 张图片")
            processed_images = await self.image_processor.process_images(content.images)
            
            if not processed_images:
                return PublishResponse(
                    success=False,
                    message="图片处理失败",
                    error="IMAGE_PROCESSING_FAILED"
                )
            
            logger.info(f"图片处理完成，共 {len(processed_images)} 张图片")
            
            # 执行发布
            return await self._publish_content(
                title=content.title,
                content_text=content.content,
                images=processed_images,
                tags=content.tags or [],
                username=username,
                context=context
            )
            
        except Exception as e:
            logger.error(f"发布内容失败: {e}")
            return PublishResponse(
                success=False,
                message=f"发布失败: {str(e)}",
                error="PUBLISH_FAILED"
            )
    
    async def publish_video(
        self,
        content: PublishVideoContent,
        username: Optional[str] = None,
        context: Optional[Context] = None
    ) -> PublishResponse:
        """
        发布视频内容
        
        Args:
            content: 视频内容
            username: 用户名
            
        Returns:
            发布结果
        """
        try:
            # 验证标题长度
            if len(content.title) < PublishConfig.TITLE_MIN_LENGTH:
                return PublishResponse(
                    success=False,
                    message="标题不能为空",
                    error="TITLE_TOO_SHORT"
                )
            
            if len(content.title) > PublishConfig.TITLE_MAX_LENGTH:
                return PublishResponse(
                    success=False,
                    message=f"标题不能超过{PublishConfig.TITLE_MAX_LENGTH}个字符",
                    error="TITLE_TOO_LONG"
                )
            
            # 验证视频文件是否存在
            if not os.path.exists(content.video_path):
                return PublishResponse(
                    success=False,
                    message="视频文件不存在",
                    error="VIDEO_FILE_NOT_FOUND"
                )
            
            # 验证视频格式
            video_ext = Path(content.video_path).suffix.lower()
            if video_ext not in PublishConfig.SUPPORTED_VIDEO_FORMATS:
                return PublishResponse(
                    success=False,
                    message=f"不支持的视频格式: {video_ext}",
                    error="UNSUPPORTED_VIDEO_FORMAT"
                )
            
            # 执行视频发布
            return await self._publish_video(
                title=content.title,
                content=content.content,
                video_path=content.video_path,
                cover_path=content.cover_path,
                tags=content.tags or [],
                username=username,
                context=context
            )
            
        except Exception as e:
            logger.error(f"发布视频失败: {e}")
            return PublishResponse(
                success=False,
                message=f"发布失败: {str(e)}",
                error="PUBLISH_FAILED"
            )
    
    async def get_feeds_list(
        self,
        cursor_score: Optional[str] = None,
        username: Optional[str] = None
    ) -> FeedsListResponse:
        """
        获取推荐动态列表
        
        Args:
            cursor_score: 游标分数，用于分页
            username: 用户名
            
        Returns:
            动态列表响应
        """
        try:
            page = await self.browser_manager.get_page()
            if not page:
                return FeedsListResponse(
                    success=False,
                    error="无法获取浏览器页面"
                )
            
            feeds_action = FeedsAction(page)
            result = await feeds_action.get_feeds(cursor_score)
            
            return result
            
        except Exception as e:
            logger.error(f"获取推荐列表失败: {e}")
            return FeedsListResponse(
                success=False,
                error=f"获取推荐列表失败: {str(e)}"
            )

    async def list_feeds(self, username: Optional[str] = None) -> FeedsListResponse:
        """
        获取首页推荐Feed列表（使用__INITIAL_STATE__方法）
        
        Args:
            username: 用户名（可选）
            
        Returns:
            Feed列表响应
        """
        try:
            page = await self.browser_manager.get_page()
            if not page:
                return FeedsListResponse(
                    success=False,
                    error="无法获取浏览器页面"
                )
            
            feeds_action = FeedsAction(page)
            
            # 导航到首页
            await page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
            
            # 等待页面稳定
            await asyncio.sleep(1)
            
            # 使用__INITIAL_STATE__方法获取推荐内容
            result = await feeds_action._parse_from_initial_state()
            
            if result:
                logger.info(f"成功获取到 {len(result.data.feeds) if result.data else 0} 个推荐内容")
                return result
            else:
                logger.warning("未能从__INITIAL_STATE__获取推荐内容")
                return FeedsListResponse(
                    success=False,
                    error="未能获取推荐内容"
                )
            
        except Exception as e:
            logger.error(f"获取首页推荐失败: {e}")
            return FeedsListResponse(
                success=False,
                error=f"获取首页推荐失败: {str(e)}"
            )
    
    async def search_content(
        self,
        keyword: str,
        page: int = 1,
        username: Optional[str] = None
    ) -> SearchResult:
        """
        搜索内容
        
        Args:
            keyword: 搜索关键词
            page: 页码
            username: 用户名
            
        Returns:
            搜索结果
        """
        try:
            browser_page = await self.browser_manager.get_page()
            if not browser_page:
                return SearchResult(
                    items=[],
                    has_more=False,
                    total=0
                )
            
            search_action = SearchAction(browser_page)
            return await search_action.search(keyword, page)
            
        except Exception as e:
            logger.error(f"搜索内容失败: {e}")
            return SearchResult(
                items=[],
                has_more=False,
                total=0
            )
    
    async def get_user_profile(
        self,
        user_id: str,
        username: Optional[str] = None
    ) -> UserProfileResponse:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            username: 当前用户名
            
        Returns:
            用户资料响应
        """
        try:
            page = await self.browser_manager.get_page()
            if not page:
                return UserProfileResponse(
                    success=False,
                    code=500,
                    msg="无法获取浏览器页面",
                    data=None
                )
            
            user_action = UserAction(page)
            return await user_action.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return UserProfileResponse(
                success=False,
                code=500,
                msg=f"获取用户资料失败: {str(e)}",
                data=None
            )
    
    async def get_feed_detail(
        self,
        note_id: str,
        xsec_token: Optional[str] = None,
        username: Optional[str] = None
    ) -> FeedDetailResponse:
        """
        获取动态详情
        
        Args:
            note_id: 笔记ID
            xsec_token: xsec_token参数（可选）
            username: 用户名
            
        Returns:
            动态详情响应
        """
        try:
            page = await self.browser_manager.get_page()
            if not page:
                return FeedDetailResponse(
                    success=False,
                    code=500,
                    msg="无法获取浏览器页面",
                    data=None
                )
            
            feeds_action = FeedsAction(page)
            return await feeds_action.get_feed_detail(note_id, xsec_token)
            
        except Exception as e:
            logger.error(f"获取动态详情失败: {e}")
            return FeedDetailResponse(
                success=False,
                code=500,
                msg=f"获取动态详情失败: {str(e)}",
                data=None
            )
    
    async def _publish_content(
        self,
        title: str,
        content_text: str,
        images: List[str],
        tags: List[str],
        username: Optional[str] = None,
        context: Optional[Context] = None
    ) -> PublishResponse:
        """
        执行图文内容发布
        
        Args:
            title: 标题
            content_text: 正文
            images: 图片路径列表
            tags: 标签列表
            username: 用户名
            
        Returns:
            发布结果
        """
        page = await self.browser_manager.get_page()
        if not page:
            return PublishResponse(
                success=False,
                message="无法获取浏览器页面",
                error="NO_BROWSER_PAGE"
            )
        
        publish_action = PublishAction(page)
        
        # 创建发布内容
        publish_content = PublishImageContent(
            title=title,
            content=content_text,
            images=images,
            tags=tags
        )
        
        # 执行发布
        return await publish_action.publish(publish_content, context=context)
    
    async def _publish_video(
        self,
        title: str,
        content: str,
        video_path: str,
        cover_path: Optional[str],
        tags: List[str],
        username: Optional[str] = None,
        context: Optional[Context] = None
    ) -> PublishResponse:
        """
        执行视频内容发布
        
        Args:
            title: 标题
            content: 正文内容
            video_path: 视频路径
            cover_path: 封面路径
            tags: 标签列表
            username: 用户名
            
        Returns:
            发布结果
        """
        page = await self.browser_manager.get_page()
        if not page:
            return PublishResponse(
                success=False,
                message="无法获取浏览器页面",
                error="NO_BROWSER_PAGE"
            )
        
        publish_action = PublishAction(page)
        
        # 创建视频发布内容
        video_content = PublishVideoContent(
            title=title,
            content=content,
            video_path=video_path,
            cover_path=cover_path,
            tags=tags
        )
        
        # 执行视频发布
        return await publish_action.publish_video(video_content, context=context)
    
    async def post_comment_to_feed(
        self,
        feed_id: str,
        content: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发表评论到笔记
        
        Args:
            feed_id: 笔记ID
            content: 评论内容
            username: 用户名
            
        Returns:
            评论结果
        """
        try:
            # TODO: 实现评论功能
            # 获取页面控制器
            # page_controller = await self.browser_manager.get_page_controller()
            
            # 创建评论操作
            # comment_action = CommentAction(page_controller)
            
            # 发表评论
            # result = await comment_action.post_comment(feed_id, content)
            
            return {
                "success": False,
                "message": "评论功能尚未实现",
                "error": "NOT_IMPLEMENTED"
            }
            
        except Exception as e:
            logger.error(f"发表评论失败: {e}")
            return {
                "success": False,
                "message": f"发表评论失败: {str(e)}",
                "error": "COMMENT_FAILED"
            }
    
    async def like_feed(
        self,
        feed_id: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        点赞笔记
        
        Args:
            feed_id: 笔记ID
            username: 用户名
            
        Returns:
            点赞结果
        """
        try:
            # TODO: 实现点赞功能
            # 获取页面控制器
            # page_controller = await self.browser_manager.get_page_controller()
            
            # 创建点赞操作
            # like_action = LikeAction(page_controller)
            
            # 执行点赞
            # result = await like_action.like_feed(feed_id)
            
            return {
                "success": False,
                "message": "点赞功能尚未实现",
                "error": "NOT_IMPLEMENTED"
            }
            
        except Exception as e:
            logger.error(f"点赞失败: {e}")
            return {
                "success": False,
                "message": f"点赞失败: {str(e)}",
                "error": "LIKE_FAILED"
            }
    
    async def favorite_feed(
        self,
        feed_id: str,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        收藏笔记
        
        Args:
            feed_id: 笔记ID
            username: 用户名
            
        Returns:
            收藏结果
        """
        try:
            # TODO: 实现收藏功能
            # 获取页面控制器
            # page_controller = await self.browser_manager.get_page_controller()
            
            # 创建收藏操作
            # favorite_action = FavoriteAction(page_controller)
            
            # 执行收藏
            # result = await favorite_action.favorite_feed(feed_id)
            
            return {
                "success": False,
                "message": "收藏功能尚未实现",
                "error": "NOT_IMPLEMENTED"
            }
            
        except Exception as e:
            logger.error(f"收藏失败: {e}")
            return {
                "success": False,
                "message": f"收藏失败: {str(e)}",
                "error": "FAVORITE_FAILED"
            }

    async def cleanup(self):
        """清理资源"""
        try:
            await self.browser_manager.cleanup()
            logger.info("小红书服务清理完成")
        except Exception as e:
            logger.error(f"清理小红书服务失败: {e}")