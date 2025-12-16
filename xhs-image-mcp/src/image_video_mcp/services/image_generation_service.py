"""批量图片生成服务"""
import uuid
import asyncio
import base64
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
from loguru import logger

from ..clients import ZImageClient, WanT2IClient, GoogleGenAIClient
from ..llm_clients import get_model_provider_client
from ..config import settings
import json


class ImageGenerationService:
    """批量图片生成服务"""

    def __init__(
        self, 
        max_concurrent: int = 1,
        llm_client: Optional[Any] = None,
        auto_init_qwen: bool = False
    ):
        """
        初始化服务
        
        Args:
            max_concurrent: 最大并发数，默认1（Z-Image 已通过 Semaphore 限制并发为1）
            llm_client: LLM 客户端实例，用于根据内容生成图片提示词（可选）
            auto_init_qwen: 是否自动从配置初始化通义千问客户端（如果 llm_client 为 None）
        
        注意：Z-Image 返回图片二进制数据，会保存为临时文件并返回文件路径
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        # 创建临时目录用于保存图片
        self.temp_dir = Path(tempfile.gettempdir()) / "xhs_image_generation"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM 客户端（用于根据内容生成图片提示词）
        self.llm_model_name = None  # 保存模型名称
        if llm_client is None and auto_init_qwen:
            try:
                qwen_config = settings.get_qwen_config()
                self.llm_client = get_model_provider_client(qwen_config)
                # 保存模型名称（用于后续调用）
                self.llm_model_name = qwen_config.get("model") or qwen_config.get("provider_name", "qwen-plus")
                logger.info(f"自动初始化通义千问客户端: {self.llm_model_name}")
            except Exception as e:
                logger.warning(f"自动初始化通义千问客户端失败: {e}")
                self.llm_client = None
                self.llm_model_name = None
        else:
            self.llm_client = llm_client
            # 如果提供了 llm_client，尝试从配置获取模型名称
            if llm_client and hasattr(llm_client, 'model'):
                self.llm_model_name = llm_client.model
        
        # 注册不同 client 类型的提示词模板
        self.prompt_templates: Dict[str, Callable] = {}
        self._register_templates()
        
        logger.info(f"图片生成服务初始化（最大并发数: {max_concurrent}, LLM客户端: {'已配置' if self.llm_client else '未配置'}）")
    
    def _register_templates(self):
        """注册所有 client 类型的提示词模板"""
        self.prompt_templates["ZImageClient"] = self._z_image_template
        self.prompt_templates["WanT2IClient"] = self._wan_t2i_template
        self.prompt_templates["GoogleGenAIClient"] = self._google_genai_template
        logger.debug(f"已注册 {len(self.prompt_templates)} 个提示词模板")
    
    def _load_z_images_prompts(self) -> tuple[str, str]:
        """
        加载 Z-Images 专用的提示词文件
        
        使用相对路径从当前文件位置查找提示词文件：
        - 当前文件：services/image_generation_service.py
        - 提示词文件：prompts/z-images_prompt_*.txt
        
        Returns:
            (system_prompt, user_prompt_template) 元组
        """
        # 使用相对路径：从 services/ 目录到 prompts/ 目录
        current_file = Path(__file__).resolve()
        prompts_dir = current_file.parent.parent / "prompts"
        
        system_prompt_path = prompts_dir / "z-images_prompt_system.txt"
        user_prompt_path = prompts_dir / "z-images_prompt_user.txt"
        
        if not system_prompt_path.exists() or not user_prompt_path.exists():
            raise FileNotFoundError(
                f"Z-Images 提示词文件未找到。"
                f"请确保以下文件存在：\n"
                f"  - {system_prompt_path}\n"
                f"  - {user_prompt_path}"
            )
        
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
        
        with open(user_prompt_path, "r", encoding="utf-8") as f:
            user_prompt_template = f.read()
        
        logger.info(f"已加载 Z-Images 提示词文件: {prompts_dir}")
        return system_prompt, user_prompt_template
    
    async def _generate_image_prompts_from_content(
        self,
        full_content: str,
        client_type: str,
        style: str = ""
    ) -> List[Dict[str, Any]]:
        """
        根据完整内容使用 LLM 生成图片提示词
        
        Args:
            full_content: 完整的内容文本
            client_type: 客户端类型名称
            style: 图片风格，可选。如果提供，将使用指定的风格；如果不提供，LLM 会自动选择风格
            
        Returns:
            生成的页面列表，每个页面包含 {index, type, content}
        """
        if not self.llm_client:
            logger.warning("LLM 客户端未配置，无法生成图片提示词")
            raise ValueError("LLM 客户端未配置，无法根据内容生成图片提示词")
        
        try:
            logger.info(f"开始使用 LLM 根据内容生成图片提示词 (client_type={client_type})")
            
            # 根据客户端类型加载不同的提示词
            if client_type == "ZImageClient":
                # Z-Images 客户端：从文件加载专用提示词
                try:
                    system_prompt, user_prompt_template = self._load_z_images_prompts()
                    # 格式化用户提示词模板
                    user_prompt = user_prompt_template.format(
                        client_type=client_type,
                        full_content=full_content,
                        style=style if style else "未指定，请根据内容自动选择最合适的风格"
                    )
                    logger.info("使用 Z-Images 专用提示词文件")
                except FileNotFoundError as e:
                    logger.warning(f"Z-Images 提示词文件未找到，使用默认提示词: {e}")
                    # 如果文件未找到，使用默认提示词
                    system_prompt = self._get_default_system_prompt()
                    user_prompt = self._get_default_user_prompt(client_type, full_content, style)
            else:
                # 其他客户端：使用默认提示词
                system_prompt = self._get_default_system_prompt()
                user_prompt = self._get_default_user_prompt(client_type, full_content, style)

            # 调用 LLM 客户端（同步调用，在异步环境中运行）
            model_name = self.llm_model_name or getattr(self.llm_client, 'model', None) or "qwen-plus"
            loop = asyncio.get_event_loop()
            result_text = await loop.run_in_executor(
                None,
                lambda: self.llm_client.generate_text(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model=model_name,
                    temperature=1.0,
                    max_output_tokens=8000
                )
            )
            
            # 解析返回结果
            try:
                # 尝试提取 JSON（可能包含 markdown 代码块）
                result_text = result_text.strip()
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                result_data = json.loads(result_text)
                
                # 提取生成的页面列表
                generated_pages = result_data.get("pages", [])
                global_style = result_data.get("global_style", "")
                
                if not generated_pages:
                    raise ValueError("LLM 未生成任何页面")
                
                logger.info(f"LLM 生成图片提示词成功：生成了 {len(generated_pages)} 张图片的提示词")
                
                # 打印生成的内容（JSON 格式化）
                logger.info("=" * 80)
                logger.info("【LLM 生成的图片提示词】")
                logger.info("=" * 80)
                processed_result = {
                    "pages": generated_pages
                }
                if global_style:
                    processed_result["global_style"] = global_style
                logger.info(json.dumps(processed_result, ensure_ascii=False, indent=2))
                logger.info("=" * 80)
                
                return generated_pages
                
            except json.JSONDecodeError as e:
                logger.error(f"LLM 返回的 JSON 格式错误: {e}")
                logger.debug(f"LLM 返回内容: {result_text[:500]}")
                raise ValueError(f"LLM 返回的 JSON 格式错误: {e}")
            
        except Exception as e:
            logger.error(f"LLM 生成图片提示词失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise
    
    def _get_default_system_prompt(self) -> str:
        """获取默认的系统提示词（用于非 Z-Images 客户端）"""
        return """你是一个专业的图片生成提示词优化助手。你的核心任务是：根据用户提供的完整内容文本，生成适合图片生成模型的提示词，用于生成配合内容使用的视觉图片。

请根据内容生成适合的图片提示词，确保提示词清晰、详细，能够指导图片生成模型生成符合要求的图片。"""
    
    def _get_default_user_prompt(self, client_type: str, full_content: str, style: str = "") -> str:
        """获取默认的用户提示词（用于非 Z-Images 客户端）"""
        style_text = f"\n\n风格要求：{style}" if style else "\n\n风格要求：未指定，请根据内容自动选择最合适的风格"
        return f"""请根据以下完整内容文本，生成适合图片生成模型的提示词（客户端类型：{client_type}）。

完整内容：
{full_content}{style_text}

请生成适合的图片提示词，返回 JSON 格式：
{{
    "pages": [
        {{
            "index": 0,
            "type": "cover",
            "content": "图片提示词内容"
        }}
    ]
}}"""
    
    def _get_template_for_client(self, client: Union[ZImageClient, WanT2IClient, GoogleGenAIClient]) -> Callable:
        """
        根据 client 类型获取对应的提示词模板函数
        
        Args:
            client: 图片生成客户端实例
            
        Returns:
            模板函数，如果未找到则返回默认模板
        """
        client_type = type(client).__name__
        template_func = self.prompt_templates.get(client_type)
        
        if template_func:
            logger.debug(f"使用 {client_type} 的专属提示词模板")
            return template_func
        else:
            logger.warning(f"未找到 {client_type} 的提示词模板，使用默认模板")
            return self._z_image_template  # 默认使用 Z-Image 模板

    def _z_image_template(
        self,
        page_content: str,
        page_type: str,
    ) -> str:
        """
        Z-Image 客户端的提示词模板

        Args:
            page_content: 页面内容（已包含文字和配图方案）
            page_type: 页面类型（封面/内容/总结）

        Returns:
            生成的提示词（只包含 page_content）
        """
        # 直接返回 page_content，不添加其他内容
        # page_content 已经包含了极简文字和详细的配图方案
        return page_content
    
    def _wan_t2i_template(
        self,
        page_content: str,
        page_type: str,
    ) -> str:
        """
        通义万相 T2I 客户端的提示词模板

        Args:
            page_content: 页面内容
            page_type: 页面类型（封面/内容/总结）

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

        return f"""生成一张小红书风格的图文内容图片，{page_type_cn}类型。

页面内容：{page_content}

设计要求：
- 小红书爆款图文风格，清新精致
- 竖版 3:4 比例
- 文字清晰可读，排版美观
- 配色和谐，视觉吸引力强
- 适合手机屏幕查看

请生成精美的小红书风格图片，不要有任何logo、水印、手机边框或白色留边。"""
    
    def _google_genai_template(
        self,
        page_content: str,
        page_type: str,
    ) -> str:
        """
        Google GenAI 客户端的提示词模板

        Args:
            page_content: 页面内容
            page_type: 页面类型（封面/内容/总结）

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

        return f"""Create a Xiaohongshu (Little Red Book) style graphic content image, {page_type_cn} type.

Content: {page_content}

Design requirements:
- Xiaohongshu trending graphic style, fresh and refined
- Vertical 3:4 aspect ratio
- Clear, readable text with beautiful layout
- Harmonious color scheme with strong visual appeal
- Suitable for mobile screen viewing
- No logos, watermarks, phone frames, or white borders

Please generate a beautiful Xiaohongshu style image according to the above requirements."""
    
    def _get_prompt_from_template(
        self,
        client: Union[ZImageClient, WanT2IClient, GoogleGenAIClient],
        page_content: str,
        page_type: str,
    ) -> str:
        """
        根据 client 类型使用对应的 prompt 模板生成提示词

        Args:
            client: 图片生成客户端实例
            page_content: 页面内容
            page_type: 页面类型（封面/内容/总结）

        Returns:
            生成的提示词
        """
        template_func = self._get_template_for_client(client)
        return template_func(page_content, page_type)

    async def _generate_single_image(
        self,
        client: Union[ZImageClient, WanT2IClient, GoogleGenAIClient],
        page: Dict[str, Any],
        max_wait_time: int,
    ) -> Dict[str, Any]:
        """
        生成单张图片（内部方法，使用信号量控制并发）
        
        Args:
            client: 图片生成客户端（支持 ZImageClient, WanT2IClient, GoogleGenAIClient）
            page: 页面信息
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            包含生成结果的字典，成功时包含 index, url, type，失败时包含 index, error
        """
        index = page.get("index", 0)
        page_type = page.get("type", "content")
        client_type = type(client).__name__
        
        async with self.semaphore:  # 使用信号量控制并发数
            logger.info(f"开始生成图片: index={index}, type={page_type}, client={client_type}")
            try:
                # 根据 client 类型使用对应的提示词模板
                prompt = self._get_prompt_from_template(
                    client=client,
                    page_content=page.get("content", ""),
                    page_type=page_type,
                )

                # 根据不同的 client 类型调用不同的生成方法
                if isinstance(client, ZImageClient):
                    # Z-Image 客户端：返回 bytes
                    image_data = await client.generate_image(
                        prompt=prompt,
                        height=1365,
                        width=1024,
                        seed=None,
                    )
                elif isinstance(client, GoogleGenAIClient):
                    # Google GenAI 客户端：返回 bytes
                    image_data = await client.generate_image(
                        prompt=prompt,
                        aspect_ratio="3:4",
                    )
                elif isinstance(client, WanT2IClient):
                    # 通义万相 T2I 客户端：返回 Dict，需要异步等待任务完成
                    # 注意：WanT2IClient 返回的是任务信息，需要轮询获取结果
                    # 这里简化处理，实际使用时需要根据任务状态获取图片
                    raise NotImplementedError("WanT2IClient 需要异步任务处理，暂不支持直接生成")
                else:
                    raise ValueError(f"不支持的客户端类型: {client_type}")
                
                # 保存为临时文件
                temp_file = self.temp_dir / f"image_{uuid.uuid4().hex[:8]}_{index}.png"
                temp_file.write_bytes(image_data)
                image_url = str(temp_file.absolute())

                logger.info(f"✅ 页面 [{index}] 生成成功: file={image_url}")
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
        max_wait_time: int = 600,
        client: Optional[Union[ZImageClient, WanT2IClient, GoogleGenAIClient]] = None,
    ) -> Dict[str, Any]:
        """
        批量生成图片

        Args:
            pages: 页面列表，每个页面包含 {index, type, content}
            max_wait_time: 最大等待时间（秒）
            client: 图片生成客户端实例，如果不提供则默认使用 ZImageClient

        Returns:
            包含生成结果的字典
        """
        if not pages:
            raise ValueError("pages 不能为空")

        # 自动生成任务ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # 如果没有提供 client，默认使用 Z-Image
        if client is None:
            client = ZImageClient()
        
        client_type = type(client).__name__
        logger.info(f"开始图片生成任务: task_id={task_id}, pages={len(pages)}, client={client_type}")

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

        # 使用 asyncio.gather 生成所有图片（Z-Image 已通过 Semaphore 限制并发为1）
        logger.info(f"开始生成 {len(all_pages_to_generate)} 张图片（最大并发数: {self.max_concurrent}）")
        
        # 创建所有生成任务
        tasks = [
            self._generate_single_image(
                client=client,
                page=page,
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
    
    async def generate_images_from_content(
        self,
        full_content: str,
        style: str = "",
        max_wait_time: int = 600,
        client: Optional[Union[ZImageClient, WanT2IClient, GoogleGenAIClient]] = None,
    ) -> Dict[str, Any]:
        """
        根据完整内容生成图片
        
        Args:
            full_content: 完整的内容文本
            style: 图片风格，可选。如果提供，将使用指定的风格；如果不提供，LLM 会自动选择风格
            max_wait_time: 最大等待时间（秒）
            client: 图片生成客户端实例，如果不提供则默认使用 ZImageClient
            
        Returns:
            包含生成结果的字典
        """
        if not full_content or not full_content.strip():
            raise ValueError("full_content 不能为空")
        
        # 如果没有提供 client，默认使用 Z-Image
        if client is None:
            client = ZImageClient()
        
        client_type = type(client).__name__
        style_info = f", 风格: {style}" if style else ", 风格: 自动选择"
        logger.info(f"开始根据内容生成图片: full_content长度={len(full_content)}, client={client_type}{style_info}")
        
        # 使用 LLM 根据内容生成图片提示词
        if not self.llm_client:
            raise ValueError("LLM 客户端未配置，无法根据内容生成图片提示词。请设置 auto_init_qwen=True 或提供 llm_client")
        
        logger.info(f"使用 LLM 根据内容生成图片提示词")
        pages = await self._generate_image_prompts_from_content(
            full_content=full_content,
            client_type=client_type,
            style=style
        )
        logger.info(f"LLM 生成图片提示词完成，pages数量: {len(pages)}")
        
        # 调用 generate_images 方法生成图片
        return await self.generate_images(
            pages=pages,
            max_wait_time=max_wait_time,
            client=client,
        )

