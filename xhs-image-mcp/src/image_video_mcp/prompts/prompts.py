"""
MCP Prompt 模板定义

这些 Prompt 可以在 MCP Inspector 的 Prompts 标签页中查看和使用
使用 @mcp.prompt 装饰器注册 Prompt

注意：所有 Prompt 内容现在从 Skills 加载
"""

from loguru import logger
from ..skills import SkillManager


def register_prompts(mcp):
    """
    注册所有 Prompt 模板到 FastMCP 实例（从 Skills 加载）
    
    Args:
        mcp: FastMCP 实例
    """
    # 初始化技能管理器
    skill_manager = SkillManager()
    # 1. 图像生成提示词优化 Prompt
    @mcp.prompt()
    def optimize_image_prompt(original_prompt: str) -> str:
        """
        优化图像生成提示词，使其更加详细和专业
        
        Args:
            original_prompt: 原始提示词
        
        Returns:
            优化后的提示词、负面提示词建议和推荐尺寸
        """
        return skill_manager.format_skill(
            "image_prompt_optimization",
            original_prompt=original_prompt
        ) or f"优化以下图像生成提示词，使其更加详细和专业：\n\n原始提示词: {original_prompt}"

    # 2. 视频生成提示词模板
    @mcp.prompt()
    def video_generation_prompt(topic: str, duration: int, style: str, scene: str, action: str) -> str:
        """
        生成视频创建提示词
        
        Args:
            topic: 视频主题
            duration: 视频时长（秒）
            style: 视频风格
            scene: 场景描述
            action: 动作描述
        
        Returns:
            详细的视频生成提示词
        """
        return skill_manager.format_skill(
            "video_generation",
            topic=topic,
            duration=duration,
            style=style,
            scene=scene,
            action=action
        ) or f"生成一个关于 {topic} 的视频，视频时长为 {duration} 秒。"

    # 3. 图像风格描述 Prompt
    @mcp.prompt()
    def image_style_description(subject: str, style_type: str, purpose: str) -> str:
        """
        为特定主题生成详细的图像风格描述
        
        Args:
            subject: 图像主题/主体
            style_type: 风格类型（如：写实、插画、水彩等）
            purpose: 用途（如：社交媒体、广告等）
        
        Returns:
            详细的图像风格描述提示词
        """
        return skill_manager.format_skill(
            "image_style_description",
            subject=subject,
            style_type=style_type,
            purpose=purpose
        ) or f"为以下主题生成详细的图像风格描述：\n\n主题: {subject}\n风格类型: {style_type}\n用途: {purpose}"

    # 4. 负面提示词生成 Prompt（使用 Resource）
    @mcp.prompt()
    def generate_negative_prompt(positive_prompt: str, image_type: str) -> str:
        """
        为正面提示词生成对应的负面提示词（使用负面提示词资源库）
        
        Args:
            positive_prompt: 正面提示词
            image_type: 图像类型（如：人物、风景、产品等）
        
        Returns:
            负面提示词列表
        """
        # 从资源中获取负面提示词库
        try:
            negative_prompts = mcp.get_resource("resource://negative_prompts")
            # 根据图像类型选择合适的负面提示词
            base_negative = negative_prompts.get("general", "")
            type_specific = negative_prompts.get(image_type.lower(), "")
            
            combined_negative = f"{base_negative}, {type_specific}".strip(", ")
        except Exception:
            # 如果资源获取失败，使用默认值
            combined_negative = "low resolution, blurry, distorted, low quality, worst quality"
        
        return skill_manager.format_skill(
            "negative_prompt_generation",
            positive_prompt=positive_prompt,
            image_type=image_type,
            combined_negative=combined_negative
        ) or f"为以下图像生成提示词生成对应的负面提示词（negative prompt）：\n\n正面提示词: {positive_prompt}\n图像类型: {image_type}"

    # 5. 批量图像生成计划 Prompt
    @mcp.prompt()
    def batch_image_generation_plan(theme: str, count: int, purpose: str, style_requirement: str) -> str:
        """
        为批量图像生成制定计划
        
        Args:
            theme: 主题系列
            count: 生成数量
            purpose: 用途
            style_requirement: 风格要求
        
        Returns:
            批量图像生成计划
        """
        return skill_manager.format_skill(
            "batch_image_planning",
            theme=theme,
            count=count,
            purpose=purpose,
            style_requirement=style_requirement
        ) or f"为以下需求制定批量图像生成计划：\n\n主题系列: {theme}\n生成数量: {count} 张\n用途: {purpose}"

    # 6. 小红书风格图片生成 Prompt
    @mcp.prompt()
    def xiaohongshu_image_prompt(
        page_content: str,
        page_type: str = "内容",
        user_topic: str = "",
        full_outline: str = ""
    ) -> str:
        """
        生成小红书风格的图文内容图片提示词
        
        Args:
            page_content: 页面内容
            page_type: 页面类型（封面/内容/总结），默认 "内容"
            user_topic: 用户原始需求（可选）
            full_outline: 完整内容大纲（可选）
        
        Returns:
            完整的小红书风格图片生成提示词
        """
        return skill_manager.format_skill(
            "xiaohongshu_image_prompt",
            page_content=page_content,
            page_type=page_type,
            user_topic=user_topic if user_topic else "未提供",
            full_outline=full_outline if full_outline else "未提供"
        ) or f"请生成一张小红书风格的图文内容图片。\n\n页面内容：\n{page_content}\n\n页面类型：{page_type}"

    logger.info("已注册 6 个 Prompt 模板，可在 MCP Inspector 的 Prompts 标签页中查看")

