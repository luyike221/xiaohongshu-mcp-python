"""视觉语言模型服务 - 用于分析图片"""
from typing import List, Optional
from loguru import logger

from ..clients.genai_client import GenAIClient
from ..clients.text_client import get_text_chat_client


class VisionService:
    """视觉语言模型服务类，用于分析图片内容"""

    def __init__(self, provider_config: Optional[dict] = None):
        """
        初始化视觉语言模型服务

        Args:
            provider_config: 服务商配置字典，如果为 None 则使用默认配置（阿里云 qwen3-vl-plus）
        """
        logger.debug("初始化 VisionService...")
        self.provider_config = provider_config or self._get_default_config()
        self.client = self._get_client()
        logger.info(f"VisionService 初始化完成，使用服务商: {self.provider_config.get('type', 'openai_compatible')}, 模型: {self.provider_config.get('model', 'qwen3-vl-plus')}")

    def _get_default_config(self) -> dict:
        """获取默认配置（使用阿里云 qwen3-vl-plus）"""
        import os
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError(
                "VL 模型 API Key 未配置。\n"
                "解决方案：\n"
                "1. 设置环境变量 DASHSCOPE_API_KEY\n"
                "2. 或在配置中传入 api_key"
            )
        return {
            'type': 'openai_compatible',
            'api_key': api_key,
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'model': 'qwen3-vl-plus',
            'temperature': 0.3,
            'max_output_tokens': 2000,
        }

    def _get_client(self):
        """根据配置获取客户端"""
        provider_type = self.provider_config.get('type', 'openai_compatible')
        api_key = self.provider_config.get('api_key')
        
        if not api_key:
            raise ValueError(
                "VL 模型 API Key 未配置。\n"
                "解决方案：\n"
                "1. 设置环境变量 DASHSCOPE_API_KEY（推荐）\n"
                "2. 或设置环境变量 VL_MODEL_API_KEY\n"
                "3. 或在配置中传入 api_key"
            )

        if provider_type == 'google_gemini':
            base_url = self.provider_config.get('base_url')
            return GenAIClient(api_key=api_key, base_url=base_url)
        else:
            # 使用 OpenAI 兼容接口（如 qwen3-vl-plus）
            return get_text_chat_client(self.provider_config)

    def analyze_images(
        self,
        images: List[bytes],
        context: Optional[str] = None
    ) -> str:
        """
        分析图片内容，返回文本描述

        Args:
            images: 图片数据列表（bytes）
            context: 上下文信息（可选），用于指导分析方向

        Returns:
            图片内容的文本描述
        """
        try:
            logger.info(f"开始分析 {len(images)} 张图片...")
            
            # 构建分析提示词
            prompt = "请详细分析这些图片的内容，包括：\n"
            prompt += "1. 图片的主要内容和主题\n"
            prompt += "2. 图片中的关键元素（人物、物品、场景等）\n"
            prompt += "3. 图片的风格特点（色彩、构图、氛围等）\n"
            prompt += "4. 图片可能传达的信息或情感\n"
            prompt += "5. 适合用于小红书图文创作的内容建议\n"
            
            if context:
                prompt += f"\n上下文信息：{context}\n"
                prompt += "请结合上下文信息来分析图片。\n"
            
            prompt += "\n请用中文详细描述，描述要具体、生动，便于后续用于内容创作。"
            
            # 从配置中获取模型参数
            model = self.provider_config.get('model', 'qwen3-vl-plus')
            temperature = self.provider_config.get('temperature', 0.3)
            max_output_tokens = self.provider_config.get('max_output_tokens', 2000)
            
            logger.debug(f"调用 VL 模型分析图片: model={model}")
            analysis_result = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images
            )
            
            logger.info(f"图片分析完成，描述长度: {len(analysis_result)} 字符")
            return analysis_result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"图片分析失败: {error_msg}")
            raise Exception(
                f"图片分析失败。\n"
                f"错误详情: {error_msg}\n"
                "可能原因：\n"
                "1. VL 模型 API Key 未配置或无效\n"
                "2. 网络连接问题\n"
                "3. 图片格式不支持\n"
                "解决方案：检查 VL 模型配置和网络连接"
            )


def get_vision_service(provider_config: Optional[dict] = None) -> VisionService:
    """
    获取视觉语言模型服务实例

    Args:
        provider_config: 服务商配置字典，如果为 None 则使用默认配置

    Returns:
        VisionService 实例
    """
    return VisionService(provider_config=provider_config)

