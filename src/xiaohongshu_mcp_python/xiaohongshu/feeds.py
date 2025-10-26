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

from ..types import FeedsListResponse, FeedData, Feed
from ..config import XiaohongshuUrls, XiaohongshuSelectors, BrowserConfig


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
            
            # 导航到首页
            url = XiaohongshuUrls.HOME_URL
            if cursor:
                url += f"?cursor={cursor}"
            
            await self.page.goto(url, wait_until="networkidle")
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")
            
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
    
    async def _parse_from_initial_state(self) -> Optional[FeedsListResponse]:
        """
        从 __INITIAL_STATE__ 解析推荐内容
        
        Returns:
            推荐内容响应
        """
        try:
            # 获取页面中的 __INITIAL_STATE__ 数据
            initial_state_script = await self.page.query_selector(
                "script:has-text('__INITIAL_STATE__')"
            )
            
            if not initial_state_script:
                logger.debug("未找到 __INITIAL_STATE__ 脚本")
                return None
            
            script_content = await initial_state_script.text_content()
            if not script_content:
                return None
            
            # 提取JSON数据
            match = re.search(r'__INITIAL_STATE__\s*=\s*({.+?});', script_content)
            if not match:
                logger.debug("未找到 __INITIAL_STATE__ 数据")
                return None
            
            json_str = match.group(1)
            data = json.loads(json_str)
            
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
            # 根据小红书的数据结构提取推荐内容
            # 这里需要根据实际的数据结构调整
            home_data = data.get("home", {})
            if not home_data:
                # 尝试其他可能的路径
                home_data = data.get("feed", {}) or data.get("recommend", {})
            
            if not home_data:
                return None
            
            feeds_data = home_data.get("feeds", [])
            if not feeds_data:
                # 尝试其他可能的字段名
                feeds_data = home_data.get("items", []) or home_data.get("list", [])
            
            if not feeds_data:
                return None
            
            # 转换为Feed对象
            feeds = []
            for feed_data in feeds_data:
                try:
                    feed = self._convert_data_to_feed(feed_data)
                    if feed:
                        feeds.append(feed)
                except Exception as e:
                    logger.debug(f"转换推荐项失败: {e}")
                    continue
            
            # 获取分页信息
            cursor = home_data.get("cursor", "")
            has_more = home_data.get("has_more", False)
            
            return FeedsListResponse(
                data=FeedData(
                    feeds=feeds,
                    cursor=cursor,
                    has_more=has_more
                )
            )
            
        except Exception as e:
            logger.debug(f"提取推荐数据失败: {e}")
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
            # 这里需要根据实际的数据结构进行转换
            # 以下是示例结构，需要根据实际情况调整
            
            note_card_data = feed_data.get("note_card", {})
            if not note_card_data:
                return None
            
            from ..types import Feed, NoteCard, User, InteractInfo, Cover, ImageInfo, Video
            
            # 用户信息
            user_data = note_card_data.get("user", {})
            user = User(
                user_id=user_data.get("user_id", ""),
                nickname=user_data.get("nickname", ""),
                avatar=user_data.get("avatar", ""),
                desc=user_data.get("desc", ""),
                gender=user_data.get("gender"),
                ip_location=user_data.get("ip_location", "")
            )
            
            # 互动信息
            interact_data = note_card_data.get("interact_info", {})
            interact_info = InteractInfo(
                liked=interact_data.get("liked", False),
                liked_count=str(interact_data.get("liked_count", 0)),
                collected=interact_data.get("collected", False),
                collected_count=str(interact_data.get("collected_count", 0)),
                comment_count=str(interact_data.get("comment_count", 0)),
                share_count=str(interact_data.get("share_count", 0))
            )
            
            # 封面信息
            cover_data = note_card_data.get("cover", {})
            cover = Cover(
                url=cover_data.get("url", ""),
                width=cover_data.get("width", 0),
                height=cover_data.get("height", 0),
                file_id=cover_data.get("file_id")
            )
            
            # 图片列表
            images_list = []
            images_data = note_card_data.get("images_list", [])
            for img_data in images_data:
                image_info = ImageInfo(
                    url=img_data.get("url", ""),
                    width=img_data.get("width", 0),
                    height=img_data.get("height", 0),
                    file_id=img_data.get("file_id")
                )
                images_list.append(image_info)
            
            # 视频信息
            video = None
            video_data = note_card_data.get("video", {})
            if video_data:
                from ..types import VideoCapability
                
                capability_data = video_data.get("capability", {})
                capability = VideoCapability(
                    adaptive_url=capability_data.get("adaptive_url", ""),
                    definition=capability_data.get("definition", ""),
                    duration=capability_data.get("duration", 0),
                    size=capability_data.get("size", 0),
                    url=capability_data.get("url", "")
                )
                
                video = Video(
                    url=video_data.get("url", ""),
                    width=video_data.get("width", 0),
                    height=video_data.get("height", 0),
                    file_id=video_data.get("file_id"),
                    capability=capability
                )
            
            # 笔记卡片
            note_card = NoteCard(
                type=note_card_data.get("type", ""),
                display_title=note_card_data.get("display_title", ""),
                user=user,
                interact_info=interact_info,
                cover=cover,
                images_list=images_list if images_list else None,
                video=video
            )
            
            # Feed对象
            feed = Feed(
                id=feed_data.get("id", ""),
                model_type=feed_data.get("model_type", ""),
                note_card=note_card,
                track_id=feed_data.get("track_id")
            )
            
            return feed
            
        except Exception as e:
            logger.debug(f"转换推荐数据失败: {e}")
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
            from ..types import Feed, NoteCard, User, InteractInfo, Cover
            
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
            
            # 滚动加载
            for i in range(scroll_count):
                # 滚动到页面底部
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # 等待新内容加载
                await asyncio.sleep(2)
                
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