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

from ..config import (
    PublishImageContent,
    PublishVideoContent,
    PublishResponse,
    XiaohongshuUrls,
    XiaohongshuSelectors,
    BrowserConfig,
    PublishConfig,
)


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
            
            # 处理可能出现的权限弹窗
            await self._dismiss_permission_popups()
            
            # 填写内容
            if context:
                await context.report_progress(progress=70, total=100)
            await self._fill_content(content.title, content.content, content.tags or [])
            
            # 再次处理可能出现的权限弹窗（填写内容时可能触发）
            await self._dismiss_permission_popups()
            
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
            
            # 处理可能出现的权限弹窗
            await self._dismiss_permission_popups()
            
            # 填写内容
            if context:
                await context.report_progress(progress=70, total=100)
            await self._fill_content(content.title, content.content, content.tags or [])
            
            # 再次处理可能出现的权限弹窗（填写内容时可能触发）
            await self._dismiss_permission_popups()
            
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
        
        # 关闭权限弹窗（如位置权限请求）
        await self._dismiss_permission_popups()
        
        # 移除其他可能的弹窗
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
        logger.info(f"填写发布内容: 标题={title}, 正文={content}, 标签={tags}")
        
        
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
    
    async def _find_content_editor(self):
        """
        定位正文编辑区（查找容器内的可编辑元素）
        
        Returns:
            编辑器元素，如果找不到则返回None
        """
        try:
            # 先找到编辑器容器
            container = await self.page.wait_for_selector(
                XiaohongshuSelectors.CONTENT_TEXTAREA,
                timeout=BrowserConfig.ELEMENT_TIMEOUT,
                state="visible"
            )
            
            if not container:
                logger.warning("未找到正文编辑器容器")
                return None
            
            # 在容器内查找可编辑元素（contenteditable 或 textarea/input）
            # 优先查找 contenteditable 元素
            editable_element = await container.query_selector('[contenteditable="true"]')
            if editable_element:
                logger.debug("找到 contenteditable 编辑器")
                return editable_element
            
            # 如果没有 contenteditable，查找 textarea 或 input
            textarea = await container.query_selector('textarea')
            if textarea:
                logger.debug("找到 textarea 编辑器")
                return textarea
            
            input_elem = await container.query_selector('input')
            if input_elem:
                logger.debug("找到 input 编辑器")
                return input_elem
            
            # 如果都没找到，尝试使用容器本身（某些情况下容器可能就是可编辑的）
            logger.debug("使用容器作为编辑器")
            return container
            
        except PlaywrightTimeoutError:
            logger.warning("未找到正文编辑器")
            return None
        except Exception as e:
            logger.warning(f"查找正文编辑器失败: {e}")
            return None
    
    async def _input_content(self, content: str):
        """
        输入正文内容
        
        Args:
            content: 正文内容
        """
        logger.info("输入正文内容")
        
        editor = await self._find_content_editor()
        if not editor:
            raise Exception("找不到正文输入框")
        
        try:
            await editor.click()
            await asyncio.sleep(0.2)
            
            # 检查元素是否可编辑
            is_contenteditable = await editor.get_attribute("contenteditable")
            if is_contenteditable == "true":
                # 对于 contenteditable 元素，使用 innerHTML 或 textContent
                await editor.evaluate(f"(el) => el.textContent = ''")
                await editor.type(content, delay=50)
            else:
                # 对于 input/textarea，使用 fill
                await editor.fill(content)
            
            logger.info("正文内容输入完成")
        except Exception as e:
            logger.error(f"输入正文内容失败: {e}")
            raise Exception(f"输入正文内容失败: {e}")
    
    async def _input_tags(self, tags: List[str]):
        """
        输入标签（在正文编辑区以"#话题"形式输入）
        
        Args:
            tags: 标签列表
        """
        if not tags:
            return
        
        logger.info(f"输入标签: {tags}")
        
        # 定位正文编辑区
        editor = await self._find_content_editor()
        if not editor:
            logger.warning("找不到正文编辑器，无法输入标签")
            return
        
        # 进入"可输入话题"的状态
        await self._prepare_for_tag_input(editor)
        
        # 逐个输入标签
        for tag in tags:
            await self._input_single_tag_in_editor(editor, tag)
            await asyncio.sleep(0.5)  # 每个标签完成后等待500ms，给页面时间渲染标签块
    
    async def _prepare_for_tag_input(self, editor):
        """
        进入"可输入话题"的状态
        
        Args:
            editor: 编辑器元素
        """
        logger.debug("准备输入话题状态")
        
        try:
            # 点击编辑器确保焦点
            await editor.click()
            await asyncio.sleep(0.2)
            
            # 光标准备：执行约20次ArrowDown，确保光标移动到文本末尾
            for _ in range(20):
                await self.page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.05)
            
            # 回车两次：创建新的段落或行，避免在已有inline元素中插入#导致联想不弹出
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.1)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.2)
            
            logger.debug("已进入可输入话题状态")
        except Exception as e:
            logger.warning(f"准备输入话题状态失败: {e}")
    
    async def _input_single_tag_in_editor(self, editor, tag: str):
        """
        在编辑器中输入单个标签
        
        Args:
            editor: 编辑器元素
            tag: 标签内容（会自动去掉左侧的#）
        """
        # 规范化：去掉左侧的#
        normalized_tag = tag.lstrip("#").strip()
        if not normalized_tag:
            logger.warning(f"标签为空，跳过: {tag}")
            return
        
        logger.debug(f"输入标签: {normalized_tag}")
        
        try:
            # 确保编辑器有焦点
            await editor.click()
            await asyncio.sleep(0.1)
            
            # 触发联想：先输入#
            await self.page.keyboard.type("#", delay=50)
            await asyncio.sleep(0.1)
            
            # 逐字符输入标签名（每字符约50ms延时）
            for ch in normalized_tag:
                await self.page.keyboard.type(ch, delay=50)
            
            # 等待联想容器出现（约1s）
            await asyncio.sleep(1.0)
            
            # 查找联想容器并选择第一项
            picked = await self._try_pick_topic_suggestion()
            
            if not picked:
                # 未找到或没有联想项：输入一个空格结束当前话题，使其作为"自由话题"插入
                await self.page.keyboard.press("Space")
                logger.debug(f"标签作为自由话题插入: {normalized_tag}")
            else:
                logger.debug(f"标签通过联想项选择: {normalized_tag}")
            
        except Exception as e:
            logger.warning(f"输入标签失败: {normalized_tag}, 错误: {e}")
            # 尝试输入空格作为兜底
            try:
                await self.page.keyboard.press("Space")
            except Exception:
                pass
    
    async def _try_pick_topic_suggestion(self) -> bool:
        """
        尝试选择第一条话题建议
        
        Returns:
            是否成功选择
        """
        try:
            # 等待联想容器出现
            container = await self.page.wait_for_selector(
                XiaohongshuSelectors.TOPIC_SUGGEST_CONTAINER,
                timeout=1000,
                state="visible"
            )
            
            if container:
                # 使用 xpath 在整个页面中查找第一项（因为 xpath 是绝对路径）
                # 或者如果 xpath 是相对路径，可以在容器内查找
                # 这里使用 page.query_selector 因为 xpath 是绝对路径
                item = await self.page.query_selector(XiaohongshuSelectors.TOPIC_SUGGEST_ITEM)
                if item:
                    # 检查项是否在容器内（可选验证）
                    is_visible = await item.is_visible()
                    if is_visible:
                        await item.click()
                        await asyncio.sleep(0.3)
                        logger.debug("成功选择话题联想项")
                        return True
                    else:
                        logger.debug("话题联想项不可见")
                else:
                    logger.debug("联想容器存在但无建议项")
            else:
                logger.debug("未找到话题联想容器")
        except PlaywrightTimeoutError:
            logger.debug("等待话题联想容器超时")
        except Exception as e:
            logger.debug(f"选择话题建议失败: {e}")
        
        return False
    

    async def _click_publish_button(self, is_video: bool = False):
        """
        点击发布按钮
        
        Args:
            is_video: 是否为视频发布
        """
        logger.info(f"点击发布按钮 ({'视频' if is_video else '图文'})")
        
        try:
            if is_video:
                # 视频发布：等待 button.publishBtn 变为可点击（无 disabled 属性且可见）
                # 因为视频处理需要较长时间，按钮可点击即表示处理完成
                logger.info("等待视频发布按钮变为可点击...")
                publish_button = await self.page.wait_for_selector(
                    XiaohongshuSelectors.VIDEO_PUBLISH_BUTTON,
                    timeout=BrowserConfig.ELEMENT_TIMEOUT * 3,  # 视频处理可能需要更长时间
                    state="visible"
                )
                
                # 等待按钮变为可点击（无 disabled 属性）
                max_wait = 60  # 最多等待60秒
                wait_interval = 0.5
                waited = 0
                while waited < max_wait:
                    is_disabled = await publish_button.get_attribute("disabled")
                    if is_disabled is None or is_disabled == "false":
                        # 按钮可点击
                        break
                    await asyncio.sleep(wait_interval)
                    waited += wait_interval
                    logger.debug(f"等待视频处理完成... ({waited:.1f}s)")
                
                if waited >= max_wait:
                    logger.warning("视频处理超时，但继续尝试点击发布按钮")
                
                await publish_button.click()
                logger.info("视频发布按钮已点击")
            else:
                # 图文发布：使用 xpath 精确匹配"发布"按钮
                # 注意：使用 xpath 的 normalize-space 确保精确匹配文本内容
                publish_button = await self.page.wait_for_selector(
                    XiaohongshuSelectors.IMAGE_PUBLISH_BUTTON,
                    timeout=BrowserConfig.ELEMENT_TIMEOUT,
                    state="visible"
                )
                await publish_button.click()
                logger.info("图文发布按钮已点击")
            
            # 等待页面响应
            await asyncio.sleep(1)
            
        except PlaywrightTimeoutError:
            raise Exception("等待发布按钮超时")
        except Exception as e:
            logger.error(f"点击发布按钮失败: {e}")
            raise Exception(f"点击发布按钮失败: {e}")
    
    async def _wait_for_publish_complete(self) -> Optional[str]:
        """
        等待发布完成
        
        Returns:
            发布成功返回笔记ID，失败返回None
        """
        logger.info("等待发布完成")
        
        timeout = BrowserConfig.DEFAULT_TIMEOUT * 2  # 增加发布等待时间
        start_time = asyncio.get_event_loop().time()
        last_log_time = start_time
        check_count = 0
        
        # 记录初始URL
        initial_url = self.page.url
        
        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed = (current_time - start_time) * 1000
            check_count += 1
            
            if elapsed > timeout:
                logger.error(f"等待发布完成超时（{timeout}ms），已等待 {elapsed:.0f}ms")
                raise Exception(f"等待发布完成超时（{timeout}ms）")
            
            # 1. 检查URL是否改变（发布成功后可能跳转到笔记页面）
            current_url = self.page.url
            if current_url != initial_url and "/discovery/item/" in current_url:
                logger.info(f"检测到URL变化，可能已跳转到笔记页面: {current_url}")
                logger.info("发布成功")
                return None  # 不提取笔记ID，直接返回成功
            
            # 2. 检查是否发布成功（多种方式）
            success_selectors = [
                "text=发布成功",
                "text=笔记发布成功",
                "//div[contains(text(), '发布成功')]",
                "//div[contains(text(), '笔记发布成功')]"
            ]
            
            for success_selector in success_selectors:
                try:
                    success_element = await self.page.query_selector(success_selector)
                    if success_element:
                        logger.info("检测到发布成功提示")
                        logger.info("发布成功")
                        return None  # 不提取笔记ID，直接返回成功
                except Exception:
                    pass
            
            # 3. 检查是否有错误
            error_selectors = [
                XiaohongshuSelectors.ERROR_MESSAGE,
                "text=发布失败",
                "text=上传失败",
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'toast-error')]"
            ]
            
            for error_selector in error_selectors:
                try:
                    error_element = await self.page.query_selector(error_selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        if error_text and len(error_text.strip()) > 0:
                            logger.error(f"检测到错误信息: {error_text}")
                            raise Exception(f"发布失败: {error_text}")
                except Exception as e:
                    if "发布失败" in str(e):
                        raise
            
            # 4. 检查发布按钮是否还存在（如果不存在，可能在发布中）
            publish_button = self.page.locator(XiaohongshuSelectors.IMAGE_PUBLISH_BUTTON)
            is_button_visible = await publish_button.is_visible()
            
            # 5. 每5秒记录一次详细状态（避免日志过多）
            if current_time - last_log_time >= 5.0:
                logger.info(f"正在发布中... (已等待 {elapsed/1000:.1f}s / {timeout/1000:.1f}s, 检查次数: {check_count}, 按钮可见: {is_button_visible})")
                last_log_time = current_time
            
            await asyncio.sleep(2)  # 检查间隔
    
    
    async def _dismiss_permission_popups(self):
        """关闭权限请求弹窗（如位置权限）"""
        try:
            # 方法1: 通过 JavaScript 阻止地理位置请求，避免触发权限弹窗
            await self.page.evaluate("""
                () => {
                    // 阻止地理位置请求
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition = function(success, error) {
                            if (error) {
                                error({ code: 1, message: "User denied Geolocation" });
                            }
                        };
                        
                        navigator.geolocation.watchPosition = function(success, error) {
                            if (error) {
                                error({ code: 1, message: "User denied Geolocation" });
                            }
                        };
                        
                        navigator.geolocation.clearWatch = function() {};
                    }
                }
            """)
            
            # 方法2: 尝试查找并点击浏览器权限弹窗的拒绝按钮
            # 浏览器权限弹窗通常在页面加载后立即出现
            await asyncio.sleep(0.5)
            
            # 尝试多种可能的拒绝按钮文本和选择器
            deny_selectors = [
                'button:has-text("Never allow")',
                'button:has-text("拒绝")',
                'button:has-text("Block")',
                'button:has-text("不允许")',
                'button[aria-label*="Never allow"]',
                'button[aria-label*="拒绝"]',
                '[role="button"]:has-text("Never allow")',
                '[role="button"]:has-text("拒绝")',
            ]
            
            for selector in deny_selectors:
                try:
                    deny_button = await self.page.query_selector(selector)
                    if deny_button:
                        # 检查按钮是否可见
                        is_visible = await deny_button.is_visible()
                        if is_visible:
                            await deny_button.click()
                            logger.info(f"已点击权限弹窗拒绝按钮: {selector}")
                            await asyncio.sleep(0.3)
                            break
                except Exception:
                    continue
            
            # 方法3: 尝试按 ESC 键关闭弹窗（如果存在）
            try:
                await self.page.keyboard.press("Escape")
                await asyncio.sleep(0.2)
            except Exception:
                pass
                
        except Exception as e:
            logger.debug(f"处理权限弹窗时出错: {e}")
    
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