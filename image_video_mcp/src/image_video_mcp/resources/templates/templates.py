"""
MCP Resource Template 资源模板定义

Resource Templates 使用 URI 模板（包含占位符）来定义动态资源
LLM 可以通过提供具体参数来访问不同的资源实例
"""

from loguru import logger
from ..resources import (
    IMAGE_STYLES,
    NEGATIVE_PROMPTS,
    IMAGE_SIZES,
    VIDEO_STYLES,
    GENERATION_CONFIGS,
    PROMPT_TEMPLATES
)


def register_resource_templates(mcp):
    """
    注册所有 Resource Template 到 FastMCP 实例
    
    Args:
        mcp: FastMCP 实例
    """
    
    # 1. 图像风格模板 - 根据风格名称获取风格配置
    @mcp.resource("resource://styles/{style_name}")
    def get_image_style(style_name: str) -> dict:
        """
        根据风格名称获取图像风格配置
        
        Args:
            style_name: 风格名称（realistic, anime, watercolor, oil_painting, 3d_render, sketch）
        
        Returns:
            风格配置字典
        """
        # 从数据中获取风格配置
        try:
            style = IMAGE_STYLES.get(style_name.lower())
            if style:
                return {
                    "style_name": style_name,
                    **style
                }
            else:
                return {
                    "error": f"风格 '{style_name}' 不存在",
                    "available_styles": list(IMAGE_STYLES.keys())
                }
        except Exception as e:
            logger.error(f"获取风格配置失败: {e}")
            return {
                "error": f"获取风格配置失败: {str(e)}"
            }
    
    # 2. 负面提示词模板 - 根据图像类型获取负面提示词
    @mcp.resource("resource://negative_prompts/{image_type}")
    def get_negative_prompt_by_type(image_type: str) -> dict:
        """
        根据图像类型获取负面提示词
        
        Args:
            image_type: 图像类型（general, portrait, landscape, product）
        
        Returns:
            负面提示词字典
        """
        try:
            negative = NEGATIVE_PROMPTS.get(image_type.lower(), "")
            if negative:
                return {
                    "image_type": image_type,
                    "negative_prompt": negative,
                    "description": f"适用于 {image_type} 类型的负面提示词"
                }
            else:
                return {
                    "error": f"图像类型 '{image_type}' 不存在",
                    "available_types": list(NEGATIVE_PROMPTS.keys())
                }
        except Exception as e:
            logger.error(f"获取负面提示词失败: {e}")
            return {
                "error": f"获取负面提示词失败: {str(e)}"
            }
    
    # 3. 图像尺寸模板 - 根据尺寸名称获取尺寸配置
    @mcp.resource("resource://sizes/{size_name}")
    def get_image_size(size_name: str) -> dict:
        """
        根据尺寸名称获取图像尺寸配置
        
        Args:
            size_name: 尺寸名称（square_1k, square_2k, portrait_16_9, portrait_9_16, 等）
        
        Returns:
            尺寸配置字典
        """
        try:
            size = IMAGE_SIZES.get(size_name.lower())
            if size:
                return {
                    "size_name": size_name,
                    **size
                }
            else:
                return {
                    "error": f"尺寸 '{size_name}' 不存在",
                    "available_sizes": list(IMAGE_SIZES.keys())
                }
        except Exception as e:
            logger.error(f"获取尺寸配置失败: {e}")
            return {
                "error": f"获取尺寸配置失败: {str(e)}"
            }
    
    # 4. 视频风格模板 - 根据风格名称获取视频风格配置
    @mcp.resource("resource://video_styles/{style_name}")
    def get_video_style(style_name: str) -> dict:
        """
        根据风格名称获取视频风格配置
        
        Args:
            style_name: 视频风格名称（cinematic, documentary, commercial, vlog, timelapse）
        
        Returns:
            视频风格配置字典
        """
        try:
            style = VIDEO_STYLES.get(style_name.lower())
            if style:
                return {
                    "style_name": style_name,
                    **style
                }
            else:
                return {
                    "error": f"视频风格 '{style_name}' 不存在",
                    "available_styles": list(VIDEO_STYLES.keys())
                }
        except Exception as e:
            logger.error(f"获取视频风格配置失败: {e}")
            return {
                "error": f"获取视频风格配置失败: {str(e)}"
            }
    
    # 5. 生成配置模板 - 根据配置名称获取生成配置
    @mcp.resource("resource://configs/{config_name}")
    def get_generation_config(config_name: str) -> dict:
        """
        根据配置名称获取生成配置
        
        Args:
            config_name: 配置名称（high_quality, fast_generation, social_media, artistic）
        
        Returns:
            生成配置字典
        """
        try:
            config = GENERATION_CONFIGS.get(config_name.lower())
            if config:
                return {
                    "config_name": config_name,
                    **config
                }
            else:
                return {
                    "error": f"配置 '{config_name}' 不存在",
                    "available_configs": list(GENERATION_CONFIGS.keys())
                }
        except Exception as e:
            logger.error(f"获取生成配置失败: {e}")
            return {
                "error": f"获取生成配置失败: {str(e)}"
            }
    
    # 6. 提示词模板 - 根据模板名称获取提示词模板
    @mcp.resource("resource://prompt_templates/{template_name}")
    def get_prompt_template(template_name: str) -> dict:
        """
        根据模板名称获取提示词模板
        
        Args:
            template_name: 模板名称（portrait, landscape, product, animal, abstract）
        
        Returns:
            提示词模板字典
        """
        try:
            template = PROMPT_TEMPLATES.get(template_name.lower())
            if template:
                return {
                    "template_name": template_name,
                    "template": template,
                    "description": f"提示词模板: {template_name}",
                    "usage": f"使用此模板时，替换模板中的占位符变量"
                }
            else:
                return {
                    "error": f"模板 '{template_name}' 不存在",
                    "available_templates": list(PROMPT_TEMPLATES.keys())
                }
        except Exception as e:
            logger.error(f"获取提示词模板失败: {e}")
            return {
                "error": f"获取提示词模板失败: {str(e)}"
            }
    
    # 7. 组合配置模板 - 根据风格和尺寸组合生成完整配置
    @mcp.resource("resource://combined_config/{style_name}/{size_name}")
    def get_combined_config(style_name: str, size_name: str) -> dict:
        """
        根据风格和尺寸组合生成完整的图像生成配置
        
        Args:
            style_name: 风格名称
            size_name: 尺寸名称
        
        Returns:
            组合后的完整配置字典
        """
        try:
            # 获取风格配置（直接访问数据）
            style_data = IMAGE_STYLES.get(style_name.lower())
            if not style_data:
                return {
                    "error": f"风格 '{style_name}' 不存在",
                    "available_styles": list(IMAGE_STYLES.keys())
                }
            style = {
                "style_name": style_name,
                **style_data
            }
            
            # 获取尺寸配置（直接访问数据）
            size_data = IMAGE_SIZES.get(size_name.lower())
            if not size_data:
                return {
                    "error": f"尺寸 '{size_name}' 不存在",
                    "available_sizes": list(IMAGE_SIZES.keys())
                }
            size = {
                "size_name": size_name,
                **size_data
            }
            
            # 组合配置
            return {
                "style": style,
                "size": size,
                "recommended_prompt": f"使用 {style.get('keywords', '')} 风格",
                "recommended_negative": style.get("negative_keywords", ""),
                "width": size.get("width", 1280),
                "height": size.get("height", 1280),
                "description": f"组合配置: {style.get('name', style_name)} 风格 + {size.get('name', size_name)} 尺寸"
            }
        except Exception as e:
            logger.error(f"获取组合配置失败: {e}")
            return {
                "error": f"获取组合配置失败: {str(e)}"
            }
    
    # 8. 完整生成方案模板 - 根据主题、风格、尺寸生成完整方案
    @mcp.resource("resource://generation_plan/{theme}/{style_name}/{size_name}")
    def get_generation_plan(theme: str, style_name: str, size_name: str) -> dict:
        """
        根据主题、风格、尺寸生成完整的图像生成方案
        
        Args:
            theme: 图像主题
            style_name: 风格名称
            size_name: 尺寸名称
        
        Returns:
            完整的生成方案字典
        """
        try:
            # 获取风格配置（直接访问数据）
            style_data = IMAGE_STYLES.get(style_name.lower())
            if not style_data:
                return {
                    "error": f"风格 '{style_name}' 不存在",
                    "available_styles": list(IMAGE_STYLES.keys())
                }
            style = {
                "style_name": style_name,
                **style_data
            }
            
            # 获取尺寸配置（直接访问数据）
            size_data = IMAGE_SIZES.get(size_name.lower())
            if not size_data:
                return {
                    "error": f"尺寸 '{size_name}' 不存在",
                    "available_sizes": list(IMAGE_SIZES.keys())
                }
            size = {
                "size_name": size_name,
                **size_data
            }
            
            # 获取负面提示词（使用通用类型）
            negative_prompt = NEGATIVE_PROMPTS.get("general", "")
            
            # 生成完整方案
            return {
                "theme": theme,
                "style": style,
                "size": size,
                "prompt_suggestion": f"{theme}, {style.get('keywords', '')}",
                "negative_prompt": negative_prompt,
                "width": size.get("width", 1280),
                "height": size.get("height", 1280),
                "description": f"为主题 '{theme}' 生成的完整方案",
                "steps": [
                    f"1. 使用主题: {theme}",
                    f"2. 应用风格: {style.get('name', style_name)}",
                    f"3. 设置尺寸: {size.get('name', size_name)} ({size.get('width')}x{size.get('height')})",
                    f"4. 使用负面提示词: {negative_prompt[:50]}..."
                ]
            }
        except Exception as e:
            logger.error(f"生成完整方案失败: {e}")
            return {
                "error": f"生成完整方案失败: {str(e)}"
            }
    
    logger.info("已注册 8 个 Resource Template 模板，可在 MCP Inspector 的 Resources 标签页中查看")

