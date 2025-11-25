"""
小红书搜索功能实现
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from ..config import Feed, SearchResult


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
            # 构建搜索URL
            search_url = self._make_search_url(keyword)
            logger.info(f"搜索URL: {search_url}")
            
            # 导航到搜索页面
            await self.page.goto(search_url, wait_until="networkidle")
            
            # 等待页面稳定
            await self.page.wait_for_load_state("networkidle")
            
            # 等待 __INITIAL_STATE__ 可用
            await self.page.wait_for_function("() => window.__INITIAL_STATE__ !== undefined")
            
            # 获取 __INITIAL_STATE__ 数据
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
                        if (state && state.Main && state.Main.feedData) {
                            return JSON.stringify({
                                Main: {
                                    feedData: state.Main.feedData
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
                logger.warning("未找到 __INITIAL_STATE__ 数据")
                return SearchResult(items=[], has_more=False, total=0)
            
            
            # 解析搜索结果
            return await self._parse_search_results_from_state(result)
            
        except PlaywrightTimeoutError as e:
            logger.error(f"搜索超时: {e}")
            return SearchResult(items=[], has_more=False, total=0)
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return SearchResult(items=[], has_more=False, total=0)
    
    def _make_search_url(self, keyword: str) -> str:
        """
        构建搜索URL
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            搜索URL
        """
        params = {
            "keyword": keyword,
            "source": "web_explore_feed"
        }
        query_string = urlencode(params)
        return f"https://www.xiaohongshu.com/search_result?{query_string}"
    
    async def _parse_search_results_from_state(self, state_json: str) -> SearchResult:
        """
        从 __INITIAL_STATE__ 解析搜索结果
        
        Args:
            state_json: __INITIAL_STATE__ 的JSON字符串
            
        Returns:
            解析后的搜索结果
        """
        try:
            state_data = json.loads(state_json)
            
            # 数据结构：searchResult.Search.Feeds.Value
            search_data = state_data.get("search", {})
            feeds_data = search_data.get("feeds", {})
            feeds_value = feeds_data.get("_value", [])
            
            logger.info(f"从 __INITIAL_STATE__ 解析到 {len(feeds_value)} 个搜索结果")
            
            # 转换为Feed对象
            feeds = []
            for item in feeds_value:
                try:
                    feed = self._convert_item_to_feed(item)
                    if feed:
                        feeds.append(feed)
                except Exception as e:
                    logger.warning(f"转换Feed项失败: {e}")
                    continue
            
            # 保存数据到临时文件夹
            self._save_search_data_to_file(state_data, feeds_value, feeds)
            
            return SearchResult(
                items=feeds,
                has_more=len(feeds_value) >= 20,  # 假设每页20个结果
                total=len(feeds)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"解析 __INITIAL_STATE__ JSON失败: {e}")
            return SearchResult(items=[], has_more=False, total=0)
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
            return SearchResult(items=[], has_more=False, total=0)
    
    def _convert_item_to_feed(self, item: Dict[str, Any]) -> Optional[Feed]:
        """
        将搜索结果项转换为Feed对象
        
        Args:
            item: 搜索结果项
            
        Returns:
            Feed对象或None
        """
        try:
            from ..config import (
                User, InteractInfo, Cover, ImageInfo, 
                NoteCard, VideoCapability, Video
            )
            
            # 获取基本信息
            note_card_data = item.get("noteCard", {})
            user_data = note_card_data.get("user", {})
            interact_data = note_card_data.get("interactInfo", {})
            cover_data = note_card_data.get("cover", {})
            video_data = note_card_data.get("video")
            
            # 构建User对象（修正字段映射）
            user = User(
                user_id=user_data.get("userId", ""),
                nickname=user_data.get("nickname", user_data.get("nickName", "")),
                avatar=user_data.get("avatar", ""),
                desc=user_data.get("desc", ""),
                gender=user_data.get("gender"),
                ip_location=user_data.get("ipLocation")
            )
            
            # 构建InteractInfo对象（修正字段映射）
            interact_info = InteractInfo(
                liked=interact_data.get("liked", False),
                liked_count=str(interact_data.get("likedCount", "0")),
                collected=interact_data.get("collected", False),
                collected_count=str(interact_data.get("collectedCount", "0")),
                comment_count=str(interact_data.get("commentCount", "0")),
                share_count=str(interact_data.get("sharedCount", "0"))
            )
            
            # 构建Cover对象（修正字段映射）
            cover = Cover(
                url=cover_data.get("url", ""),
                width=cover_data.get("width", 0),
                height=cover_data.get("height", 0),
                file_id=cover_data.get("fileId", "")
            )
            
            # 构建Video对象（如果存在）
            video = None
            if video_data:
                video = Video(
                    media=video_data.get("media", {}),
                    video_id=video_data.get("videoId", ""),
                    duration=video_data.get("duration", 0),
                    width=video_data.get("width", 0),
                    height=video_data.get("height", 0),
                    master_url=video_data.get("masterUrl", ""),
                    backup_urls=video_data.get("backupUrls", []),
                    stream=video_data.get("stream", {}),
                    h264=video_data.get("h264", []),
                    h265=video_data.get("h265", []),
                    av1=video_data.get("av1", [])
                )
            
            # 构建NoteCard对象（修正字段映射）
            note_card = NoteCard(
                type=note_card_data.get("type", ""),
                display_title=note_card_data.get("displayTitle", ""),
                user=user,
                interact_info=interact_info,
                cover=cover,
                images_list=None,  # 简化处理
                video=video
            )
            
            # 构建Feed对象（修正字段映射）
            feed = Feed(
                id=item.get("id", ""),
                model_type=item.get("modelType", ""),
                note_card=note_card,
                track_id=item.get("trackId")
            )
            
            return feed
            
        except Exception as e:
            logger.error(f"转换Feed对象失败: {e}")
            return None
    
    def _save_search_data_to_file(self, state_data: Dict[str, Any], feeds_value: List[Dict], feeds: List[Feed]):
        """
        保存搜索数据到临时文件夹
        
        Args:
            state_data: 完整的 __INITIAL_STATE__ 数据
            feeds_value: 原始搜索结果列表
            feeds: 转换后的Feed对象列表
        """
        try:
            # 创建临时文件夹（基于项目根目录）
            from ..config.settings import get_project_root
            project_root = get_project_root()
            save_dir = project_root / "temp_search_results"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成时间戳文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存原始状态数据
            state_file = save_dir / f"initial_state_{timestamp}.json"
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            logger.info(f"原始状态数据已保存到: {state_file}")
            
            # 保存原始搜索结果
            feeds_file = save_dir / f"feeds_raw_{timestamp}.json"
            with open(feeds_file, "w", encoding="utf-8") as f:
                json.dump(feeds_value, f, ensure_ascii=False, indent=2)
            logger.info(f"原始搜索结果已保存到: {feeds_file}")
            
            # 保存转换后的Feed对象（使用Pydantic的序列化）
            feeds_dict = []
            for feed in feeds:
                try:
                    # 使用 Pydantic 的 model_dump 方法序列化
                    if hasattr(feed, 'model_dump'):
                        feed_dict = feed.model_dump()
                    elif hasattr(feed, 'dict'):
                        feed_dict = feed.dict()
                    else:
                        # 降级方案：手动构建字典
                        feed_dict = {
                            "id": feed.id,
                            "model_type": feed.model_type,
                            "track_id": feed.track_id,
                            "note_card": feed.note_card.model_dump() if feed.note_card and hasattr(feed.note_card, 'model_dump') else None,
                        }
                    feeds_dict.append(feed_dict)
                except Exception as e:
                    logger.warning(f"序列化Feed对象失败: {e}")
                    continue
            
            parsed_file = save_dir / f"feeds_parsed_{timestamp}.json"
            with open(parsed_file, "w", encoding="utf-8") as f:
                json.dump(feeds_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"解析后的数据已保存到: {parsed_file}")
            
        except Exception as e:
            logger.error(f"保存搜索数据失败: {e}")