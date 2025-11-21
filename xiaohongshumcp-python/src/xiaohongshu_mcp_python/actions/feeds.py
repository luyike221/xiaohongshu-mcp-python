"""
小红书推荐功能
实现首页推荐内容获取和解析
"""

import asyncio
import json
import re
from typing import List, Optional, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger

from ..config import (
    FeedsListResponse,
    FeedData,
    Feed,
    FeedDetailResponse,
    FeedDetail,
    CommentList,
    FeedDetailData,
    XiaohongshuUrls,
    XiaohongshuSelectors,
    BrowserConfig,
)
from ..utils.anti_bot import AntiBotStrategy


class FeedsAction:
    """推荐内容操作类"""
    
    def __init__(self, page: Page):
        """
        初始化推荐操作
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
    
    async def get_feeds(self, cursor: Optional[str] = None) -> FeedsListResponse:
        """
        获取推荐内容
        
        Args:
            cursor: 分页游标
            
        Returns:
            推荐内容响应
        """
        try:
            logger.info(f"开始获取推荐内容, cursor: {cursor}")
            
            # 添加随机延迟，模拟人类行为
            await AntiBotStrategy.add_random_delay(seed=str(cursor or ""))
            
            # 导航到首页
            url = XiaohongshuUrls.HOME_URL
            if cursor:
                url += f"?cursor={cursor}"
            
            # 使用统一的反爬虫导航策略
            await AntiBotStrategy.simulate_human_navigation(self.page, url)
            
            # 解析推荐内容
            result = await self._parse_feeds()
            
            logger.info(f"获取推荐内容完成，找到 {len(result.data.feeds)} 个内容")
            return result
            
        except Exception as e:
            logger.error(f"获取推荐内容失败: {e}")
            return FeedsListResponse(
                data=FeedData(
                    feeds=[],
                    cursor="",
                    has_more=False
                )
            )
    
    async def _parse_feeds(self) -> FeedsListResponse:
        """
        解析推荐内容
        
        Returns:
            推荐内容响应
        """
        try:
            # 方法1: 尝试从 __INITIAL_STATE__ 解析
            initial_state_result = await self._parse_from_initial_state()
            if initial_state_result and initial_state_result.data.feeds:
                return initial_state_result
            
            # 方法2: 从DOM元素解析
            dom_result = await self._parse_from_dom()
            return dom_result
            
        except Exception as e:
            logger.error(f"解析推荐内容失败: {e}")
            return FeedsListResponse(
                data=FeedData(
                    feeds=[],
                    cursor="",
                    has_more=False
                )
            )
    
    async def get_feed_detail(self, note_id: str, xsec_token: Optional[str] = None) -> FeedDetailResponse:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
            xsec_token: xsec_token参数（可选）
            
        Returns:
            笔记详情响应
        """
        try:
            logger.info(f"开始获取笔记详情, note_id: {note_id}")
            
            # 构建详情页URL
            url = self._make_feed_detail_url(note_id, xsec_token)
            
            # 添加随机延迟，模拟人类行为
            await AntiBotStrategy.add_random_delay(seed=note_id)
            
            # 使用统一的反爬虫导航策略
            await AntiBotStrategy.simulate_human_navigation(self.page, url)
            logger.info("页面加载完成")
            
            # 使用专门用于笔记详情页的数据提取方法（去除Vue响应式）
            result = await AntiBotStrategy.extract_feed_detail_state(self.page)
            logger.info(f"获取到的 __INITIAL_STATE__ 数据长度: {len(result)}")
            
            if not result:
                logger.error("未找到 __INITIAL_STATE__ 数据")
                return FeedDetailResponse(
                    success=False,
                    code=500,
                    msg="未找到页面数据",
                    data=None
                )
            
            # 解析JSON数据
            initial_state = json.loads(result)
            
            # 从 noteDetailMap 中获取对应 note_id 的数据
            note_detail_map = initial_state.get("note", {}).get("noteDetailMap", {})
            note_detail = note_detail_map.get(note_id)
            
            if not note_detail:
                logger.error(f"在 noteDetailMap 中未找到笔记 {note_id}")
                return FeedDetailResponse(
                    success=False,
                    code=404,
                    msg=f"未找到笔记 {note_id}",
                    data=None
                )
            
            # 解析笔记详情数据
            feed_detail = self._parse_feed_detail(note_detail.get("note", {}))
            
            # 解析评论数据（如果存在）
            comments_data = note_detail.get("comments", {})
            comment_list = None
            if comments_data:
                comment_list = self._parse_comment_list(comments_data)
            
            # 构建详情数据
            detail_data = FeedDetailData(
                note=feed_detail,
                comments=comment_list
            )
            
            logger.info(f"获取笔记详情成功: {note_id}")
            return FeedDetailResponse(
                success=True,
                code=200,
                msg="获取成功",
                data=detail_data
            )
            
        except Exception as e:
            logger.error(f"获取笔记详情失败: {e}")
            return FeedDetailResponse(
                success=False,
                code=500,
                msg=f"获取笔记详情失败: {str(e)}",
                data=None
            )
    
    def _make_feed_detail_url(self, note_id: str, xsec_token: Optional[str] = None) -> str:
        """
        构建笔记详情页URL
        
        Args:
            note_id: 笔记ID
            xsec_token: xsec_token参数
            
        Returns:
            详情页URL
        """
        base_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if xsec_token:
            base_url += f"?xsec_token={xsec_token}&xsec_source=pc_feed"
        return base_url
    
    def _parse_feed_detail(self, note_data: Dict[str, Any]) -> FeedDetail:
        """
        解析笔记详情数据
        
        Args:
            note_data: 原始笔记数据
            
        Returns:
            解析后的笔记详情
        """
        from ..config import User, InteractInfo, DetailImageInfo
        
        # 解析用户信息
        user_data = note_data.get("user", {})
        user = User(
            user_id=user_data.get("userId", ""),
            nickname=user_data.get("nickname", ""),
            avatar=user_data.get("avatar", ""),
            desc=user_data.get("desc", ""),
            gender=user_data.get("gender"),
            ip_location=user_data.get("ipLocation", "")
        )
        
        # 解析互动信息
        interact_data = note_data.get("interactInfo", {})
        interact_info = InteractInfo(
            liked=interact_data.get("liked", False),
            liked_count=str(interact_data.get("likedCount", 0)),
            collected=interact_data.get("collected", False),
            collected_count=str(interact_data.get("collectedCount", 0)),
            comment_count=str(interact_data.get("commentCount", 0)),
            share_count=str(interact_data.get("shareCount", 0))
        )
        
        # 解析图片列表
        image_list = []
        images_data = note_data.get("imageList", [])
        for img_data in images_data:
            # 处理 live_photo 字段：如果是布尔值或非字典类型，设置为 None
            live_photo = img_data.get("livePhoto")
            if live_photo is not None and not isinstance(live_photo, dict):
                # 如果是布尔值 False 或其他非字典类型，设置为 None
                live_photo = None
            
            image_info = DetailImageInfo(
                url=img_data.get("url", ""),
                width=img_data.get("width", 0),
                height=img_data.get("height", 0),
                file_id=img_data.get("fileId"),
                live_photo=live_photo,
                format=img_data.get("format")
            )
            image_list.append(image_info)
        
        # 解析视频信息（如果存在）
        video_data = note_data.get("video")
        parsed_video = None
        
        if video_data and isinstance(video_data, dict):
            try:
                from ..config import Video, VideoCapability
                
                # 提取视频信息，处理不同的数据结构
                # 支持多种字段名变体
                video_id = (video_data.get("videoId") or 
                           video_data.get("video_id") or 
                           video_data.get("id") or "")
                
                # 从不同位置提取视频属性
                capa = video_data.get("capa", {})
                duration = (video_data.get("duration") or 
                           capa.get("duration") or 0)
                width = (video_data.get("width") or 
                        capa.get("width") or 0)
                height = (video_data.get("height") or 
                         capa.get("height") or 0)
                
                master_url = (video_data.get("masterUrl") or 
                            video_data.get("master_url") or 
                            video_data.get("url") or "")
                
                backup_urls = (video_data.get("backupUrls") or 
                              video_data.get("backup_urls") or [])
                if not isinstance(backup_urls, list):
                    backup_urls = []
                
                stream = video_data.get("stream") or {}
                if not isinstance(stream, dict):
                    stream = {}
                
                media = video_data.get("media") or {}
                if not isinstance(media, dict):
                    media = {}
                
                # 解析视频编码能力
                h264 = []
                h265 = []
                av1 = []
                
                def parse_capabilities(cap_list):
                    """解析编码能力列表"""
                    result = []
                    if cap_list and isinstance(cap_list, list):
                        for item in cap_list:
                            if isinstance(item, dict):
                                try:
                                    result.append(VideoCapability(**item))
                                except Exception:
                                    # 如果解析失败，尝试使用默认值
                                    result.append(VideoCapability(
                                        adaptive_type=item.get("adaptive_type", 0),
                                        media_type=item.get("media_type", 0),
                                        profile=item.get("profile", ""),
                                        quality_type=item.get("quality_type", 0)
                                    ))
                    return result
                
                h264 = parse_capabilities(video_data.get("h264"))
                h265 = parse_capabilities(video_data.get("h265"))
                av1 = parse_capabilities(video_data.get("av1"))
                
                # 只有当有足够信息时才创建 Video 对象
                # 至少需要有 video_id 或 master_url 或 duration
                if video_id or master_url or (duration and duration > 0):
                    parsed_video = Video(
                        media=media,
                        video_id=video_id or "",
                        duration=int(duration) if duration else 0,
                        width=int(width) if width else 0,
                        height=int(height) if height else 0,
                        master_url=master_url or "",
                        backup_urls=backup_urls,
                        stream=stream,
                        h264=h264,
                        h265=h265,
                        av1=av1
                    )
                else:
                    logger.debug("视频数据不完整，跳过视频对象创建")
            except Exception as e:
                logger.warning(f"解析视频数据失败: {e}，跳过视频字段")
                parsed_video = None
        
        # 构建笔记详情对象
        feed_detail = FeedDetail(
            note_id=note_data.get("noteId", ""),
            title=note_data.get("title", ""),
            desc=note_data.get("desc", ""),
            type=note_data.get("type", ""),
            user=user,
            interact_info=interact_info,
            image_list=image_list if image_list else None,
            video=parsed_video,
            tag_list=note_data.get("tagList"),
            at_user_list=note_data.get("atUserList"),
            collected_count=str(interact_data.get("collectedCount", 0)),
            comment_count=str(interact_data.get("commentCount", 0)),
            liked_count=str(interact_data.get("likedCount", 0)),
            share_count=str(interact_data.get("shareCount", 0)),
            time=note_data.get("time", 0),
            last_update_time=note_data.get("lastUpdateTime", 0)
        )
        
        return feed_detail
    
    def _parse_comment_list(self, comments_data: Dict[str, Any]) -> CommentList:
        """
        解析评论列表数据
        
        Args:
            comments_data: 原始评论数据
            
        Returns:
            解析后的评论列表
        """
        from ..config import Comment, User
        
        comments = []
        comment_list_data = comments_data.get("list", [])
        
        for comment_data in comment_list_data:
            # 解析评论用户信息
            user_info = comment_data.get("userInfo", {})
            user = User(
                user_id=user_info.get("userId", ""),
                nickname=user_info.get("nickname", ""),
                avatar=user_info.get("avatar", ""),
                desc=user_info.get("desc", ""),
                gender=user_info.get("gender"),
                ip_location=user_info.get("ipLocation", "")
            )
            
            # 解析子评论
            sub_comments = []
            sub_comments_data = comment_data.get("subComments", [])
            for sub_comment_data in sub_comments_data:
                sub_user_info = sub_comment_data.get("userInfo", {})
                sub_user = User(
                    user_id=sub_user_info.get("userId", ""),
                    nickname=sub_user_info.get("nickname", ""),
                    avatar=sub_user_info.get("avatar", ""),
                    desc=sub_user_info.get("desc", ""),
                    gender=sub_user_info.get("gender"),
                    ip_location=sub_user_info.get("ipLocation", "")
                )
                
                sub_comment = Comment(
                    id=sub_comment_data.get("id", ""),
                    content=sub_comment_data.get("content", ""),
                    create_time=sub_comment_data.get("createTime", 0),
                    ip_location=sub_comment_data.get("ipLocation", ""),
                    like_count=int(sub_comment_data.get("likeCount", 0)),
                    user=sub_user,
                    sub_comments=None,
                    sub_comment_count=0
                )
                sub_comments.append(sub_comment)
            
            # 构建评论对象
            comment = Comment(
                id=comment_data.get("id", ""),
                content=comment_data.get("content", ""),
                create_time=comment_data.get("createTime", 0),
                ip_location=comment_data.get("ipLocation", ""),
                like_count=int(comment_data.get("likeCount", 0)),
                user=user,
                sub_comments=sub_comments if sub_comments else None,
                sub_comment_count=int(comment_data.get("subCommentCount", 0))
            )
            comments.append(comment)
        
        return CommentList(
            comments=comments,
            cursor=comments_data.get("cursor", ""),
            has_more=comments_data.get("hasMore", False),
            time=comments_data.get("time", 0)
        )
    
    async def _parse_from_initial_state(self) -> Optional[FeedsListResponse]:
        """
        从 __INITIAL_STATE__ 解析推荐内容
        
        Returns:
            推荐内容响应
        """
        try:
            # 等待 __INITIAL_STATE__ 可用（参考search.py的实现）
            await self.page.wait_for_function("() => window.__INITIAL_STATE__ !== undefined", timeout=10000)
            
            # 获取 __INITIAL_STATE__ 数据（参考search.py的实现）
            initial_state_js = """
            () => {
                if (window.__INITIAL_STATE__) {
                    // 安全地序列化，避免循环引用
                    try {
                        return JSON.stringify(window.__INITIAL_STATE__, (key, value) => {
                            // 跳过可能导致循环引用的属性
                            if (key === 'dep' || key === 'computed' || typeof value === 'function') {
                                return undefined;
                            }
                            return value;
                        });
                    } catch (e) {
                        // 如果还是有问题，只提取我们需要的部分
                        const state = window.__INITIAL_STATE__;
                        if (state && state.feed && state.feed.feeds) {
                            return JSON.stringify({
                                feed: {
                                    feeds: state.feed.feeds
                                }
                            });
                        }
                        return "{}";
                    }
                }
                return "";
            }
            """
            
            result = await self.page.evaluate(initial_state_js)
            
            if not result:
                logger.debug("未找到 __INITIAL_STATE__ 数据")
                return None
            
            # 解析JSON数据
            data = json.loads(result)
            
            # 解析推荐内容数据
            return self._extract_feeds_data_from_state(data)
            
        except Exception as e:
            logger.debug(f"从 __INITIAL_STATE__ 解析失败: {e}")
            return None
    
    def _extract_feeds_data_from_state(self, data: Dict[str, Any]) -> Optional[FeedsListResponse]:
        """
        从状态数据中提取推荐内容
        
        Args:
            data: 状态数据
            
        Returns:
            推荐内容响应
        """
        try:
            # 数据路径是 feed.feeds._value
            feed_data = data.get("feed", {})
            if not feed_data:
                logger.debug("未找到feed数据")
                return None
            
            feeds_container = feed_data.get("feeds", {})
            if not feeds_container:
                logger.debug("未找到feeds容器")
                return None
            
            feeds_list = feeds_container.get("_value", [])
            if not feeds_list:
                logger.debug("未找到feeds列表")
                return None
            
            # 转换为Feed对象
            feeds = []
            for item in feeds_list:
                try:
                    feed = self._convert_data_to_feed(item)
                    if feed:
                        feeds.append(feed)
                except Exception as e:
                    logger.debug(f"转换推荐项失败: {e}")
                    continue
            
            # 获取分页信息（如果有的话）
            cursor = feeds_container.get("cursor", "")
            has_more = feeds_container.get("hasMore", False)
            
            logger.info(f"成功解析到 {len(feeds)} 个推荐内容")
            
            return FeedsListResponse(
                data=FeedData(
                    feeds=feeds,
                    cursor=cursor,
                    has_more=has_more
                )
            )
            
        except Exception as e:
            logger.error(f"提取推荐数据失败: {e}")
            return None
    
    def _convert_data_to_feed(self, feed_data: Dict[str, Any]) -> Optional[Feed]:
        """
        将数据转换为Feed对象
        
        Args:
            feed_data: 推荐项数据
            
        Returns:
            Feed对象
        """
        try:
            # 数据结构转换
            from ..config import Feed, NoteCard, User, InteractInfo, Cover, ImageInfo, Video
            
            # 获取基本信息
            feed_id = feed_data.get("id", "")
            model_type = feed_data.get("modelType", "")
            xsec_token = feed_data.get("xsecToken", "")
            index = feed_data.get("index", 0)
            
            # 获取笔记卡片数据
            note_card_data = feed_data.get("noteCard", {})
            if not note_card_data:
                logger.debug(f"Feed {feed_id} 缺少noteCard数据")
                return None
            
            # 用户信息
            user_data = note_card_data.get("user", {})
            user = User(
                user_id=user_data.get("userId", ""),
                nickname=user_data.get("nickname", ""),
                avatar=user_data.get("avatar", ""),
                desc=user_data.get("desc", ""),
                gender=user_data.get("gender"),
                ip_location=user_data.get("ipLocation", "")
            )
            
            # 互动信息
            interact_data = note_card_data.get("interactInfo", {})
            interact_info = InteractInfo(
                liked=interact_data.get("liked", False),
                liked_count=str(interact_data.get("likedCount", 0)),
                collected=interact_data.get("collected", False),
                collected_count=str(interact_data.get("collectedCount", 0)),
                comment_count=str(interact_data.get("commentCount", 0)),
                share_count=str(interact_data.get("shareCount", 0))
            )
            
            # 封面信息
            cover_data = note_card_data.get("cover", {})
            cover = Cover(
                url=cover_data.get("url", ""),
                width=cover_data.get("width", 0),
                height=cover_data.get("height", 0),
                file_id=cover_data.get("fileId")
            )
            
            # 视频信息（如果存在）
            video = None
            video_data = note_card_data.get("video", {})
            if video_data:
                # 视频结构处理，简化处理
                video = Video(
                    media=video_data.get("media", {}),
                    video_id=video_data.get("videoId", ""),
                    duration=video_data.get("capa", {}).get("duration", 0),
                    width=video_data.get("width", 0),
                    height=video_data.get("height", 0),
                    master_url=video_data.get("masterUrl", ""),
                    backup_urls=video_data.get("backupUrls", []),
                    stream=video_data.get("stream", {}),
                    h264=[],  # 简化处理
                    h265=[],  # 简化处理
                    av1=[]    # 简化处理
                )
            
            # 笔记卡片
            note_card = NoteCard(
                type=note_card_data.get("type", ""),
                display_title=note_card_data.get("displayTitle", ""),
                user=user,
                interact_info=interact_info,
                cover=cover,
                images_list=None,  # 暂时不处理图片列表
                video=video
            )
            
            # Feed对象
            feed = Feed(
                id=feed_id,
                model_type=model_type,
                note_card=note_card,
                track_id=feed_data.get("trackId"),
                xsec_token=xsec_token,
                index=index
            )
            
            return feed
            
        except Exception as e:
            logger.error(f"转换推荐数据失败: {e}")
            return None
    
    async def _parse_from_dom(self) -> FeedsListResponse:
        """
        从DOM元素解析推荐内容
        
        Returns:
            推荐内容响应
        """
        try:
            logger.debug("从DOM解析推荐内容")
            
            # 等待推荐内容加载
            await self.page.wait_for_selector(
                XiaohongshuSelectors.FEED_ITEM,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            # 获取所有推荐内容项
            feed_items = await self.page.query_selector_all(
                XiaohongshuSelectors.FEED_ITEM
            )
            
            feeds = []
            for item in feed_items:
                try:
                    feed = await self._extract_feed_from_element(item)
                    if feed:
                        feeds.append(feed)
                except Exception as e:
                    logger.debug(f"提取推荐项失败: {e}")
                    continue
            
            # 检查是否有更多内容
            has_more = await self._check_has_more()
            
            return FeedsListResponse(
                data=FeedData(
                    feeds=feeds,
                    cursor="",
                    has_more=has_more
                )
            )
            
        except PlaywrightTimeoutError:
            logger.warning("等待推荐内容超时")
            return FeedsListResponse(
                data=FeedData(
                    feeds=[],
                    cursor="",
                    has_more=False
                )
            )
        except Exception as e:
            logger.error(f"从DOM解析推荐内容失败: {e}")
            return FeedsListResponse(
                data=FeedData(
                    feeds=[],
                    cursor="",
                    has_more=False
                )
            )
    
    async def _extract_feed_from_element(self, element) -> Optional[Feed]:
        """
        从DOM元素提取Feed信息
        
        Args:
            element: DOM元素
            
        Returns:
            Feed对象
        """
        try:
            from ..config import Feed, NoteCard, User, InteractInfo, Cover
            
            # 提取标题
            title_element = await element.query_selector(XiaohongshuSelectors.FEED_TITLE)
            title = await title_element.text_content() if title_element else ""
            
            # 提取作者
            author_element = await element.query_selector(XiaohongshuSelectors.FEED_AUTHOR)
            author = await author_element.text_content() if author_element else ""
            
            # 提取封面
            cover_element = await element.query_selector(XiaohongshuSelectors.FEED_COVER)
            cover_url = await cover_element.get_attribute("src") if cover_element else ""
            
            # 提取链接（用作ID）
            link_element = await element.query_selector("a")
            href = await link_element.get_attribute("href") if link_element else ""
            note_id = self._extract_note_id_from_url(href) if href else ""
            
            # 提取互动数据
            like_element = await element.query_selector(XiaohongshuSelectors.LIKE_COUNT)
            like_count = await like_element.text_content() if like_element else "0"
            
            # 构建基本的Feed对象
            user = User(
                user_id="",
                nickname=author,
                avatar="",
                desc="",
                ip_location=""
            )
            
            interact_info = InteractInfo(
                liked_count=like_count
            )
            
            cover = Cover(
                url=cover_url,
                width=0,
                height=0
            )
            
            note_card = NoteCard(
                type="normal",
                display_title=title,
                user=user,
                interact_info=interact_info,
                cover=cover
            )
            
            feed = Feed(
                id=note_id,
                model_type="note",
                note_card=note_card
            )
            
            return feed
            
        except Exception as e:
            logger.debug(f"从元素提取Feed失败: {e}")
            return None
    
    def _extract_note_id_from_url(self, url: str) -> str:
        """
        从URL中提取笔记ID
        
        Args:
            url: URL
            
        Returns:
            笔记ID
        """
        try:
            if "/item/" in url:
                return url.split("/item/")[-1].split("?")[0]
            return ""
        except Exception:
            return ""
    
    async def _check_has_more(self) -> bool:
        """
        检查是否有更多内容
        
        Returns:
            是否有更多内容
        """
        try:
            # 检查是否有"加载更多"按钮
            load_more = await self.page.query_selector("text=加载更多")
            if load_more:
                return True
            
            # 检查是否可以滚动加载更多
            # 滚动到页面底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # 检查是否有新内容加载
            new_items = await self.page.query_selector_all(XiaohongshuSelectors.FEED_ITEM)
            return len(new_items) > 0
            
        except Exception:
            return False
    
    async def load_more_feeds(self, scroll_count: int = 3) -> FeedsListResponse:
        """
        通过滚动加载更多推荐内容
        
        Args:
            scroll_count: 滚动次数
            
        Returns:
            推荐内容响应
        """
        try:
            logger.info(f"开始滚动加载更多内容，滚动次数: {scroll_count}")
            
            # 记录当前内容数量
            current_items = await self.page.query_selector_all(XiaohongshuSelectors.FEED_ITEM)
            initial_count = len(current_items)
            
            # 滚动加载 - 使用统一的反爬虫策略
            for i in range(scroll_count):
                # 添加随机延迟，模拟人类行为
                await AntiBotStrategy.add_random_delay(base_delay=1.0, max_extra=2, seed=str(i))
                
                # 使用统一的自然滚动策略
                await AntiBotStrategy.simulate_natural_scrolling(self.page, scroll_count=3)
                
                # 等待页面稳定
                await AntiBotStrategy.wait_for_page_stable(self.page)
                
                # 检查是否有新内容
                new_items = await self.page.query_selector_all(XiaohongshuSelectors.FEED_ITEM)
                if len(new_items) <= initial_count:
                    logger.info(f"第 {i+1} 次滚动后没有新内容")
                    break
                
                initial_count = len(new_items)
                logger.info(f"第 {i+1} 次滚动后加载了 {len(new_items)} 个内容")
            
            # 解析所有内容
            return await self._parse_feeds()
            
        except Exception as e:
            logger.error(f"滚动加载更多内容失败: {e}")
            return FeedsListResponse(
                data=FeedData(
                    feeds=[],
                    cursor="",
                    has_more=False
                )
            )