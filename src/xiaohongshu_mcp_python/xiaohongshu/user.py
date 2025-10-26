"""
小红书用户功能
实现用户资料获取和解析
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger

from ..types import UserProfileResponse, UserPageData, UserBasicInfo, UserInteractions
from ..config import XiaohongshuUrls, XiaohongshuSelectors, BrowserConfig


class UserAction:
    """用户操作类"""
    
    def __init__(self, page: Page):
        """
        初始化用户操作
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
    
    async def get_user_profile(self, user_id: str) -> UserProfileResponse:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户资料响应
        """
        try:
            logger.info(f"开始获取用户资料: {user_id}")
            
            # 构建用户页面URL
            user_url = f"{XiaohongshuUrls.USER_URL}/{user_id}"
            
            # 导航到用户页面
            await self.page.goto(user_url, wait_until="networkidle")
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")
            
            # 解析用户资料
            result = await self._parse_user_profile()
            
            logger.info(f"获取用户资料完成: {result.data.basic_info.nickname if result.data else '未知'}")
            return result
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return UserProfileResponse(
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id=user_id,
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location=""
                    ),
                    interactions=UserInteractions()
                )
            )
    
    async def _parse_user_profile(self) -> UserProfileResponse:
        """
        解析用户资料
        
        Returns:
            用户资料响应
        """
        try:
            # 方法1: 尝试从 __INITIAL_STATE__ 解析
            initial_state_result = await self._parse_from_initial_state()
            if initial_state_result and initial_state_result.data:
                return initial_state_result
            
            # 方法2: 从DOM元素解析
            dom_result = await self._parse_from_dom()
            return dom_result
            
        except Exception as e:
            logger.error(f"解析用户资料失败: {e}")
            return UserProfileResponse(
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id="",
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location=""
                    ),
                    interactions=UserInteractions()
                )
            )
    
    async def _parse_from_initial_state(self) -> Optional[UserProfileResponse]:
        """
        从 __INITIAL_STATE__ 解析用户资料
        
        Returns:
            用户资料响应
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
            
            # 解析用户资料数据
            return self._extract_user_data_from_state(data)
            
        except Exception as e:
            logger.debug(f"从 __INITIAL_STATE__ 解析失败: {e}")
            return None
    
    def _extract_user_data_from_state(self, data: Dict[str, Any]) -> Optional[UserProfileResponse]:
        """
        从状态数据中提取用户资料
        
        Args:
            data: 状态数据
            
        Returns:
            用户资料响应
        """
        try:
            # 根据小红书的数据结构提取用户资料
            # 这里需要根据实际的数据结构调整
            user_data = data.get("user", {})
            if not user_data:
                # 尝试其他可能的路径
                user_data = data.get("userPage", {}) or data.get("profile", {})
            
            if not user_data:
                return None
            
            # 基本信息
            basic_info_data = user_data.get("basicInfo", {})
            if not basic_info_data:
                basic_info_data = user_data.get("basic_info", {}) or user_data
            
            basic_info = UserBasicInfo(
                user_id=basic_info_data.get("user_id", ""),
                nickname=basic_info_data.get("nickname", ""),
                avatar=basic_info_data.get("avatar", ""),
                desc=basic_info_data.get("desc", ""),
                gender=basic_info_data.get("gender", 0),
                ip_location=basic_info_data.get("ip_location", ""),
                follows=basic_info_data.get("follows", 0),
                fans=basic_info_data.get("fans", 0),
                interaction=basic_info_data.get("interaction", 0),
                tags=basic_info_data.get("tags", [])
            )
            
            # 互动信息
            interactions_data = user_data.get("interactions", {})
            interactions = UserInteractions(
                follows_count=interactions_data.get("follows_count", basic_info.follows),
                fans_count=interactions_data.get("fans_count", basic_info.fans),
                interaction_count=interactions_data.get("interaction_count", basic_info.interaction),
                notes_count=interactions_data.get("notes_count", 0)
            )
            
            # 用户页面数据
            user_page_data = UserPageData(
                basic_info=basic_info,
                interactions=interactions
            )
            
            return UserProfileResponse(data=user_page_data)
            
        except Exception as e:
            logger.debug(f"提取用户数据失败: {e}")
            return None
    
    async def _parse_from_dom(self) -> UserProfileResponse:
        """
        从DOM元素解析用户资料
        
        Returns:
            用户资料响应
        """
        try:
            logger.debug("从DOM解析用户资料")
            
            # 等待用户资料加载
            await self.page.wait_for_selector(
                XiaohongshuSelectors.USER_PROFILE,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            # 提取用户基本信息
            basic_info = await self._extract_basic_info_from_dom()
            
            # 提取互动信息
            interactions = await self._extract_interactions_from_dom()
            
            # 构建用户页面数据
            user_page_data = UserPageData(
                basic_info=basic_info,
                interactions=interactions
            )
            
            return UserProfileResponse(data=user_page_data)
            
        except PlaywrightTimeoutError:
            logger.warning("等待用户资料超时")
            return UserProfileResponse(
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id="",
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location=""
                    ),
                    interactions=UserInteractions()
                )
            )
        except Exception as e:
            logger.error(f"从DOM解析用户资料失败: {e}")
            return UserProfileResponse(
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id="",
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location=""
                    ),
                    interactions=UserInteractions()
                )
            )
    
    async def _extract_basic_info_from_dom(self) -> UserBasicInfo:
        """
        从DOM提取用户基本信息
        
        Returns:
            用户基本信息
        """
        try:
            # 提取昵称
            nickname_element = await self.page.query_selector(XiaohongshuSelectors.USER_NICKNAME)
            nickname = await nickname_element.text_content() if nickname_element else ""
            
            # 提取头像
            avatar_element = await self.page.query_selector(XiaohongshuSelectors.USER_AVATAR)
            avatar = await avatar_element.get_attribute("src") if avatar_element else ""
            
            # 提取描述
            desc_element = await self.page.query_selector(XiaohongshuSelectors.USER_DESC)
            desc = await desc_element.text_content() if desc_element else ""
            
            # 提取IP位置
            location_element = await self.page.query_selector(XiaohongshuSelectors.USER_LOCATION)
            ip_location = await location_element.text_content() if location_element else ""
            
            # 提取关注数
            follows_element = await self.page.query_selector(XiaohongshuSelectors.USER_FOLLOWS)
            follows_text = await follows_element.text_content() if follows_element else "0"
            follows = self._parse_count(follows_text)
            
            # 提取粉丝数
            fans_element = await self.page.query_selector(XiaohongshuSelectors.USER_FANS)
            fans_text = await fans_element.text_content() if fans_element else "0"
            fans = self._parse_count(fans_text)
            
            # 提取获赞数
            interaction_element = await self.page.query_selector(XiaohongshuSelectors.USER_INTERACTION)
            interaction_text = await interaction_element.text_content() if interaction_element else "0"
            interaction = self._parse_count(interaction_text)
            
            # 提取标签
            tags = await self._extract_user_tags()
            
            # 从URL提取用户ID
            current_url = self.page.url
            user_id = self._extract_user_id_from_url(current_url)
            
            return UserBasicInfo(
                user_id=user_id,
                nickname=nickname.strip(),
                avatar=avatar,
                desc=desc.strip(),
                gender=0,  # 无法从DOM直接获取
                ip_location=ip_location.strip(),
                follows=follows,
                fans=fans,
                interaction=interaction,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"提取用户基本信息失败: {e}")
            return UserBasicInfo(
                user_id="",
                nickname="",
                avatar="",
                desc="",
                gender=0,
                ip_location=""
            )
    
    async def _extract_interactions_from_dom(self) -> UserInteractions:
        """
        从DOM提取用户互动信息
        
        Returns:
            用户互动信息
        """
        try:
            # 提取笔记数
            notes_element = await self.page.query_selector(XiaohongshuSelectors.USER_NOTES_COUNT)
            notes_text = await notes_element.text_content() if notes_element else "0"
            notes_count = self._parse_count(notes_text)
            
            # 其他数据从基本信息中获取
            basic_info = await self._extract_basic_info_from_dom()
            
            return UserInteractions(
                follows_count=basic_info.follows,
                fans_count=basic_info.fans,
                interaction_count=basic_info.interaction,
                notes_count=notes_count
            )
            
        except Exception as e:
            logger.error(f"提取用户互动信息失败: {e}")
            return UserInteractions()
    
    async def _extract_user_tags(self) -> list[str]:
        """
        提取用户标签
        
        Returns:
            用户标签列表
        """
        try:
            tag_elements = await self.page.query_selector_all(XiaohongshuSelectors.USER_TAGS)
            tags = []
            
            for tag_element in tag_elements:
                tag_text = await tag_element.text_content()
                if tag_text:
                    tags.append(tag_text.strip())
            
            return tags
            
        except Exception as e:
            logger.debug(f"提取用户标签失败: {e}")
            return []
    
    def _parse_count(self, count_text: str) -> int:
        """
        解析数量文本（支持万、k等单位）
        
        Args:
            count_text: 数量文本
            
        Returns:
            数量
        """
        try:
            if not count_text:
                return 0
            
            # 清理文本
            count_text = count_text.strip().lower()
            
            # 移除非数字和单位字符
            import re
            match = re.search(r'([\d.]+)([万wk]?)', count_text)
            if not match:
                return 0
            
            number_str, unit = match.groups()
            number = float(number_str)
            
            # 转换单位
            if unit in ['万', 'w']:
                return int(number * 10000)
            elif unit == 'k':
                return int(number * 1000)
            else:
                return int(number)
                
        except Exception as e:
            logger.debug(f"解析数量失败: {count_text}, {e}")
            return 0
    
    def _extract_user_id_from_url(self, url: str) -> str:
        """
        从URL中提取用户ID
        
        Args:
            url: URL
            
        Returns:
            用户ID
        """
        try:
            if "/user/profile/" in url:
                return url.split("/user/profile/")[-1].split("?")[0]
            elif "/user/" in url:
                return url.split("/user/")[-1].split("?")[0]
            return ""
        except Exception:
            return ""
    
    async def get_user_notes(self, user_id: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        获取用户笔记列表
        
        Args:
            user_id: 用户ID
            cursor: 分页游标
            
        Returns:
            用户笔记列表
        """
        try:
            logger.info(f"开始获取用户笔记: {user_id}")
            
            # 构建用户页面URL
            user_url = f"{XiaohongshuUrls.USER_URL}/{user_id}"
            if cursor:
                user_url += f"?cursor={cursor}"
            
            # 导航到用户页面
            await self.page.goto(user_url, wait_until="networkidle")
            
            # 等待笔记列表加载
            await self.page.wait_for_selector(
                XiaohongshuSelectors.USER_NOTES_LIST,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            # 获取笔记列表
            note_elements = await self.page.query_selector_all(
                XiaohongshuSelectors.USER_NOTE_ITEM
            )
            
            notes = []
            for note_element in note_elements:
                try:
                    note_data = await self._extract_note_from_element(note_element)
                    if note_data:
                        notes.append(note_data)
                except Exception as e:
                    logger.debug(f"提取笔记失败: {e}")
                    continue
            
            # 检查是否有更多笔记
            has_more = await self._check_has_more_notes()
            
            return {
                "notes": notes,
                "has_more": has_more,
                "cursor": cursor or ""
            }
            
        except Exception as e:
            logger.error(f"获取用户笔记失败: {e}")
            return {
                "notes": [],
                "has_more": False,
                "cursor": ""
            }
    
    async def _extract_note_from_element(self, element) -> Optional[Dict[str, Any]]:
        """
        从DOM元素提取笔记信息
        
        Args:
            element: DOM元素
            
        Returns:
            笔记信息
        """
        try:
            # 提取标题
            title_element = await element.query_selector(".title")
            title = await title_element.text_content() if title_element else ""
            
            # 提取封面
            cover_element = await element.query_selector("img")
            cover = await cover_element.get_attribute("src") if cover_element else ""
            
            # 提取链接
            link_element = await element.query_selector("a")
            href = await link_element.get_attribute("href") if link_element else ""
            note_id = self._extract_note_id_from_url(href) if href else ""
            
            # 提取互动数据
            like_element = await element.query_selector(".like-count")
            like_count = await like_element.text_content() if like_element else "0"
            
            return {
                "id": note_id,
                "title": title.strip(),
                "cover": cover,
                "like_count": self._parse_count(like_count),
                "url": href
            }
            
        except Exception as e:
            logger.debug(f"从元素提取笔记失败: {e}")
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
    
    async def _check_has_more_notes(self) -> bool:
        """
        检查是否有更多笔记
        
        Returns:
            是否有更多笔记
        """
        try:
            # 检查是否有"加载更多"按钮
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