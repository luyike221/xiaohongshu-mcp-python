"""
小红书发布功能
实现图文和视频内容的发布
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from loguru import logger

try:
    from fastmcp import Context
except ImportError:
    Context = None

from ..types import PublishImageContent, PublishVideoContent, PublishResponse
from ..config import XiaohongshuUrls, XiaohongshuSelectors, BrowserConfig, PublishConfig


class PublishAction:
    """发布操作类"""
    
    def __init__(self, page: Page):
        """
        初始化发布操作
        
        Args:
            page: Playwright页面对象
        """
        self.page = page
    
    async def publish(self, content: PublishImageContent, context: Optional[Context] = None) -> PublishResponse:
        """
        发布图文内容
        
        Args:
            content: 发布内容
            
        Returns:
            发布结果
        """
        try:
            logger.info(f"开始发布图文内容: {content.title}")
            
            # 导航到发布页面
            if context:
                await context.report_progress(progress=10, total=100)
            await self._navigate_to_publish_page(context)

            
            
            # 选择图文发布标签
            if context:
                await context.report_progress(progress=20, total=100)
            await self._select_image_publish_tab()
            
            # 上传图片
            if context:
                await context.report_progress(progress=30, total=100)
            await self._upload_images(content.images)
            
            # 等待图片上传完成
            if context:
                await context.report_progress(progress=50, total=100)
            await self._wait_for_upload_complete(len(content.images))
            
            # 填写内容
            if context:
                await context.report_progress(progress=70, total=100)
            await self._fill_content(content.title, content.content, content.tags or [])
            
            # 点击发布按钮
            if context:
                await context.report_progress(progress=90, total=100)
            await self._click_publish_button(is_video=False)
            
            # 等待发布完成
            if context:
                await context.report_progress(progress=95, total=100)
            note_id = await self._wait_for_publish_complete()
            
            if context:
                await context.report_progress(progress=100, total=100)
            
            logger.info(f"图文发布成功: {note_id}")
            return PublishResponse(
                success=True,
                message="发布成功",
                note_id=note_id
            )
            
        except Exception as e:
            logger.error(f"发布图文失败: {e}")
            return PublishResponse(
                success=False,
                message=f"发布失败: {str(e)}",
                error="PUBLISH_FAILED"
            )
    
    async def publish_video(self, content: PublishVideoContent, context: Optional[Context] = None) -> PublishResponse:
        """
        发布视频内容
        
        Args:
            content: 视频内容
            context: 上下文对象，用于进度报告
            
        Returns:
            发布结果
        """
        try:
            logger.info(f"开始发布视频内容: {content.title}")
            
            # 导航到发布页面
            if context:
                await context.report_progress(progress=10, total=100)
            await self._navigate_to_publish_page(context)
            
            # 选择视频发布标签
            if context:
                await context.report_progress(progress=20, total=100)
            await self._select_video_publish_tab()
            
            # 上传视频
            if context:
                await context.report_progress(progress=30, total=100)
            await self._upload_video(content.video_path, content.cover_path)
            
            # 等待视频上传完成
            if context:
                await context.report_progress(progress=60, total=100)
            await self._wait_for_video_upload_complete()
            
            # 填写内容
            if context:
                await context.report_progress(progress=70, total=100)
            await self._fill_content(content.title, "", content.tags or [])
            
            # 点击发布按钮
            if context:
                await context.report_progress(progress=90, total=100)
            await self._click_publish_button(is_video=True)
            
            # 等待发布完成
            if context:
                await context.report_progress(progress=95, total=100)
            note_id = await self._wait_for_publish_complete()
            
            if context:
                await context.report_progress(progress=100, total=100)
            
            logger.info(f"视频发布成功: {note_id}")
            return PublishResponse(
                success=True,
                message="发布成功",
                note_id=note_id
            )
            
        except Exception as e:
            logger.error(f"发布视频失败: {e}")
            return PublishResponse(
                success=False,
                message=f"发布失败: {str(e)}",
                error="PUBLISH_FAILED"
            )
    
    async def _navigate_to_publish_page(self, context: Optional[Context] = None):
        """导航到发布页面"""
        logger.info("导航到发布页面")
        
        # 发送进度报告：开始导航
        if context:
            await context.report_progress(progress=5, total=100)
        
        # 使用更长的超时时间进行页面导航
        await self.page.goto(
            XiaohongshuUrls.PUBLISH_URL, 
            wait_until="networkidle",
            timeout=BrowserConfig.PAGE_LOAD_TIMEOUT  # 60秒超时
        )
        
        # 发送进度报告：页面加载中
        if context:
            await context.report_progress(progress=8, total=100)
        
        # 等待页面加载完成
        await self.page.wait_for_load_state("networkidle", timeout=BrowserConfig.PAGE_LOAD_TIMEOUT)
        
        # 发送进度报告：移除弹窗
        if context:
            await context.report_progress(progress=10, total=100)
        
        # 移除可能的弹窗
        await self._remove_popups()
    
    async def _select_image_publish_tab(self):
        """选择图文发布标签"""
        logger.info("选择图文发布标签")
        
        try:
            # 等待并点击图文发布标签
            tab_element = await self.page.wait_for_selector(
                XiaohongshuSelectors.PUBLISH_TAB,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if tab_element:
                await tab_element.click()
                await asyncio.sleep(1)  # 等待标签切换
                logger.info("已选择图文发布标签")
            else:
                raise Exception("找不到图文发布标签")
                
        except PlaywrightTimeoutError:
            raise Exception("等待图文发布标签超时")
    
    async def _select_video_publish_tab(self):
        """选择视频发布标签"""
        logger.info("选择视频发布标签")
        
        try:
            # 等待并点击视频发布标签
            video_tab = await self.page.wait_for_selector(
                XiaohongshuSelectors.VIDEO_PUBLISH_TAB,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if video_tab:
                await video_tab.click()
                await asyncio.sleep(1)  # 等待标签切换
                logger.info("已选择视频发布标签")
            else:
                raise Exception("找不到视频发布标签")
                
        except PlaywrightTimeoutError:
            raise Exception("等待视频发布标签超时")
    
    async def _upload_images(self, image_paths: List[str]):
        """
        上传图片
        
        Args:
            image_paths: 图片路径列表
        """
        if not image_paths:
            raise Exception("图片路径列表不能为空")
        
        # 验证文件存在性
        for path in image_paths:
            if not os.path.exists(path):
                raise Exception(f"图片文件不存在: {path}")
        
        logger.info(f"开始上传 {len(image_paths)} 张图片")
        
        try:
            # 等待上传输入框
            upload_input = await self.page.wait_for_selector(
                XiaohongshuSelectors.UPLOAD_INPUT,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if not upload_input:
                raise Exception("找不到图片上传输入框")
            
            # 设置文件
            await upload_input.set_input_files(image_paths)
            
            # 等待上传完成
            await self._wait_for_upload_complete(len(image_paths))
            
            logger.info("图片上传完成")
            
        except PlaywrightTimeoutError:
            raise Exception("等待图片上传输入框超时")
    
    async def _upload_video(self, video_path: str, cover_path: Optional[str] = None):
        """
        上传视频
        
        Args:
            video_path: 视频路径
            cover_path: 封面路径
        """
        if not os.path.exists(video_path):
            raise Exception(f"视频文件不存在: {video_path}")
        
        logger.info(f"开始上传视频: {video_path}")
        
        try:
            # 等待视频上传输入框
            video_input = await self.page.wait_for_selector(
                "//input[@class='upload-input']",
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if not video_input:
                raise Exception("找不到视频上传输入框")
            
            # 上传视频
            await video_input.set_input_files([video_path])
            
            # 等待视频上传完成（视频上传时间较长）
            await self._wait_for_video_upload_complete()
            
            # 如果有封面，上传封面
            if cover_path and os.path.exists(cover_path):
                await self._upload_video_cover(cover_path)
            
            logger.info("视频上传完成")
            
        except PlaywrightTimeoutError:
            raise Exception("等待视频上传输入框超时")
    
    async def _upload_video_cover(self, cover_path: str):
        """
        上传视频封面
        
        Args:
            cover_path: 封面路径
        """
        logger.info(f"上传视频封面: {cover_path}")
        
        try:
            # 等待封面上传按钮
            cover_button = await self.page.wait_for_selector(
                "text=上传封面",
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if cover_button:
                await cover_button.click()
                
                # 等待封面上传输入框
                cover_input = await self.page.wait_for_selector(
                    "input[type='file'][accept*='image']",
                    timeout=BrowserConfig.ELEMENT_TIMEOUT
                )
                
                if cover_input:
                    await cover_input.set_input_files([cover_path])
                    await asyncio.sleep(2)  # 等待封面上传
                    logger.info("视频封面上传完成")
                    
        except PlaywrightTimeoutError:
            logger.warning("上传视频封面超时，使用默认封面")
    
    async def _wait_for_upload_complete(self, expected_count: int):
        """
        等待图片上传完成
        
        Args:
            expected_count: 期望的图片数量
        """
        logger.info(f"等待 {expected_count} 张图片上传完成")
        
        timeout = BrowserConfig.UPLOAD_TIMEOUT
        start_time = asyncio.get_event_loop().time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if (current_time - start_time) * 1000 > timeout:
                raise Exception("等待图片上传完成超时")
            
            # 检查已上传的图片数量
            uploaded_images = await self.page.query_selector_all(
                XiaohongshuSelectors.UPLOADED_IMAGE
            )
            
            if len(uploaded_images) >= expected_count:
                logger.info(f"图片上传完成，共 {len(uploaded_images)} 张")
                break
            
            # 添加进度日志，减少用户焦虑
            logger.info(f"上传进度: {len(uploaded_images)}/{expected_count}")
            await asyncio.sleep(2)  # 增加检查间隔，减少CPU占用
    
    async def _wait_for_video_upload_complete(self):
        """等待视频上传完成"""
        logger.info("等待视频上传完成")
        
        timeout = 5 * 60 * 1000  # 5分钟超时时间（毫秒）
        start_time = asyncio.get_event_loop().time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if (current_time - start_time) * 1000 > timeout:
                raise Exception("等待视频上传完成超时")
            
            # 检查发布按钮是否可点击（视频上传完成的标志）
            publish_button = await self.page.query_selector(XiaohongshuSelectors.VIDEO_PUBLISH_BUTTON)
            if publish_button:
                # 检查按钮是否可见
                is_visible = await publish_button.is_visible()
                if is_visible:
                    # 检查按钮是否被禁用
                    is_disabled = await publish_button.is_disabled()
                    if not is_disabled:
                        # 检查按钮class是否包含disabled
                        class_name = await publish_button.get_attribute("class")
                        if class_name and "disabled" not in class_name:
                            logger.info("视频上传完成，发布按钮可点击")
                            break
            
            # 检查是否有错误
            error_element = await self.page.query_selector(XiaohongshuSelectors.ERROR_MESSAGE)
            if error_element:
                error_text = await error_element.text_content()
                raise Exception(f"视频上传失败: {error_text}")
            
            await asyncio.sleep(2)
    
    async def _fill_content(self, title: str, content: str, tags: List[str]):
        """
        填写发布内容
        
        Args:
            title: 标题
            content: 正文内容
            tags: 标签列表
        """
        logger.info("填写发布内容")
        
        # 填写标题
        await self._input_title(title)
        
        # 填写正文（如果有）
        if content:
            await self._input_content(content)
        
        # 添加标签
        if tags:
            await self._input_tags(tags)
    
    async def _input_title(self, title: str):
        """
        输入标题
        
        Args:
            title: 标题内容
        """
        logger.info(f"输入标题: {title}")
        
        try:
            title_input = await self.page.wait_for_selector(
                XiaohongshuSelectors.TITLE_INPUT,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if title_input:
                # 使用 fill() 方法，它会自动清空输入框然后填入新内容
                await title_input.fill(title)
                logger.info("标题输入完成")
            else:
                raise Exception("找不到标题输入框")
                
        except PlaywrightTimeoutError:
            raise Exception("等待标题输入框超时")
    
    async def _input_content(self, content: str):
        """
        输入正文内容
        
        Args:
            content: 正文内容
        """
        logger.info("输入正文内容")
        
        try:
            content_textarea = await self.page.wait_for_selector(
                XiaohongshuSelectors.CONTENT_TEXTAREA,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if content_textarea:
                # 使用 fill() 方法，它会自动清空输入框然后填入新内容
                await content_textarea.fill(content)
                logger.info("正文内容输入完成")
            else:
                raise Exception("找不到正文输入框")
                
        except PlaywrightTimeoutError:
            raise Exception("等待正文输入框超时")
    
    async def _input_tags(self, tags: List[str]):
        """
        输入标签
        
        Args:
            tags: 标签列表
        """
        if not tags:
            return
        
        logger.info(f"输入标签: {tags}")
        
        for tag in tags:
            await self._input_single_tag(tag)
            await asyncio.sleep(0.5)  # 标签输入间隔
    
    async def _input_single_tag(self, tag: str):
        """
        输入单个标签
        
        Args:
            tag: 标签内容
        """
        try:
            tag_input = await self.page.wait_for_selector(
                XiaohongshuSelectors.TAG_INPUT,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if tag_input:
                # 添加标签前缀
                tag_text = tag if tag.startswith(PublishConfig.TAG_PREFIX) else f"{PublishConfig.TAG_PREFIX}{tag}"
                
                await tag_input.fill(tag_text)
                await self.page.keyboard.press("Enter")
                
                # 等待标签添加完成
                await asyncio.sleep(0.5)
                
                logger.debug(f"标签添加完成: {tag_text}")
            else:
                logger.warning("找不到标签输入框")
                
        except PlaywrightTimeoutError:
            logger.warning(f"输入标签超时: {tag}")
    
    async def _click_publish_button(self, is_video: bool = False):
        """点击发布按钮"""
        logger.info("点击发布按钮")
        
        # 根据发布类型选择不同的按钮选择器
        selector = XiaohongshuSelectors.VIDEO_PUBLISH_BUTTON if is_video else XiaohongshuSelectors.IMAGE_PUBLISH_BUTTON
        
        try:
            publish_button = await self.page.wait_for_selector(
                selector,
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if publish_button:
                # 点击发布按钮
                await publish_button.click()
                logger.info("点击发布按钮成功")
                
                # 等待一下，让页面有时间响应
                await asyncio.sleep(2)
                
                logger.info("已完成发布按钮点击")
            else:
                raise Exception("找不到发布按钮")
                
        except PlaywrightTimeoutError:
            raise Exception("等待发布按钮超时")
    
    async def _wait_for_publish_complete(self) -> Optional[str]:
        """
        等待发布完成
        
        Returns:
            发布成功返回笔记ID，失败返回None
        """
        logger.info("等待发布完成")
        
        timeout = BrowserConfig.DEFAULT_TIMEOUT * 2  # 增加发布等待时间
        start_time = asyncio.get_event_loop().time()
        
        while True:
            current_time = asyncio.get_event_loop().time()
            if (current_time - start_time) * 1000 > timeout:
                raise Exception("等待发布完成超时")
            
            # 检查是否发布成功
            success_element = await self.page.query_selector("text=发布成功")
            if success_element:
                logger.info("发布成功")
                # 尝试获取笔记ID
                note_id = await self._extract_note_id()
                return note_id
            
            # 检查是否有错误
            error_element = await self.page.query_selector(XiaohongshuSelectors.ERROR_MESSAGE)
            if error_element:
                error_text = await error_element.text_content()
                raise Exception(f"发布失败: {error_text}")
            
            # 添加发布进度日志
            logger.info("正在发布中...")
            await asyncio.sleep(2)  # 增加检查间隔
    
    async def _extract_note_id(self) -> Optional[str]:
        """
        提取笔记ID
        
        Returns:
            笔记ID
        """
        try:
            # 尝试从URL中提取笔记ID
            current_url = self.page.url
            if "/item/" in current_url:
                note_id = current_url.split("/item/")[-1].split("?")[0]
                logger.info(f"提取到笔记ID: {note_id}")
                return note_id
            
            # 尝试从页面元素中提取
            # 这里可以根据实际页面结构调整选择器
            note_link = await self.page.query_selector("a[href*='/item/']")
            if note_link:
                href = await note_link.get_attribute("href")
                if href and "/item/" in href:
                    note_id = href.split("/item/")[-1].split("?")[0]
                    logger.info(f"从链接提取到笔记ID: {note_id}")
                    return note_id
            
            logger.warning("无法提取笔记ID")
            return None
            
        except Exception as e:
            logger.error(f"提取笔记ID失败: {e}")
            return None
    
    async def _remove_popups(self):
        """移除弹窗"""
        try:
            # 等待页面加载完毕 - 检查上传容器是否存在或等待最多3秒
            await self._wait_for_page_loaded()
            
            # 查找并关闭可能的弹窗
            popup_close = await self.page.query_selector(XiaohongshuSelectors.POPUP_CLOSE)
            if popup_close:
                await popup_close.click()
                await asyncio.sleep(0.5)
            
            # 查找并点击短笔记提示按钮
            short_note_tooltip_button = await self.page.query_selector('//button[contains(@class, "short-note-rooltip-button")]')
            if short_note_tooltip_button:
                await short_note_tooltip_button.click()
                await asyncio.sleep(0.5)
            
            # 点击空白区域关闭遮罩
            modal_mask = await self.page.query_selector(XiaohongshuSelectors.MODAL_MASK)
            if modal_mask:
                await modal_mask.click()
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.debug(f"移除弹窗时出错: {e}")
    
    async def _wait_for_page_loaded(self):
        """等待页面加载完毕"""
        try:
            # 等待上传容器出现或超时3秒
            await self.page.wait_for_selector(
                '//div[contains(@class, "upload-container")]',
                timeout=3000,
                state="visible"
            )
            logger.debug("页面加载完毕 - 上传容器已出现")
        except PlaywrightTimeoutError:
            # 超时也继续执行，可能页面已经加载完毕但没有上传容器
            logger.debug("等待上传容器超时，继续执行")
        except Exception as e:
            logger.debug(f"等待页面加载时出错: {e}")
    
    async def _click_empty_position(self):
        """点击页面空白位置"""
        try:
            # 点击页面中央空白区域
            await self.page.click("body", position={"x": 500, "y": 300})
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.debug(f"点击空白位置时出错: {e}")