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
        return f"""请生成一张小红书风格的图文内容图片。
【合规特别注意的】注意不要带有任何小红书的logo，不要有右下角的用户id以及logo
【合规特别注意的】用户给到的参考图片里如果有水印和logo（尤其是注意右下角，左上角），请一定要去掉

页面内容：
{page_content}

页面类型：{page_type}

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

    logger.info("已注册 6 个 Prompt 模板，可在 MCP Inspector 的 Prompts 标签页中查看")

