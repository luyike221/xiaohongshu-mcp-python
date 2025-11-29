"""大纲生成服务"""
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from loguru import logger

from ..clients.text_client import get_text_chat_client
from ..config import model_config


class OutlineService:
    """大纲生成服务类"""

    def __init__(self, provider_config: Optional[Dict[str, Any]] = None):
        """
        初始化大纲生成服务

        Args:
            provider_config: 服务商配置字典，如果为 None 则使用默认配置
        """
        logger.debug("初始化 OutlineService...")
        self.provider_config = provider_config or self._get_default_config()
        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"OutlineService 初始化完成，使用服务商: {self.provider_config.get('type', 'google_gemini')}")

    def _get_default_config(self) -> dict:
        """获取默认配置（使用阿里百炼）"""
        try:
            return model_config.get_provider_config(provider_type='alibaba_bailian')
        except ValueError:
            # 如果配置未设置，尝试使用 openai_compatible
            try:
                return model_config.get_provider_config(provider_type='openai_compatible')
            except ValueError:
                # 如果配置未设置，返回空配置（会在 _get_client 中报错）
                return {
                    'type': 'alibaba_bailian',
                    'api_key': '',
                }

    def _get_client(self):
        """根据配置获取客户端"""
        if not self.provider_config.get('api_key'):
            raise ValueError(
                "API Key 未配置。\n"
                "解决方案：\n"
                "1. 设置环境变量 GEMINI_API_KEY 或 OPENAI_API_KEY\n"
                "2. 或在调用时传入 provider_config 参数"
            )

        logger.info(f"使用文本服务商: {self.provider_config.get('type', 'google_gemini')}")
        return get_text_chat_client(self.provider_config)

    def _load_prompt_template(self) -> str:
        """加载提示词模板"""
        prompt_path = Path(__file__).parent.parent / "prompts" / "outline_prompt.txt"
        if not prompt_path.exists():
            raise FileNotFoundError(f"提示词模板文件不存在: {prompt_path}")
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        """解析大纲文本为页面列表"""
        # 按 <page> 分割页面（兼容旧的 --- 分隔符）
        if '<page>' in outline_text:
            pages_raw = re.split(r'<page>', outline_text, flags=re.IGNORECASE)
        else:
            # 向后兼容：如果没有 <page> 则使用 ---
            pages_raw = outline_text.split("---")

        pages = []

        for index, page_text in enumerate(pages_raw):
            page_text = page_text.strip()
            if not page_text:
                continue

            page_type = "content"
            type_match = re.match(r"\[(\S+)\]", page_text)
            if type_match:
                type_cn = type_match.group(1)
                type_mapping = {
                    "封面": "cover",
                    "内容": "content",
                    "总结": "summary",
                }
                page_type = type_mapping.get(type_cn, "content")

            pages.append({
                "index": index,
                "type": page_type,
                "content": page_text
            })

        return pages

    def generate_outline(
        self,
        topic: str,
        images: Optional[List[bytes]] = None,
        image_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成大纲

        Args:
            topic: 主题
            images: 参考图片列表（可选，仅当文本模型支持图片时使用）
            image_description: 图片描述文本（可选，当使用 VL 模型分析图片后传入）

        Returns:
            包含大纲信息的字典
        """
        try:
            logger.info(f"开始生成大纲: topic={topic[:50]}..., images={len(images) if images else 0}, has_description={image_description is not None}")
            prompt = self.prompt_template.format(topic=topic)

            # 处理图片描述或图片
            if image_description:
                # 如果提供了图片描述（来自 VL 模型分析），添加到 prompt
                prompt += f"\n\n【参考图片分析结果】\n用户提供了参考图片，VL 模型分析结果如下：\n{image_description}\n\n请根据以上图片分析结果，在生成大纲时充分考虑图片的内容、风格和特点，使生成的内容与图片高度关联。"
                logger.debug("已将 VL 模型分析的图片描述添加到提示词")
            elif images and len(images) > 0:
                # 如果直接提供了图片（文本模型支持图片），添加到 prompt
                prompt += f"\n\n注意：用户提供了 {len(images)} 张参考图片，请在生成大纲时考虑这些图片的内容和风格。这些图片可能是产品图、个人照片或场景图，请根据图片内容来优化大纲，使生成的内容与图片相关联。"
                logger.debug(f"添加了 {len(images)} 张参考图片到提示词（直接传递）")

            # 从配置中获取模型参数
            model = self.provider_config.get('model', 'gemini-2.0-flash-exp')
            temperature = self.provider_config.get('temperature', 1.0)
            max_output_tokens = self.provider_config.get('max_output_tokens', 8000)

            logger.info(f"调用文本生成 API: model={model}, temperature={temperature}")
            outline_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images  # 如果使用了 VL 模型，这里 images 为 None
            )

            logger.debug(f"API 返回文本长度: {len(outline_text)} 字符")
            pages = self._parse_outline(outline_text)
            logger.info(f"大纲解析完成，共 {len(pages)} 页")

            return {
                "success": True,
                "outline": outline_text,
                "pages": pages,
                "has_images": images is not None and len(images) > 0
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"大纲生成失败: {error_msg}")

            # 根据错误类型提供更详细的错误信息
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg:
                detailed_error = (
                    f"API 认证失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API Key 无效或已过期\n"
                    "2. API Key 没有访问该模型的权限\n"
                    "解决方案：检查并更新 API Key"
                )
            elif "model" in error_msg.lower() or "404" in error_msg:
                detailed_error = (
                    f"模型访问失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 模型名称不正确\n"
                    "2. 没有访问该模型的权限\n"
                    "解决方案：检查模型名称配置"
                )
            elif "timeout" in error_msg.lower() or "连接" in error_msg:
                detailed_error = (
                    f"网络连接失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 网络连接不稳定\n"
                    "2. API 服务暂时不可用\n"
                    "3. Base URL 配置错误\n"
                    "解决方案：检查网络连接，稍后重试"
                )
            elif "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                detailed_error = (
                    f"API 配额限制。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API 调用次数超限\n"
                    "2. 账户配额用尽\n"
                    "解决方案：等待配额重置，或升级 API 套餐"
                )
            else:
                detailed_error = (
                    f"大纲生成失败。\n"
                    f"错误详情: {error_msg}\n"
                    "可能原因：\n"
                    "1. Text API 配置错误或密钥无效\n"
                    "2. 网络连接问题\n"
                    "3. 模型无法访问或不存在\n"
                    "建议：检查配置和网络连接"
                )

            return {
                "success": False,
                "error": detailed_error
            }

