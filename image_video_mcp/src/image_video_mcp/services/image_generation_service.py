"""批量图片生成服务"""
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from ..clients import WanT2IClient


class ImageGenerationService:
    """批量图片生成服务"""

    def __init__(self, max_concurrent: int = 2):
        """
        初始化服务
        
        Args:
            max_concurrent: 最大并发数，默认2个线程（降低并发以避免API速率限制）
        
        注意：图片不再保存到本地，直接返回模型提供的 URL
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"图片生成服务初始化（使用 URL 模式，不保存本地文件，最大并发数: {max_concurrent}）")

    def _get_prompt_from_template(
        self,
        page_content: str,
        page_type: str,
        full_outline: str = "",
        user_topic: str = ""
    ) -> str:
        """
        使用小红书 prompt 模板生成提示词

        Args:
            page_content: 页面内容
            page_type: 页面类型（封面/内容/总结）
            full_outline: 完整大纲
            user_topic: 用户原始需求

        Returns:
            生成的提示词
        """
        # 映射页面类型
        type_mapping = {
            "cover": "封面",
            "content": "内容",
            "summary": "总结"
        }
        page_type_cn = type_mapping.get(page_type, "内容")

        return f"""请生成一张小红书风格的图文内容图片。
【合规特别注意的】注意不要带有任何小红书的logo，不要有右下角的用户id以及logo
【合规特别注意的】用户给到的参考图片里如果有水印和logo（尤其是注意右下角，左上角），请一定要去掉

页面内容：
{page_content}

页面类型：{page_type_cn}

如果当前页面类型不是封面页的话，你要参考最后一张图片作为封面的样式

后续生成风格要严格参考封面的风格，要保持风格统一。

设计要求：

1. 整体风格
- 小红书爆款图文风格
- 清新、精致、有设计感
- 适合年轻人审美
- 配色和谐，视觉吸引力强

2. 文字排版
- 文字清晰可读，字号适中
- 重要信息突出显示
- 排版美观，留白合理
- 支持 emoji 和符号
- 如果是封面，标题要大而醒目

3. 视觉元素
- 背景简洁但不单调
- 可以有装饰性元素（如图标、插画）
- 配色温暖或清新
- 保持专业感

4. 页面类型特殊要求

[封面] 类型：
- 标题占据主要位置，字号最大
- 副标题居中或在标题下方
- 整体设计要有吸引力和冲击力
- 背景可以更丰富，有视觉焦点

[内容] 类型：
- 信息层次分明
- 列表项清晰展示
- 重点内容用颜色或粗体强调
- 可以有小图标辅助说明

[总结] 类型：
- 总结性文字突出
- 可以有勾选框或完成标志
- 给人完成感和满足感
- 鼓励性的视觉元素

5. 技术规格
- 竖版 3:4 比例（小红书标准）
- 高清画质
- 适合手机屏幕查看
- 所有文字内容必须完整呈现
- 【特别注意】无论是给到的图片还是参考文字，请仔细思考，让其符合正确的竖屏观看的排版，不能左右旋转或者是倒置。

6. 整体风格一致性
为确保所有页面风格统一，请参考完整的内容大纲和用户原始需求来确定：
- 整体色调和配色方案
- 设计风格（清新/科技/温暖/专业等）
- 视觉元素的一致性
- 排版布局的统一风格

用户原始需求：
{user_topic if user_topic else "未提供"}

完整内容大纲参考：
---
{full_outline if full_outline else "未提供"}
---

请根据以上要求，生成一张精美的小红书风格图片。请直接给出图片，不要有任何手机边框，或者是白色留边。"""

    async def _generate_single_image(
        self,
        client: WanT2IClient,
        page: Dict[str, Any],
        full_outline: str,
        user_topic: str,
        max_wait_time: int,
    ) -> Dict[str, Any]:
        """
        生成单张图片（内部方法，使用信号量控制并发）
        
        Args:
            client: WanT2I 客户端
            page: 页面信息
            full_outline: 完整大纲
            user_topic: 用户主题
            max_wait_time: 最大等待时间
            
        Returns:
            包含生成结果的字典，成功时包含 index, url, type，失败时包含 index, error
        """
        index = page.get("index", 0)
        page_type = page.get("type", "content")
        
        async with self.semaphore:  # 使用信号量控制并发数
            logger.info(f"开始生成图片: index={index}, type={page_type}")
            try:
                # 在获取信号量后，添加小延迟以避免请求过于集中
                await asyncio.sleep(0.5)  # 500ms延迟，避免请求过于集中
                
                prompt = self._get_prompt_from_template(
                    page_content=page.get("content", ""),
                    page_type=page_type,
                    full_outline=full_outline,
                    user_topic=user_topic
                )

                # 生成图片（使用 WanT2I）
                result = await client.generate_image(
                    prompt=prompt,
                    size="1024*1365",
                    seed=None,
                )
                
                # 轮询获取结果
                output = result.get('output', {})
                task_id_img = output.get('task_id')
                task_status = output.get('task_status', 'PENDING')
                
                if task_status in ['PENDING', 'RUNNING']:
                    max_polls = max_wait_time // 10
                    poll_count = 0
                    
                    while poll_count < max_polls:
                        await asyncio.sleep(10)
                        poll_count += 1
                        
                        status_result = await client.get_task_status(task_id_img)
                        status_output = status_result.get('output', {})
                        current_status = status_output.get('task_status', 'UNKNOWN')
                        
                        if current_status == 'SUCCEEDED':
                            results = status_output.get('results', [])
                            if results and results[0].get('url'):
                                image_url = results[0]['url']
                                break
                        elif current_status == 'FAILED':
                            raise Exception(f"图片生成失败: {status_output.get('message', '未知错误')}")
                elif task_status == 'SUCCEEDED':
                    results = output.get('results', [])
                    if results and results[0].get('url'):
                        image_url = results[0]['url']
                    else:
                        raise Exception("未获取到图片 URL")
                else:
                    raise Exception(f"任务状态异常: {task_status}")

                logger.info(f"✅ 页面 [{index}] 生成成功: url={image_url[:50]}...")
                return {
                    "index": index,
                    "url": image_url,
                    "type": page_type
                }

            except Exception as e:
                logger.error(f"❌ 页面 [{index}] 生成失败: {e}")
                return {
                    "index": index,
                    "error": str(e)
                }

    async def generate_images(
        self,
        pages: List[Dict[str, Any]],
        full_outline: str = "",
        user_topic: str = "",
        user_images: Optional[List[bytes]] = None,
        max_wait_time: int = 600,
    ) -> Dict[str, Any]:
        """
        批量生成图片（默认使用 WanT2I）

        Args:
            pages: 页面列表，每个页面包含 {index, type, content}
            full_outline: 完整大纲文本，用于保持风格一致
            user_topic: 用户原始需求，用于保持意图一致
            user_images: 用户上传的参考图片列表（bytes），目前仅 Google GenAI 支持
            max_wait_time: 最大等待时间（秒），仅用于 WanT2I

        Returns:
            包含生成结果的字典
        """
        if not pages:
            raise ValueError("pages 不能为空")

        # 自动生成任务ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        logger.info(f"开始图片生成任务: task_id={task_id}, pages={len(pages)}")

        # 默认使用 WanT2I
        client = WanT2IClient()
        
        # 注意：WanT2I 不支持参考图片，user_images 参数暂未使用

        # 分离封面和其他页面
        cover_page = None
        other_pages = []
        for page in pages:
            if page.get("type") == "cover":
                cover_page = page
            else:
                other_pages.append(page)

        # 如果没有封面，使用第一页作为封面
        if cover_page is None and len(pages) > 0:
            cover_page = pages[0]
            other_pages = pages[1:]

        generated_images = []
        failed_pages = []
        cover_image_url = None

        # 准备所有需要生成的页面（封面优先，其他页面并行）
        all_pages_to_generate = []
        if cover_page:
            all_pages_to_generate.append(cover_page)
        all_pages_to_generate.extend(other_pages)

        # 使用线程池并行生成所有图片（使用 asyncio.gather）
        logger.info(f"开始并行生成 {len(all_pages_to_generate)} 张图片（最大并发数: {self.max_concurrent}）")
        
        # 创建所有生成任务
        tasks = [
            self._generate_single_image(
                client=client,
                page=page,
                full_outline=full_outline,
                user_topic=user_topic,
                max_wait_time=max_wait_time,
            )
            for page in all_pages_to_generate
        ]
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"生成任务异常: {result}")
                continue
            
            if "error" in result:
                failed_pages.append(result)
            else:
                generated_images.append(result)
                # 如果是封面，保存封面URL
                if result.get("type") == "cover":
                    cover_image_url = result.get("url")
        
        # 按index排序生成结果
        generated_images.sort(key=lambda x: x.get("index", 0))

        # 返回结果
        result = {
            "success": len(failed_pages) == 0,
            "task_id": task_id,
            "total": len(pages),
            "completed": len(generated_images),
            "failed": len(failed_pages),
            "images": generated_images,
            "failed_pages": failed_pages
        }

        logger.info(f"图片生成任务完成: task_id={task_id}, 成功={len(generated_images)}, 失败={len(failed_pages)}")
        return result

