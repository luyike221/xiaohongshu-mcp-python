"""
小红书发布功能
实现图文和视频内容的发布
"""

import asyncio
import os
import platform
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
            
            # 验证会话有效性
            logger.info("验证会话有效性...")
            try:
                # 等待页面稳定
                await asyncio.sleep(2)
                
                # 检查是否被重定向到登录页
                current_url = self.page.url
                if "/login" in current_url:
                    raise Exception("会话已失效，页面重定向到登录页，请重新登录")
                
                # 测试会话有效性
                is_valid = await self._test_session_validity()
                if not is_valid:
                    logger.warning("会话验证失败，但继续尝试上传")
                else:
                    logger.info("会话验证通过")
                    
            except Exception as e:
                if "会话已失效" in str(e):
                    raise
                logger.warning(f"会话验证时出现异常: {e}")
            
            # 上传视频（内部已包含等待上传完成的逻辑）
            if context:
                await context.report_progress(progress=30, total=100)
            await self._upload_video(content.video_path, content.cover_path)
            
            # 发送进度通知：视频上传完成
            if context:
                await context.report_progress(progress=60, total=100)
            
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
        
        # 等待发布页面关键元素出现（简化判断：只要发现按钮容器或草稿头部就认为已进入）
        logger.info("等待发布页面关键元素出现...")
        element_found = False
        try:
            # 创建两个等待任务
            async def wait_for_btn():
                try:
                    await self.page.wait_for_selector('//div[@class="btn"]', timeout=BrowserConfig.ELEMENT_TIMEOUT, state="visible")
                    return True
                except Exception:
                    return False
            
            async def wait_for_header():
                try:
                    await self.page.wait_for_selector('//div[contains(@class, "header-draft")]', timeout=BrowserConfig.ELEMENT_TIMEOUT, state="visible")
                    return True
                except Exception:
                    return False
            
            # 使用 asyncio.wait 等待任一任务完成，并用 wait_for 包装以设置总体超时
            timeout_seconds = (BrowserConfig.ELEMENT_TIMEOUT / 1000) + 5  # 转换为秒，并加5秒缓冲
            try:
                async def wait_for_any():
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(wait_for_btn()), asyncio.create_task(wait_for_header())],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    return done, pending
                
                done, pending = await asyncio.wait_for(wait_for_any(), timeout=timeout_seconds)
                
                # 检查完成的任务结果
                for task in done:
                    try:
                        result = await task
                        if result:
                            element_found = True
                            logger.info("检测到发布页面关键元素，确认已进入发布页面")
                            break
                    except Exception as task_error:
                        logger.debug(f"等待任务失败: {task_error}")
                
                # 取消未完成的任务
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass  # 忽略取消任务的异常
                
            except asyncio.TimeoutError:
                logger.warning("等待发布页面关键元素超时，但继续执行")
            
            if not element_found:
                logger.warning("未检测到发布页面关键元素，但继续执行")
                
        except Exception as e:
            logger.warning(f"等待发布页面关键元素时出现异常: {e}，但继续执行")
        
        # 发送进度报告：移除弹窗
        if context:
            await context.report_progress(progress=10, total=100)
    
    async def _select_image_publish_tab(self):
        """选择图文发布标签"""
        logger.info("选择图文发布标签")
        
        try:
            # 步骤1: 先 hover 到按钮容器
            logger.debug("悬停到按钮容器")
            btn_element = await self.page.wait_for_selector(
                '//div[@class="btn"]',
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if btn_element:
                await btn_element.hover()
                await asyncio.sleep(0.3)  # 等待悬停效果
                logger.debug("已悬停到按钮容器")
            else:
                logger.warning("未找到按钮容器，直接尝试点击图文标签")
            
            # 步骤2: 点击图文发布标签
            logger.debug("点击图文发布标签")
            tab_element = await self.page.wait_for_selector(
                '//div[normalize-space(.)="上传图文"][@class="container"]',
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
            # 步骤1: 先 hover 到按钮容器
            logger.debug("悬停到按钮容器")
            btn_element = await self.page.wait_for_selector(
                '//div[@class="btn"]',
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if btn_element:
                await btn_element.hover()
                await asyncio.sleep(0.3)  # 等待悬停效果
                logger.debug("已悬停到按钮容器")
            else:
                logger.warning("未找到按钮容器，直接尝试点击视频标签")
            
            # 步骤2: 点击视频发布标签
            logger.debug("点击视频发布标签")
            video_tab = await self.page.wait_for_selector(
                '//div[normalize-space(.)="上传视频"][@class="container"]',
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
    
    async def _ensure_on_publish_page(self, timeout_seconds: int = 10):
        """确保当前停留在发布页面"""
        logger.info("检查是否停留在发布页面")
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        last_url = None
        attempt = 0

        while asyncio.get_event_loop().time() < deadline:
            attempt += 1
            current_url = self.page.url
            if current_url != last_url:
                logger.debug(f"当前页面URL: {current_url}")
                last_url = current_url

            if "/publish/publish" in current_url and "/login" not in current_url:
                logger.info("确认停留在发布页面")
                return

            if "/login" in current_url:
                logger.warning("检测到登录页面，尝试重新导航到发布页")
                try:
                    await self.page.goto(
                        XiaohongshuUrls.PUBLISH_URL,
                        wait_until="networkidle",
                        timeout=BrowserConfig.PAGE_LOAD_TIMEOUT
                    )
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    logger.warning(f"重新导航到发布页失败: {e}")

            logger.debug(f"不在发布页，等待页面稳定 (第 {attempt} 次检测)")
            await asyncio.sleep(1)

        raise Exception("无法保持在发布页面，请检查登录状态")
    
    async def _simulate_human_behavior(self):
        """模拟人类行为，降低被检测风险"""
        import random
        
        try:
            # 随机延迟 0.5-2 秒
            delay = random.uniform(0.5, 2.0)
            logger.debug(f"随机延迟 {delay:.2f} 秒")
            await asyncio.sleep(delay)
            
            # 模拟鼠标移动
            viewport_size = self.page.viewport_size
            if viewport_size:
                width = viewport_size['width']
                height = viewport_size['height']
                
                # 随机移动鼠标 2-4 次
                move_count = random.randint(2, 4)
                for _ in range(move_count):
                    x = random.randint(100, width - 100)
                    y = random.randint(100, height - 100)
                    await self.page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                
                logger.debug(f"模拟了 {move_count} 次鼠标移动")
            
            # 随机滚动页面
            scroll_distance = random.randint(-200, 200)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await asyncio.sleep(random.uniform(0.2, 0.5))
            logger.debug(f"模拟页面滚动: {scroll_distance}px")
            
        except Exception as e:
            logger.debug(f"模拟人类行为时出错: {e}，继续执行")
    
    async def _test_session_validity(self):
        """测试会话有效性，通过触发一个需要认证的操作"""
        logger.info("测试会话有效性...")
        try:
            # 尝试执行一个需要认证的 JavaScript 调用
            # 小红书会在页面加载时检查登录状态
            result = await self.page.evaluate("""
                () => {
                    // 检查是否有用户信息
                    if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.user) {
                        return { valid: true, user: window.__INITIAL_STATE__.user };
                    }
                    return { valid: false };
                }
            """)
            
            if result and result.get('valid'):
                logger.info("会话有效，检测到用户信息")
                return True
            else:
                logger.warning("会话可能无效，未检测到用户信息")
                return False
                
        except Exception as e:
            logger.warning(f"测试会话有效性时出错: {e}")
            return False

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
            
            # 尝试批量上传所有图片
            try:
                logger.info(f"尝试批量上传 {len(image_paths)} 张图片")
                await upload_input.set_input_files(image_paths)
                logger.info("批量上传成功，等待所有图片上传完成")
            except Exception as e:
                # 如果批量上传失败，尝试逐个上传
                error_msg = str(e)
                if "Non-multiple" in error_msg or "single file" in error_msg.lower():
                    logger.warning(f"输入框不支持批量上传，改为逐个上传: {error_msg}")
                    # 逐个上传
                    for index, image_path in enumerate(image_paths, 1):
                        logger.info(f"上传第 {index}/{len(image_paths)} 张图片: {image_path}")
                        
                        # 每次上传前重新查找上传输入框（因为上传后DOM可能会变化）
                        upload_input = await self.page.wait_for_selector(
                            XiaohongshuSelectors.UPLOAD_INPUT,
                            timeout=BrowserConfig.ELEMENT_TIMEOUT
                        )
                        
                        if not upload_input:
                            raise Exception(f"找不到图片上传输入框（第 {index} 张）")
                        
                        # 逐个上传
                        await upload_input.set_input_files([image_path])
                        
                        # 等待当前图片上传完成（检查已上传的图片数量）
                        await asyncio.sleep(1)  # 给一点时间让上传开始
                        
                        # 等待上传进度更新
                        max_wait = 10  # 最多等待10秒
                        waited = 0
                        while waited < max_wait:
                            uploaded_count = len(await self.page.query_selector_all(
                                XiaohongshuSelectors.UPLOADED_IMAGE
                            ))
                            if uploaded_count >= index:
                                logger.info(f"第 {index} 张图片上传完成")
                                break
                            await asyncio.sleep(0.5)
                            waited += 0.5
                        
                        # 如果不是最后一张，等待一小段时间再上传下一张
                        if index < len(image_paths):
                            await asyncio.sleep(0.5)
                else:
                    # 其他错误，直接抛出
                    raise
            
            # 等待所有图片上传完成
            await self._wait_for_upload_complete(len(image_paths))
            
            logger.info("所有图片上传完成")
            
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
        
        # 记录当前URL
        initial_url = self.page.url
        logger.info(f"上传前页面URL: {initial_url}")
        
        # 设置导航监听器，用于调试
        navigation_events = []
        console_messages = []
        network_errors = []
        
        def on_framenavigated(frame):
            """框架导航事件监听器"""
            try:
                if frame == self.page.main_frame:
                    url = frame.url
                    event_info = {
                        "timestamp": asyncio.get_event_loop().time(),
                        "url": url,
                        "type": "framenavigated"
                    }
                    navigation_events.append(event_info)
                    logger.warning(f"[导航监听] 主框架导航: {url}")
            except Exception as e:
                logger.warning(f"[导航监听] 记录框架导航失败: {e}")
        
        def on_console(msg):
            """控制台消息监听器"""
            try:
                msg_text = msg.text
                msg_type = msg.type
                # 只记录警告和错误，以及包含导航、跳转、redirect等关键词的消息
                if msg_type in ['warning', 'error'] or any(keyword in msg_text.lower() for keyword in ['navigate', 'redirect', '跳转', '导航', 'location', 'href']):
                    console_messages.append({
                        "timestamp": asyncio.get_event_loop().time(),
                        "type": msg_type,
                        "text": msg_text
                    })
                    logger.warning(f"[控制台监听] {msg_type.upper()}: {msg_text}")
            except Exception as e:
                logger.debug(f"[控制台监听] 记录消息失败: {e}")

        def on_response(response):
            """网络响应监听器，用于捕捉认证失败"""
            try:
                status = response.status
                if status != 401:
                    return
                url = response.url
                event_info = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "status": status,
                    "url": url
                }
                network_errors.append(event_info)
                logger.warning(f"[网络监听] 捕捉到 401 响应: {url}")
            except Exception as e:
                logger.debug(f"[网络监听] 记录响应失败: {e}")
        
        # 注册监听器
        self.page.on("framenavigated", on_framenavigated)
        self.page.on("console", on_console)
        self.page.on("response", on_response)
        
        try:
            # 等待视频上传输入框
            logger.info("等待视频上传输入框...")
            video_input = await self.page.wait_for_selector(
                "//input[@class='upload-input']",
                timeout=BrowserConfig.ELEMENT_TIMEOUT
            )
            
            if not video_input:
                raise Exception("找不到视频上传输入框")
            
            logger.info("找到视频上传输入框，准备上传文件...")
            await self._ensure_on_publish_page()
            current_url_before_upload = self.page.url
            logger.info(f"上传前当前URL: {current_url_before_upload}")
            
            # 模拟人类行为：随机延迟和鼠标移动
            logger.info("模拟人类行为...")
            await self._simulate_human_behavior()
            
            # 上传视频
            logger.info("开始设置文件到上传输入框...")
            await video_input.set_input_files([video_path])
            logger.info("文件已设置到上传输入框")
            
            # 等待一小段时间，观察是否有立即的导航
            await asyncio.sleep(1)
            current_url_after_upload = self.page.url
            logger.info(f"上传后1秒当前URL: {current_url_after_upload}")
            
            if current_url_before_upload != current_url_after_upload:
                logger.warning(f"检测到URL变化: {current_url_before_upload} -> {current_url_after_upload}")
                
                # 如果重定向到登录页面（401错误），直接抛出异常
                if "/login" in current_url_after_upload and "redirectReason=401" in current_url_after_upload:
                    logger.error("上传文件时触发401错误，会话已失效")
                    logger.error("这通常是因为：")
                    logger.error("1. Cookie 已过期或失效")
                    logger.error("2. 小红书检测到自动化行为")
                    logger.error("3. 需要重新登录以刷新会话")
                    raise Exception(
                        "上传失败：会话已失效 (401 Unauthorized)。"
                        "请执行以下操作之一：\n"
                        "1. 调用 xiaohongshu_cleanup_login_session 清理会话\n"
                        "2. 调用 xiaohongshu_start_login_session(fresh=True) 重新登录\n"
                        "3. 手动在浏览器中登录小红书创作者中心"
                    )
            
            # 等待视频上传完成（视频上传时间较长）
            logger.info("开始等待视频上传完成...")
            await self._wait_for_video_upload_complete()
            
            # 记录最终URL和所有导航事件
            final_url = self.page.url
            logger.info(f"上传完成后最终URL: {final_url}")
            logger.info(f"共检测到 {len(navigation_events)} 次导航事件")
            for i, event in enumerate(navigation_events, 1):
                logger.info(f"导航事件 {i}: {event}")
            logger.info(f"共检测到 {len(console_messages)} 条相关控制台消息")
            for i, msg in enumerate(console_messages, 1):
                logger.info(f"控制台消息 {i}: [{msg['type']}] {msg['text']}")
            logger.info(f"共检测到 {len(network_errors)} 条 401 响应")
            for i, error in enumerate(network_errors, 1):
                logger.info(f"401 响应 {i}: {error['url']}")
            
            # 如果有封面，上传封面
            if cover_path and os.path.exists(cover_path):
                await self._upload_video_cover(cover_path)
            
            logger.info("视频上传完成")
            
        except PlaywrightTimeoutError:
            raise Exception("等待视频上传输入框超时")
        except Exception as e:
            # 记录错误时的URL和导航事件
            error_url = self.page.url
            logger.error(f"上传视频时发生错误，当前URL: {error_url}")
            logger.error(f"错误发生前共检测到 {len(navigation_events)} 次导航事件")
            for i, event in enumerate(navigation_events, 1):
                logger.error(f"导航事件 {i}: {event}")
            logger.error(f"错误发生前共检测到 {len(console_messages)} 条相关控制台消息")
            for i, msg in enumerate(console_messages, 1):
                logger.error(f"控制台消息 {i}: [{msg['type']}] {msg['text']}")
            logger.error(f"错误发生前共检测到 {len(network_errors)} 条 401 响应")
            for i, error in enumerate(network_errors, 1):
                logger.error(f"401 响应 {i}: {error['url']}")
            if network_errors or ("/login" in error_url and "redirectReason=401" in error_url):
                raise Exception("视频上传失败：检测到登录状态失效 (401)，请重新登录后重试") from e
            raise
        finally:
            # 移除监听器
            try:
                self.page.remove_listener("framenavigated", on_framenavigated)
                self.page.remove_listener("console", on_console)
                self.page.remove_listener("response", on_response)
            except Exception as e:
                logger.debug(f"移除监听器失败: {e}")
    
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
        navigation_detected = False
        last_url = self.page.url
        check_count = 0
        login_detected_at: Optional[float] = None
        
        logger.info(f"[等待上传] 初始URL: {last_url}")
        
        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed_seconds = (current_time - start_time)
            check_count += 1
            
            if elapsed_seconds * 1000 > timeout:
                raise Exception("等待视频上传完成超时")
            
            # 监控URL变化
            try:
                current_url = self.page.url
                if current_url != last_url:
                    logger.warning(f"[等待上传] URL变化检测 (检查 #{check_count}, 已等待 {elapsed_seconds:.1f}秒):")
                    logger.warning(f"  从: {last_url}")
                    logger.warning(f"  到: {current_url}")
                    last_url = current_url
                    navigation_detected = True
                if "/login" in current_url and "redirectReason=401" in current_url:
                    if login_detected_at is None:
                        login_detected_at = elapsed_seconds
                        logger.warning("[等待上传] 检测到进入登录页，监控会话恢复")
                    elif elapsed_seconds - login_detected_at > 15:
                        raise Exception("检测到会话反复跳转至登录页，可能需要重新登录")
                else:
                    login_detected_at = None
            except Exception as e:
                logger.debug(f"[等待上传] 获取URL失败: {e}")
            
            try:
                # 如果检测到导航，等待页面加载完成
                if navigation_detected:
                    logger.info("检测到页面导航，等待页面加载完成...")
                    try:
                        await self.page.wait_for_load_state("networkidle", timeout=10000)
                        await asyncio.sleep(1)  # 额外等待1秒确保页面稳定
                        navigation_detected = False
                        logger.info("页面导航完成，继续检查上传状态")
                        
                        # 导航后检查是否需要重新选择视频标签
                        # 如果找不到发布按钮，可能需要重新选择标签
                        temp_button = await self.page.query_selector(XiaohongshuSelectors.VIDEO_PUBLISH_BUTTON)
                        if not temp_button:
                            logger.info("导航后未找到发布按钮，尝试重新选择视频标签")
                            try:
                                await self._select_video_publish_tab()
                                await asyncio.sleep(1)  # 等待标签切换
                            except Exception as e:
                                logger.warning(f"重新选择视频标签失败: {e}，继续检查")
                    except PlaywrightTimeoutError:
                        logger.warning("等待页面加载超时，继续检查")
                
                # 检查发布按钮是否可点击（视频上传完成的标志）
                # 每次循环都重新获取元素，避免元素失效
                publish_button = await self.page.query_selector(XiaohongshuSelectors.VIDEO_PUBLISH_BUTTON)
                if publish_button:
                    try:
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
                    except Exception as e:
                        # 如果元素失效（可能是导航导致），标记导航并继续
                        if "Execution context was destroyed" in str(e) or "navigation" in str(e).lower():
                            logger.warning(f"检测到页面导航: {e}")
                            navigation_detected = True
                            await asyncio.sleep(2)
                            continue
                        else:
                            raise
                
                # 检查是否有错误
                try:
                    error_element = await self.page.query_selector(XiaohongshuSelectors.ERROR_MESSAGE)
                    if error_element:
                        error_text = await error_element.text_content()
                        raise Exception(f"视频上传失败: {error_text}")
                except Exception as e:
                    # 如果是导航错误，继续等待
                    if "Execution context was destroyed" in str(e) or "navigation" in str(e).lower():
                        logger.warning(f"检查错误时检测到导航: {e}")
                        navigation_detected = True
                        await asyncio.sleep(2)
                        continue
                    elif "视频上传失败" in str(e):
                        raise
                
            except Exception as e:
                # 捕获导航相关的错误
                if "Execution context was destroyed" in str(e) or "navigation" in str(e).lower():
                    logger.warning(f"检测到页面导航: {e}")
                    navigation_detected = True
                    await asyncio.sleep(2)
                    continue
                else:
                    # 其他错误直接抛出
                    raise
                
                # 定期输出状态日志（每10次检查或每5秒）
                if check_count % 10 == 0 or elapsed_seconds % 5 < 2:
                    try:
                        current_url_status = self.page.url
                        publish_button_status = "未找到"
                        try:
                            temp_button = await self.page.query_selector(XiaohongshuSelectors.VIDEO_PUBLISH_BUTTON)
                            if temp_button:
                                is_visible = await temp_button.is_visible()
                                is_disabled = await temp_button.is_disabled()
                                publish_button_status = f"可见={is_visible}, 禁用={is_disabled}"
                        except:
                            pass
                        logger.info(f"[等待上传] 状态检查 #{check_count} - 已等待 {elapsed_seconds:.1f}秒, URL: {current_url_status}, 发布按钮: {publish_button_status}")
                    except Exception as e:
                        logger.debug(f"[等待上传] 状态检查失败: {e}")
            
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
        输入正文内容（模拟手动输入，包括处理换行符）
        
        Args:
            content: 正文内容
        """
        import random
        
        logger.info(f"输入正文内容（模拟手动输入），长度: {len(content)} 字符")
        
        editor = await self._find_content_editor()
        if not editor:
            raise Exception("找不到正文输入框")
        
        try:
            await editor.click()
            await asyncio.sleep(0.3)
            
            # 检查元素是否可编辑
            is_contenteditable = await editor.get_attribute("contenteditable")
            if is_contenteditable == "true":
                # 对于 contenteditable 元素，清空内容
                await editor.evaluate("(el) => { el.textContent = ''; el.innerHTML = ''; }")
                await asyncio.sleep(0.2)
            else:
                # 对于 input/textarea，清空内容
                await editor.fill("")
                await asyncio.sleep(0.2)
            
            # 模拟手动输入：逐字符输入，处理换行符
            logger.info("开始模拟手动输入...")
            
            # 将内容按换行符分割，然后逐段输入
            lines = content.split('\n')
            total_lines = len(lines)
            
            for line_idx, line in enumerate(lines):
                if line:  # 如果行不为空，逐字符输入
                    # 逐字符输入，模拟真实打字速度
                    for char in line:
                        await self.page.keyboard.type(char, delay=random.randint(30, 80))
                        # 偶尔添加更长的延迟，模拟思考停顿
                        if random.random() < 0.05:  # 5% 的概率
                            await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # 如果不是最后一行，按 Enter 键换行
                if line_idx < total_lines - 1:
                    await asyncio.sleep(random.uniform(0.1, 0.2))  # 换行前短暂停顿
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(random.uniform(0.1, 0.2))  # 换行后短暂停顿
            
            # 等待输入完成
            await asyncio.sleep(0.3)
            
            # 验证内容是否已输入
            if is_contenteditable == "true":
                actual_content = await editor.text_content()
            else:
                actual_content = await editor.input_value()
            
            if actual_content and len(actual_content.strip()) > 0:
                logger.info(f"模拟手动输入完成，实际输入长度: {len(actual_content)} 字符")
            else:
                logger.warning("输入后验证内容为空，但继续执行")
            
            # 再次点击确保焦点
            await editor.click()
            await asyncio.sleep(0.2)
            
            logger.info("正文内容输入完成")
        except PlaywrightTimeoutError as e:
            logger.error(f"输入正文内容超时: {e}")
            raise Exception(f"输入正文内容失败: 超时 - {str(e)}")
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
            await asyncio.sleep(0.3)
            
            # 方法1: 优先使用快捷键移动到文本末尾（最可靠的方法）
            logger.debug("使用快捷键移动光标到文本末尾")
            try:
                # 尝试使用 Ctrl+End (Windows/Linux) 或 Cmd+End (Mac)
                if platform.system() == 'Darwin':  # Mac
                    await self.page.keyboard.press("Meta+End")
                else:  # Windows/Linux
                    await self.page.keyboard.press("Control+End")
                await asyncio.sleep(0.3)  # 等待光标移动完成
                logger.debug("已使用快捷键移动光标")
            except Exception as e:
                logger.warning(f"快捷键移动光标失败: {e}，尝试备用方案")
                # 备用：使用 End 键
                try:
                    await self.page.keyboard.press("End")
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
            
            # 方法2: 使用 JavaScript 验证并确保光标在末尾
            logger.debug("使用 JavaScript 验证并确保光标在文本末尾")
            cursor_at_end = await editor.evaluate("""
                (element) => {
                    try {
                        // 检查是否是 textarea 或 input
                        if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
                            // 验证光标位置
                            const cursorPos = element.selectionStart || element.selectionEnd;
                            const textLength = element.value.length;
                            if (cursorPos === textLength) {
                                return true; // 光标已在末尾
                            }
                            // 如果不在末尾，移动到末尾
                            element.focus();
                            element.setSelectionRange(textLength, textLength);
                            return true;
                        }
                        
                        // 对于 contenteditable 元素（如 ProseMirror 编辑器）
                        if (element.contentEditable === 'true' || element.isContentEditable) {
                            const selection = window.getSelection();
                            if (!selection || selection.rangeCount === 0) {
                                // 没有选择，创建新的范围到末尾
                                const range = document.createRange();
                                range.selectNodeContents(element);
                                range.collapse(false);
                                selection.removeAllRanges();
                                selection.addRange(range);
                                return true;
                            }
                            
                            // 获取当前范围
                            const range = selection.getRangeAt(0);
                            const container = range.endContainer;
                            
                            // 检查是否在末尾
                            let isAtEnd = false;
                            if (container.nodeType === Node.TEXT_NODE) {
                                // 文本节点：检查是否在文本末尾
                                isAtEnd = (range.endOffset === container.textContent.length);
                            } else {
                                // 元素节点：检查是否是最后一个子节点
                                isAtEnd = (!container.nextSibling && 
                                          (!container.parentNode || 
                                           container.parentNode === element || 
                                           !container.parentNode.nextSibling));
                            }
                            
                            if (!isAtEnd) {
                                // 不在末尾，移动到末尾
                                const newRange = document.createRange();
                                
                                // 找到最后一个文本节点
                                let lastTextNode = null;
                                const walker = document.createTreeWalker(
                                    element,
                                    NodeFilter.SHOW_TEXT,
                                    null
                                );
                                
                                let node;
                                while (node = walker.nextNode()) {
                                    lastTextNode = node;
                                }
                                
                                if (lastTextNode) {
                                    // 设置到最后一个文本节点的末尾
                                    newRange.setStart(lastTextNode, lastTextNode.textContent.length);
                                    newRange.setEnd(lastTextNode, lastTextNode.textContent.length);
                                } else {
                                    // 没有文本节点，移动到元素末尾
                                    newRange.selectNodeContents(element);
                                    newRange.collapse(false);
                                }
                                
                                selection.removeAllRanges();
                                selection.addRange(newRange);
                            }
                            
                            return true;
                        }
                        
                        return false;
                    } catch (e) {
                        console.error('移动光标失败:', e);
                        return false;
                    }
                }
            """)
            
            if not cursor_at_end:
                logger.warning("JavaScript 方法可能失败，再次尝试快捷键")
                # 再次尝试快捷键
                try:
                    if platform.system() == 'Darwin':
                        await self.page.keyboard.press("Meta+End")
                    else:
                        await self.page.keyboard.press("Control+End")
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
            
            # 等待光标移动完成
            await asyncio.sleep(0.2)
            
            # 回车两次：创建新的段落或行，避免在已有inline元素中插入#导致联想不弹出
            logger.debug("创建新行用于输入标签")
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.2)
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.3)  # 增加等待时间，确保新行创建完成
            
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
            await asyncio.sleep(0.2)
            
            # 确保光标在文本末尾（每次输入标签前都检查）
            logger.debug("确保光标在文本末尾")
            try:
                # 使用快捷键快速移动到末尾
                if platform.system() == 'Darwin':
                    await self.page.keyboard.press("Meta+End")
                else:
                    await self.page.keyboard.press("Control+End")
                await asyncio.sleep(0.2)
            except Exception:
                # 备用：使用 End 键
                try:
                    await self.page.keyboard.press("End")
                    await asyncio.sleep(0.2)
                except Exception:
                    pass
            
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
                            error_text_lower = error_text.lower()
                            
                            # 检查是否是正常的上传状态提示（不是错误）
                            is_uploading_status = (
                                "图片上传中" in error_text or
                                "上传中" in error_text or
                                "请稍后" in error_text or
                                "正在上传" in error_text or
                                "处理中" in error_text
                            )
                            
                            if is_uploading_status:
                                # 这是正常的上传状态，继续等待
                                if current_time - last_log_time >= 5.0:
                                    logger.info(f"检测到上传状态提示: {error_text}，继续等待...")
                                continue
                            
                            # 检测内容字符数限制相关的错误（如 "1232 /1000"）
                            is_char_limit_error = (
                                "/1000" in error_text or 
                                ("字符" in error_text and "1000" in error_text) or
                                ("字数" in error_text and "1000" in error_text) or
                                (error_text.strip().replace(" ", "").replace("/", "").isdigit() and "/1000" in error_text)
                            )
                            if is_char_limit_error:
                                # 抛出明确的错误信息
                                error_msg = (
                                    f"内容字符数超过平台限制！"
                                    f"错误信息: {error_text}。"
                                    f"小红书平台限制内容最多1000字符，请缩短内容后重试。"
                                )
                                logger.error(error_msg)
                                raise Exception(error_msg)
                            logger.error(f"检测到错误信息: {error_text}")
                            raise Exception(f"发布失败: {error_text}")
                except Exception as e:
                    if "发布失败" in str(e) or "内容字符数超过平台限制" in str(e):
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