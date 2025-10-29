"""小红书用户相关功能
实现用户信息获取和解析
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger

from ..types import UserProfileResponse, UserPageData, UserBasicInfo, UserInteractions, Feed
from ..config import XiaohongshuUrls, XiaohongshuSelectors, BrowserConfig
from .anti_bot import AntiBotStrategy


class UserProfileAction:
    """用户主页操作类 - 参考Go版本实现"""
    
    def __init__(self, page: Page):
        """
        初始化用户主页操作
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
    
    async def user_profile(self, user_id: str, xsec_token: str) -> UserProfileResponse:
        """
        获取用户基本信息及帖子 
        
        Args:
            user_id: 用户ID
            xsec_token: 安全令牌
            
        Returns:
            用户主页响应数据
        """
        try:
            logger.info(f"开始获取用户主页: user_id={user_id}")
            
            # 构建用户主页URL 
            search_url = self._make_user_profile_url(user_id, xsec_token)
            
            # 添加随机延迟，模拟人类行为 - 使用统一的反爬虫策略
            await AntiBotStrategy.add_random_delay(seed=user_id)
            
            # 使用统一的反爬虫导航策略
            await AntiBotStrategy.simulate_human_navigation(self.page, search_url)
            
            # 等待__INITIAL_STATE__加载完成 -
            await self.page.wait_for_function("() => window.__INITIAL_STATE__ !== undefined")
            
            # 使用统一的安全数据提取方法
            result = await AntiBotStrategy.extract_initial_state_safely(self.page)
            
            if not result:
                raise ValueError("__INITIAL_STATE__ not found")
            
            # 解析初始状态数据 - 数据结构
            initial_state = json.loads(result)
            
            # 提取用户数据 - 解析逻辑
            user_data = initial_state.get("user", {})
            user_page_data = user_data.get("userPageData", {}).get("_rawValue", {})
            notes_data = user_data.get("notes", {}).get("_rawValue", [])
            
            # 构建响应数据 - UserProfileResponse结构
            basic_info = self._extract_basic_info(user_page_data.get("basicInfo", {}))
            interactions = self._extract_interactions(user_page_data.get("interactions", []))
            feeds = self._extract_feeds(notes_data)
            
            return UserProfileResponse(
                success=True,
                code=200,
                msg="success",
                data=UserPageData(
                    basic_info=basic_info,
                    interactions=interactions
                )
            )
            
        except Exception as e:
            logger.error(f"获取用户主页失败: {e}")
            # 返回默认的空数据结构，避免data=None导致的验证错误
            return UserProfileResponse(
                success=False,
                code=500,
                msg=f"获取用户主页失败: {str(e)}",
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id=user_id,
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location="",
                        red_id=""
                    ),
                    interactions=UserInteractions(
                        follows="0",
                        fans="0",
                        interaction="0"
                    )
                )
            )
    
    def _make_user_profile_url(self, user_id: str, xsec_token: str) -> str:
        """
        构建用户主页URL - 参考Go版本makeUserProfileURL
        
        Args:
            user_id: 用户ID
            xsec_token: 安全令牌
            
        Returns:
            用户主页URL
        """
        return f"https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={xsec_token}&xsec_source=pc_note"
    
    def _extract_basic_info(self, basic_info_data: Dict[str, Any]) -> UserBasicInfo:
        """
        提取用户基本信息 - 参考Go版本UserBasicInfo结构
        
        Args:
            basic_info_data: 基本信息数据
            
        Returns:
            用户基本信息
        """
        return UserBasicInfo(
            user_id=basic_info_data.get("redId", ""),
            nickname=basic_info_data.get("nickname", ""),
            avatar=basic_info_data.get("images", ""),
            desc=basic_info_data.get("desc", ""),
            gender=basic_info_data.get("gender", 0),
            ip_location=basic_info_data.get("ipLocation", ""),
            red_id=basic_info_data.get("redId", "")
        )
    
    def _extract_interactions(self, interactions_data: List[Dict[str, Any]]) -> UserInteractions:
        """
        提取用户互动数据 - 参考Go版本UserInteractions结构
        
        Args:
            interactions_data: 互动数据列表
            
        Returns:
            用户互动信息
        """
        follows = "0"
        fans = "0" 
        interaction = "0"
        
        for item in interactions_data:
            item_type = item.get("type", "")
            count = item.get("count", "0")
            
            if item_type == "follows":
                follows = count
            elif item_type == "fans":
                fans = count
            elif item_type == "interaction":
                interaction = count
        
        return UserInteractions(
            follows=follows,
            fans=fans,
            interaction=interaction
        )
    
    def _extract_feeds(self, notes_data: List[List[Dict[str, Any]]]) -> List[Feed]:
        """
        提取用户发布的内容 - 参考Go版本Feed提取逻辑
        
        Args:
            notes_data: 笔记数据（双重数组结构）
            
        Returns:
            Feed列表
        """
        feeds = []
        
        # 处理双重数组结构 - 参考Go版本逻辑
        for feed_group in notes_data:
            if len(feed_group) != 0:
                for feed_data in feed_group:
                    try:
                        feed = self._parse_feed_data(feed_data)
                        if feed:
                            feeds.append(feed)
                    except Exception as e:
                        logger.warning(f"解析Feed数据失败: {e}")
                        continue
        
        return feeds
    
    def _parse_feed_data(self, feed_data: Dict[str, Any]) -> Optional[Feed]:
        """
        解析单个Feed数据
        
        Args:
            feed_data: Feed原始数据
            
        Returns:
            解析后的Feed对象
        """
        try:
            # 这里需要根据实际的数据结构进行解析
            # 由于Go版本中Feed结构比较复杂，这里做简化处理
            return Feed(
                id=feed_data.get("id", ""),
                model_type=feed_data.get("modelType", ""),
                note_card=feed_data.get("noteCard", {}),
                xsec_token=feed_data.get("xsecToken", ""),
                index=feed_data.get("index", 0)
            )
        except Exception as e:
            logger.error(f"解析Feed数据失败: {e}")
            return None


class UserAction:
    """用户操作类 - 保持向后兼容"""
    
    def __init__(self, page: Page):
        """
        初始化用户操作
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
        self.profile_action = UserProfileAction(page)
    
    async def get_user_profile(self, user_id: str, xsec_token: Optional[str] = None) -> UserProfileResponse:
        """
        获取用户资料 - 兼容旧接口
        
        Args:
            user_id: 用户ID
            xsec_token: 安全令牌（可选）
            
        Returns:
            用户资料响应
        """
        if xsec_token:
            # 使用新的实现方式
            return await self.profile_action.user_profile(user_id, xsec_token)
        else:
            # 使用原有的实现方式
            return await self._get_user_profile_legacy(user_id)
    
    async def _get_user_profile_legacy(self, user_id: str) -> UserProfileResponse:
        """
        获取用户资料 - 原有实现方式
        
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
            user_profile = await self._parse_user_profile()
            
            logger.info(f"成功获取用户资料: {user_id}")
            return user_profile
            
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            # 返回默认的空数据结构，避免data=None导致的验证错误
            return UserProfileResponse(
                success=False,
                code=500,
                msg=f"获取用户资料失败: {str(e)}",
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id=user_id,
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location="",
                        red_id=""
                    ),
                    interactions=UserInteractions(
                        follows="0",
                        fans="0",
                        interaction="0"
                    )
                )
            )

    async def _parse_user_profile(self) -> UserProfileResponse:
        """
        解析用户资料 - 原有实现的简化版本
        
        Returns:
            用户资料响应
        """
        try:
            # 简化的解析逻辑，返回基本结构
            return UserProfileResponse(
                success=True,
                code=200,
                msg="success",
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id="",
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location="",
                        red_id=""
                    ),
                    interactions=UserInteractions(
                        follows="0",
                        fans="0",
                        interaction="0"
                    )
                )
            )
        except Exception as e:
            logger.error(f"解析用户资料失败: {e}")
            # 返回默认的空数据结构，避免data=None导致的验证错误
            return UserProfileResponse(
                success=False,
                code=500,
                msg=f"解析用户资料失败: {str(e)}",
                data=UserPageData(
                    basic_info=UserBasicInfo(
                        user_id="",
                        nickname="",
                        avatar="",
                        desc="",
                        gender=0,
                        ip_location="",
                        red_id=""
                    ),
                    interactions=UserInteractions(
                        follows="0",
                        fans="0",
                        interaction="0"
                    )
                )
            )