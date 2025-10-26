"""
小红书搜索功能
实现内容搜索和结果解析
"""

import asyncio
import json
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger

from ..types import SearchResult, Feed, FeedData
from ..config import XiaohongshuUrls, XiaohongshuSelectors, BrowserConfig


class SearchAction:
    """搜索操作类"""
    
    def __init__(self, page: Page):
        """
        初始化搜索操作
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
    
    async def search(self, keyword: str, page_num: int = 1) -> SearchResult:
        """
        搜索内容
        
        Args:
            keyword: 搜索关键词
            page_num: 页码
            
        Returns:
            搜索结果
        """
        try:
            logger.info(f"开始搜索: {keyword}, 页码: {page_num}")
            
            # 构建搜索URL
            search_url = self._make_search_url(keyword, page_num)
            
            # 导航到搜索页面
            await self.page.goto(search_url, wait_until="networkidle")
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")
            
            # 解析搜索结果
            result = await self._parse_search_results()
            
            logger.info(f"搜索完成，找到 {len(result.items)} 个结果")
            return result
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return SearchResult(
                items=[],
                has_more=False,
                total=0
            )
    
    def _make_search_url(self, keyword: str, page_num: int = 1) -> str:
        """
        构建搜索URL
        
        Args:
            keyword: 搜索关键词
            page_num: 页码
            
        Returns:
            搜索URL
        """
        encoded_keyword = quote(keyword)
        return f"{XiaohongshuUrls.SEARCH_URL}?keyword={encoded_keyword}&page={page_num}"
    
    async def _parse_search_results(self) -> SearchResult:
        """
        解析搜索结果
        
        Returns:
            搜索结果
        """
        try:
            # 方法1: 尝试从 __INITIAL_STATE__ 解析
            initial_state_result = await self._parse_from_initial_state()
            if initial_state_result and initial_state_result.items:
                return initial_state_result
            
            # 方法2: 从DOM元素解析
            dom_result = await self._parse_from_dom()
            return dom_result
            
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
            return SearchResult(
                items=[],
                has_more=False,
                total=0
            )
    
    async def _parse_from_initial_state(self) -> Optional[SearchResult]:
        """
        从 __INITIAL_STATE__ 解析搜索结果
        
        Returns:
            搜索结果
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
            
            # 解析搜索结果数据
            return self._extract_search_data_from_state(data)
            
        except Exception as e:
            logger.debug(f"从 __INITIAL_STATE__ 解析失败: {e}")
            return None
    
    def _extract_search_data_from_state(self, data: Dict[str, Any]) -> Optional[SearchResult]:
        """
        从状态数据中提取搜索结果
        
        Args:
            data: 状态数据
            
        Returns:
            搜索结果
        """
        try:
            # 根据小红书的数据结构提取搜索结果
            # 这里需要根据实际的数据结构调整
            search_data = data.get("search", {})
            if not search_data:
                return None
            
            items_data = search_data.get("items", [])
            if not items_data:
                return None
            
            # 转换为Feed对象
            feeds = []
            for item_data in items_data:
                try:
                    feed = self._convert_item_to_feed(item_data)
                    if feed:
                        feeds.append(feed)
                except Exception as e:
                    logger.debug(f"转换搜索项失败: {e}")
                    continue
            
            # 获取分页信息
            has_more = search_data.get("has_more", False)
            total = search_data.get("total", len(feeds))
            cursor = search_data.get("cursor")
            
            return SearchResult(
                items=feeds,
                has_more=has_more,
                total=total,
                cursor=cursor
            )
            
        except Exception as e:
            logger.debug(f"提取搜索数据失败: {e}")
            return None
    
    def _convert_item_to_feed(self, item_data: Dict[str, Any]) -> Optional[Feed]:
        """
        将搜索项数据转换为Feed对象
        
        Args:
            item_data: 搜索项数据
            
        Returns:
            Feed对象
        """
        try:
            # 这里需要根据实际的数据结构进行转换
            # 以下是示例结构，需要根据实际情况调整
            
            note_card_data = item_data.get("note_card", {})
            if not note_card_data:
                return None
            
            from ..types import Feed, NoteCard, User, InteractInfo, Cover, ImageInfo
            
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
            
            # 笔记卡片
            note_card = NoteCard(
                type=note_card_data.get("type", ""),
                display_title=note_card_data.get("display_title", ""),
                user=user,
                interact_info=interact_info,
                cover=cover,
                images_list=images_list if images_list else None
            )
            
            # Feed对象
            feed = Feed(
                id=item_data.get("id", ""),
                model_type=item_data.get("model_type", ""),
                note_card=note_card,
                track_id=item_data.get("track_id")
            )
            
            return feed
            
        except Exception as e:
            logger.debug(f"转换搜索项数据失败: {e}")
            return None
    
    async def _parse_from_dom(self) -> SearchResult:
        """
        从DOM元素解析搜索结果
        
        Returns:
            搜索结果
        """
        try:
            logger.debug("从DOM解析搜索结果")
            
            # 等待搜索结果加载
            await self.page.wait_for_selector(
                XiaohongshuSelectors.SEARCH_RESULT_ITEM,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            # 获取所有搜索结果项
            result_items = await self.page.query_selector_all(
                XiaohongshuSelectors.SEARCH_RESULT_ITEM
            )
            
            feeds = []
            for item in result_items:
                try:
                    feed = await self._extract_feed_from_element(item)
                    if feed:
                        feeds.append(feed)
                except Exception as e:
                    logger.debug(f"提取搜索项失败: {e}")
                    continue
            
            # 检查是否有更多结果
            has_more = await self._check_has_more()
            
            return SearchResult(
                items=feeds,
                has_more=has_more,
                total=len(feeds)
            )
            
        except PlaywrightTimeoutError:
            logger.warning("等待搜索结果超时")
            return SearchResult(
                items=[],
                has_more=False,
                total=0
            )
        except Exception as e:
            logger.error(f"从DOM解析搜索结果失败: {e}")
            return SearchResult(
                items=[],
                has_more=False,
                total=0
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
            
            # 构建基本的Feed对象
            user = User(
                user_id="",
                nickname=author,
                avatar="",
                desc="",
                ip_location=""
            )
            
            interact_info = InteractInfo()
            
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
        检查是否有更多结果
        
        Returns:
            是否有更多结果
        """
        try:
            # 检查是否有"加载更多"按钮或分页
            load_more = await self.page.query_selector("text=加载更多")
            if load_more:
                return True
            
            # 检查分页
            next_page = await self.page.query_selector(".pagination .next")
            if next_page:
                return True
            
            return False
            
        except Exception:
            return False