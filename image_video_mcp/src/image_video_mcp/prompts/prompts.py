"""
MCP Prompt 模板定义

这些 Prompt 可以在 MCP Inspector 的 Prompts 标签页中查看和使用
使用 @mcp.prompt 装饰器注册 Prompt
"""

from loguru import logger


def register_prompts(mcp):
    """
    注册所有 Prompt 模板到 FastMCP 实例
    
    Args:
        mcp: FastMCP 实例
    """
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
        return f"""优化以下图像生成提示词，使其更加详细和专业：

原始提示词: {original_prompt}

请提供：
1. 优化后的提示词（包含更多细节、风格、质量描述）
2. 推荐的负面提示词（negative_prompt）
3. 建议的图像尺寸（width x height）

优化后的提示词应该包含：
- 主体描述（清晰明确）
- 风格描述（如：写实、卡通、水彩等）
- 质量描述（如：高清、4K、细节丰富等）
- 光照和氛围描述（如：自然光、柔和光线、温暖色调等）
- 构图描述（如：居中构图、三分法、特写等）"""

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
        return f"""生成一个关于 {topic} 的视频，视频时长为 {duration} 秒。

视频要求：
- 主题: {topic}
- 时长: {duration} 秒
- 风格: {style}
- 场景: {scene}
- 动作: {action}

请生成详细的视频生成提示词，包括：
1. 视频内容描述
2. 镜头运动方式（如：推拉、摇移、跟随等）
3. 画面风格和色调
4. 音效建议（如果需要）"""

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
        return f"""为以下主题生成详细的图像风格描述：

主题: {subject}
风格类型: {style_type}
用途: {purpose}

请生成包含以下要素的详细提示词：
- 主体: {subject}
- 风格: {style_type}（如：写实、插画、水彩、油画、3D渲染等）
- 色彩: 建议的色彩方案和色调
- 构图: 推荐的构图方式
- 细节: 需要突出的细节特征
- 氛围: 整体氛围和情绪

用途说明: {purpose}（如：社交媒体、广告、艺术创作等）"""

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
        
        return f"""为以下图像生成提示词生成对应的负面提示词（negative prompt）：

正面提示词: {positive_prompt}
图像类型: {image_type}

参考负面提示词库：
{combined_negative}

请基于以上参考，为这个特定的图像生成一个全面的负面提示词列表，用逗号分隔。
如果图像类型是 {image_type}，请特别关注该类型的常见问题。"""

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
        return f"""为以下需求制定批量图像生成计划：

主题系列: {theme}
生成数量: {count} 张
用途: {purpose}

请为每张图像生成：
1. 唯一的提示词（保持主题一致但各有特色）
2. 推荐的尺寸
3. 风格变体建议

主题: {theme}
数量: {count} 张
用途: {purpose}
风格要求: {style_requirement}"""

    logger.info("已注册 5 个 Prompt 模板，可在 MCP Inspector 的 Prompts 标签页中查看")

