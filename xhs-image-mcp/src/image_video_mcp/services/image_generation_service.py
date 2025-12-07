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
            llm_client: LLM 客户端实例，用于预处理输入数据（可选）
            auto_init_qwen: 是否自动从配置初始化通义千问客户端（如果 llm_client 为 None）
        
        注意：Z-Image 返回图片二进制数据，会保存为临时文件并返回文件路径
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        # 创建临时目录用于保存图片
        self.temp_dir = Path(tempfile.gettempdir()) / "xhs_image_generation"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM 客户端（用于预处理）
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
        
        # 配置每个 client 类型是否启用 LLM 预处理
        # True 表示启用，False 表示不启用
        self.llm_preprocessing_config: Dict[str, bool] = {
            "ZImageClient": True,  # 默认启用 LLM 预处理
            "WanT2IClient": False,  # 默认不启用
            "GoogleGenAIClient": False,  # 默认不启用
        }
        
        # 注册不同 client 类型的提示词模板
        self.prompt_templates: Dict[str, Callable] = {}
        self._register_templates()
        
        logger.info(f"图片生成服务初始化（最大并发数: {max_concurrent}, LLM预处理: {'启用' if llm_client else '未启用'}）")
    
    def _register_templates(self):
        """注册所有 client 类型的提示词模板"""
        self.prompt_templates["ZImageClient"] = self._z_image_template
        self.prompt_templates["WanT2IClient"] = self._wan_t2i_template
        self.prompt_templates["GoogleGenAIClient"] = self._google_genai_template
        logger.debug(f"已注册 {len(self.prompt_templates)} 个提示词模板")
    
    def set_llm_preprocessing(self, client_type: str, enabled: bool):
        """
        设置指定 client 类型是否启用 LLM 预处理
        
        Args:
            client_type: 客户端类型名称（如 "ZImageClient"）
            enabled: 是否启用预处理
        """
        if client_type in self.llm_preprocessing_config:
            self.llm_preprocessing_config[client_type] = enabled
            logger.info(f"{client_type} 的 LLM 预处理已{'启用' if enabled else '禁用'}")
        else:
            logger.warning(f"未知的客户端类型: {client_type}")
    
    async def _preprocess_with_llm(
        self,
        pages: List[Dict[str, Any]],
        full_outline: str,
        user_topic: str,
        client_type: str
    ) -> tuple[List[Dict[str, Any]], str, str]:
        """
        使用 LLM 对输入数据进行预处理，使其更符合图片生成的要求
        
        Args:
            pages: 原始页面列表
            full_outline: 原始完整大纲
            user_topic: 原始用户主题
            client_type: 客户端类型名称
            
        Returns:
            (处理后的pages, 处理后的full_outline, 处理后的user_topic)
        """
        if not self.llm_client:
            logger.warning("LLM 客户端未配置，跳过预处理")
            return pages, full_outline, user_topic
        
        try:
            logger.info(f"开始使用 LLM 预处理数据 (client_type={client_type})")
            
            # 构建预处理提示词
            system_prompt = """你是一个专业的图片生成提示词优化助手。你的核心任务是：将用户提供的主体内容（完整大纲和pages）转换为适合图片生成模型的提示词，用于生成配合主体内容使用的视觉图片。

═══════════════════════════════════════════════════════════════
【核心理解】
═══════════════════════════════════════════════════════════════

1. 图片的定位：这些图片是配合主体内容（完整大纲和pages）使用的，不是独立存在的
   - 图片应该是对主体内容的视觉补充、强化和配合
   - 图片要呼应、强化、补充主体内容，而不是重复或冲突
   - 图片与主体内容共同构成完整的表达

2. 构图为核心：视觉设计、构图、配色、布局是核心，文字只是辅助
   - 优先通过视觉元素（配色、构图、装饰）传达信息
   - 文字只是辅助说明，能少就少，甚至可以完全没有

3. 文字极简或可无：
   - 图片上的文字要极度精简，只保留最核心的关键词（1-5个字）
   - 如果视觉元素已能充分配合主体内容传达信息，可以完全没有文字
   - 能不用文字就不用，优先用视觉元素传达信息

═══════════════════════════════════════════════════════════════
【工作流程】
═══════════════════════════════════════════════════════════════

第一步：深入理解主体内容
- 仔细分析完整大纲、用户主题和每个页面的内容
- 理解整体要传达的核心信息、目标受众、希望营造的氛围
- 思考每个页面的图片如何配合对应的主体内容

第二步：设计详细构图方案（核心）
为每个页面设计详细的构图方案，这是最重要的部分。构图方案要包括：

1. 视觉风格：清新/温暖/科技/简约/精致/复古等（要与主体内容风格协调）
   - 使用真实场景，不要动漫风格、插画风格
   - 风格描述要自然，不要强调"真实"或"非动漫"

2. 配色方案：
   - 主色调、辅助色、强调色（使用颜色名称，如"淡紫色"、"浅灰蓝色"，不要使用色号如#E1BEE7）
   - 要与主体内容主题呼应，与整体风格协调
   - 不要强调具体的色号、RGB值等

3. 构图布局：
   - 文字位置（上/中/下/左/右，如果无文字则说明视觉焦点位置）
   - 视觉焦点、留白设计
   - 要考虑与主体内容的配合
   - 不要强调字体、字号等文字细节

4. 装饰元素：
   - 图标、插画、背景纹理、边框等具体元素
   - 要与主体内容主题相关，能呼应主体内容
   - 使用真实场景中的元素，不要使用动漫风格的装饰

5. 视觉层次：
   - 如何通过大小、颜色、位置突出重点
   - 要配合主体内容的重点
   - 不要强调字体大小、颜色数值等细节

6. 配合关系说明：
   - 明确说明图片如何呼应、强化、补充主体内容
   - 说明图片与主体内容的配合关系

第三步：提取极简文字或完全省略
- 封面页：核心标题（1-5字）或完全省略
- 内容页：关键词或数字或完全省略
- 总结页：核心结论（1-3字）或完全省略
- 如果视觉元素已能充分配合主体内容传达信息，可以完全没有文字

═══════════════════════════════════════════════════════════════
【输出格式】
═══════════════════════════════════════════════════════════════

每个页面的 content 格式：
"极简文字（或空） | 配图方案：详细的构图设计（强调如何配合主体内容）"

示例1（有文字）：
"重要步骤 | 配图：简约风格，蓝色主调+白色辅助，文字居中上方，下方配真实场景中的步骤元素，留白充足，视觉焦点在场景元素，配合主体内容强调步骤的重要性"

示例2（无文字）：
"| 配图：简约风格，蓝色主调+白色辅助，居中配真实场景元素，留白充足，视觉焦点在场景，通过视觉元素配合主体内容传达信息，无需文字"

注意：
- 使用颜色名称（如"淡紫色"、"浅灰蓝色"），不要使用色号（如#E1BEE7）
- 不要强调字体、字号等文字细节
- 使用真实场景描述，不要使用动漫风格、插画风格
- 但不要在配图方案中明确强调"真实"或"非动漫"，自然描述即可

完整输出 JSON 格式：
{
    "pages": [
        {
            "index": 0, 
            "type": "cover", 
            "content": "极简文字（1-5个字，或空） | 配图方案：详细的构图设计"
        },
        ...
    ],
    "full_outline": "精简后的关键要点框架",
    "user_topic": "精简后的核心关键词",
    "global_style": "整体风格建议（配色方案、视觉风格、设计语言，用于保持所有页面风格统一，强调如何配合主体内容）"
}

═══════════════════════════════════════════════════════════════
【重要约束】
═══════════════════════════════════════════════════════════════

1. pages 数组中每个对象的 index 和 type 字段必须与原始输入完全一致，不能改变
2. 只允许修改 content 字段的内容，其他字段（index、type）必须保持不变
3. 所有转换后的内容必须保持原始信息的核心本质，不能丢失关键信息
4. 不要添加"请生成"、"要求"等指令性语言，直接给出要显示的内容"""

            # 构建输入数据
            pages_json = json.dumps(pages, ensure_ascii=False, indent=2)
            user_prompt = f"""请将以下主体内容转换为适合图片生成模型的提示词（客户端类型：{client_type}）。

═══════════════════════════════════════════════════════════════
【输入的主体内容】
═══════════════════════════════════════════════════════════════

用户主题：
{user_topic if user_topic else "未提供"}

完整大纲：
{full_outline if full_outline else "未提供"}

页面列表：
{pages_json}

═══════════════════════════════════════════════════════════════
【转换要求】
═══════════════════════════════════════════════════════════════

请按照以下步骤进行转换：

【步骤1：理解主体内容】
仔细分析以上主体内容，回答以下问题：
- 完整大纲和pages要传达什么核心信息？
- 目标受众是谁？希望营造什么氛围或情感？
- 整体主题是什么？风格方向是什么？

【步骤2：设计配图方案（核心）】
为每个页面设计详细的构图方案，这是最重要的部分：

1. 思考配合关系：
   - 这个页面的图片如何配合对应的主体内容？
   - 图片如何呼应、强化、补充主体内容，而不是重复？

2. 设计构图方案（必须详细）：
   - 视觉风格：具体风格名称（要与主体内容协调，使用真实场景，不要动漫风格）
   - 配色方案：主色调、辅助色、强调色（使用颜色名称如"淡紫色"、"浅灰蓝色"，不要使用色号如#E1BEE7）
   - 构图布局：文字位置/视觉焦点位置、留白设计、视觉层次（不要强调字体、字号等细节）
   - 装饰元素：真实场景中的元素、背景纹理等（要与主题相关，使用真实场景，不要动漫风格）
   - 配合说明：明确说明如何配合主体内容
   - 注意：使用真实场景描述，但不要在配图方案中明确强调"真实"或"非动漫"，自然描述即可

3. 提取极简文字或完全省略：
   - 封面页：核心标题（1-5字）或完全省略
   - 内容页：关键词或数字或完全省略
   - 总结页：核心结论（1-3字）或完全省略
   - 如果视觉元素已能充分配合主体内容传达信息，可以完全没有文字

【步骤3：整体风格建议】
根据对主体内容的理解，提供统一的整体风格建议（global_style）：
- 整体配色方案（具体颜色）
- 视觉风格、设计语言
- 构图原则
- 用于确保所有页面风格统一，构图协调

═══════════════════════════════════════════════════════════════
【输出格式要求】
═══════════════════════════════════════════════════════════════

每个页面的 content 格式：
"极简文字（或空） | 配图方案：详细的构图设计（强调如何配合主体内容）"

配图方案必须包括：
- 视觉风格、具体配色（使用颜色名称，不要色号）、构图布局、装饰元素、视觉层次
- 以及如何配合主体内容的说明
- 注意：使用真实场景描述，不要强调字体、色号等细节，不要使用动漫风格

═══════════════════════════════════════════════════════════════
【重要提醒】
═══════════════════════════════════════════════════════════════

1. 图片是配合主体内容使用的，不是独立存在的
2. 构图为核心，文字只是辅助，甚至可以完全没有文字
3. 配图方案要非常详细，要明确说明如何配合主体内容
4. pages 中每个对象的 index 和 type 必须与原始输入完全一致，不能改变
5. 只允许修改 content 字段的内容

请返回转换后的 JSON 格式数据。"""

            # 调用 LLM 客户端（同步调用，在异步环境中运行）
            # 获取模型名称（使用保存的模型名称或默认值）
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
                
                # 提取处理后的数据
                processed_pages = result_data.get("pages", pages)
                processed_outline = result_data.get("full_outline", full_outline)
                processed_topic = result_data.get("user_topic", user_topic)
                global_style = result_data.get("global_style", "")  # 整体风格建议（可选）
                
                logger.info(f"LLM 预处理成功：处理了 {len(processed_pages)} 个页面")
                
                # 打印预处理后的内容（JSON 格式化）
                logger.info("=" * 80)
                logger.info("【LLM 预处理后的内容】")
                logger.info("=" * 80)
                processed_result = {
                    "user_topic": processed_topic,
                    "full_outline": processed_outline,
                    "pages": processed_pages
                }
                if global_style:
                    processed_result["global_style"] = global_style
                logger.info(json.dumps(processed_result, ensure_ascii=False, indent=2))
                logger.info("=" * 80)
                
                return processed_pages, processed_outline, processed_topic
                
            except json.JSONDecodeError as e:
                logger.error(f"LLM 返回的 JSON 格式错误: {e}")
                logger.debug(f"LLM 返回内容: {result_text[:500]}")
                # JSON 解析失败，返回原始数据
                return pages, full_outline, user_topic
            
        except Exception as e:
            logger.error(f"LLM 预处理失败: {e}，使用原始数据")
            import traceback
            logger.debug(traceback.format_exc())
            return pages, full_outline, user_topic
    
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
        full_outline: str = "",
        user_topic: str = ""
    ) -> str:
        """
        Z-Image 客户端的提示词模板

        Args:
            page_content: 页面内容（已包含文字和配图方案）
            page_type: 页面类型（封面/内容/总结）
            full_outline: 完整大纲（不使用）
            user_topic: 用户原始需求（不使用）

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
        full_outline: str = "",
        user_topic: str = ""
    ) -> str:
        """
        通义万相 T2I 客户端的提示词模板

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

        return f"""生成一张小红书风格的图文内容图片，{page_type_cn}类型。

页面内容：{page_content}

设计要求：
- 小红书爆款图文风格，清新精致
- 竖版 3:4 比例
- 文字清晰可读，排版美观
- 配色和谐，视觉吸引力强
- 适合手机屏幕查看

用户需求：{user_topic if user_topic else "未提供"}
完整大纲：{full_outline if full_outline else "未提供"}

请生成精美的小红书风格图片，不要有任何logo、水印、手机边框或白色留边。"""
    
    def _google_genai_template(
        self,
        page_content: str,
        page_type: str,
        full_outline: str = "",
        user_topic: str = ""
    ) -> str:
        """
        Google GenAI 客户端的提示词模板

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

        return f"""Create a Xiaohongshu (Little Red Book) style graphic content image, {page_type_cn} type.

Content: {page_content}

Design requirements:
- Xiaohongshu trending graphic style, fresh and refined
- Vertical 3:4 aspect ratio
- Clear, readable text with beautiful layout
- Harmonious color scheme with strong visual appeal
- Suitable for mobile screen viewing
- No logos, watermarks, phone frames, or white borders

User requirement: {user_topic if user_topic else "Not provided"}
Full outline: {full_outline if full_outline else "Not provided"}

Please generate a beautiful Xiaohongshu style image according to the above requirements."""
    
    def _get_prompt_from_template(
        self,
        client: Union[ZImageClient, WanT2IClient, GoogleGenAIClient],
        page_content: str,
        page_type: str,
        full_outline: str = "",
        user_topic: str = ""
    ) -> str:
        """
        根据 client 类型使用对应的 prompt 模板生成提示词

        Args:
            client: 图片生成客户端实例
            page_content: 页面内容
            page_type: 页面类型（封面/内容/总结）
            full_outline: 完整大纲
            user_topic: 用户原始需求

        Returns:
            生成的提示词
        """
        template_func = self._get_template_for_client(client)
        return template_func(page_content, page_type, full_outline, user_topic)

    async def _generate_single_image(
        self,
        client: Union[ZImageClient, WanT2IClient, GoogleGenAIClient],
        page: Dict[str, Any],
        full_outline: str,
        user_topic: str,
        max_wait_time: int,
    ) -> Dict[str, Any]:
        """
        生成单张图片（内部方法，使用信号量控制并发）
        
        Args:
            client: 图片生成客户端（支持 ZImageClient, WanT2IClient, GoogleGenAIClient）
            page: 页面信息
            full_outline: 完整大纲
            user_topic: 用户主题
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
                    full_outline=full_outline,
                    user_topic=user_topic
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
        full_outline: str = "",
        user_topic: str = "",
        max_wait_time: int = 600,
        client: Optional[Union[ZImageClient, WanT2IClient, GoogleGenAIClient]] = None,
    ) -> Dict[str, Any]:
        """
        批量生成图片

        Args:
            pages: 页面列表，每个页面包含 {index, type, content}
            full_outline: 完整大纲文本，用于保持风格一致
            user_topic: 用户原始需求，用于保持意图一致
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

        # 根据配置决定是否进行 LLM 预处理
        should_preprocess = self.llm_preprocessing_config.get(client_type, False)
        if should_preprocess and self.llm_client:
            logger.info(f"对 {client_type} 启用 LLM 预处理")
            pages, full_outline, user_topic = await self._preprocess_with_llm(
                pages=pages,
                full_outline=full_outline,
                user_topic=user_topic,
                client_type=client_type
            )
            logger.info(f"LLM 预处理完成，pages数量: {len(pages)}")
        else:
            if should_preprocess and not self.llm_client:
                logger.warning(f"{client_type} 配置了预处理，但 LLM 客户端未初始化，跳过预处理")
            else:
                logger.debug(f"{client_type} 未启用 LLM 预处理，使用原始数据")

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

