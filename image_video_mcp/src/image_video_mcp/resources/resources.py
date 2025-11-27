"""
MCP Resource 资源定义

这些资源可以在 MCP Inspector 的 Resources 标签页中查看和使用
资源用于提供外部数据，可以在 Prompt 或 Tool 中引用
"""

from loguru import logger

# ========== 数据定义（模块级别，供 Resource Template 使用）==========

# 1. 图像风格预设资源
IMAGE_STYLES = {
    "realistic": {
        "name": "写实风格",
        "description": "真实、自然、细节丰富的写实风格",
        "keywords": "realistic, photorealistic, detailed, natural, high quality, 8k, sharp focus",
        "negative_keywords": "cartoon, anime, illustration, painting, abstract"
    },
    "anime": {
        "name": "动漫风格",
        "description": "日式动漫、二次元风格",
        "keywords": "anime, manga, japanese style, 2d, colorful, vibrant",
        "negative_keywords": "realistic, photorealistic, 3d, western"
    },
    "watercolor": {
        "name": "水彩风格",
        "description": "柔和、透明的水彩画风格",
        "keywords": "watercolor, soft, transparent, flowing, artistic, gentle",
        "negative_keywords": "sharp, detailed, photorealistic, digital"
    },
    "oil_painting": {
        "name": "油画风格",
        "description": "经典油画、厚重质感",
        "keywords": "oil painting, classical, rich texture, brush strokes, artistic",
        "negative_keywords": "digital, flat, simple, minimal"
    },
    "3d_render": {
        "name": "3D渲染风格",
        "description": "3D建模渲染、立体感强",
        "keywords": "3d render, cgi, 3d model, rendered, professional, studio lighting",
        "negative_keywords": "2d, flat, illustration, painting"
    },
    "sketch": {
        "name": "素描风格",
        "description": "铅笔素描、线条艺术",
        "keywords": "sketch, pencil drawing, line art, black and white, artistic",
        "negative_keywords": "colorful, detailed, photorealistic, digital"
    }
}

# 2. 常用负面提示词库
NEGATIVE_PROMPTS = {
    "general": "low resolution, blurry, distorted, low quality, worst quality, bad quality, jpeg artifacts, watermark, text, signature, username, error, cropped, out of frame, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
    "portrait": "bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, distorted face, blurry face, bad eyes, asymmetric eyes, bad eyebrows, bad nose, bad mouth, bad lips, bad teeth",
    "landscape": "bad composition, cluttered, messy, distorted perspective, bad lighting, overexposed, underexposed, blurry, low resolution, artifacts",
    "product": "bad lighting, shadows, reflections, distortion, blurry, low quality, background clutter, watermark, text"
}

# 3. 图像尺寸预设
IMAGE_SIZES = {
    "square_1k": {"width": 1024, "height": 1024, "name": "正方形 1K", "ratio": "1:1"},
    "square_2k": {"width": 2048, "height": 2048, "name": "正方形 2K", "ratio": "1:1"},
    "portrait_16_9": {"width": 1920, "height": 1080, "name": "横屏 16:9", "ratio": "16:9"},
    "portrait_9_16": {"width": 1080, "height": 1920, "name": "竖屏 9:16", "ratio": "9:16"},
    "portrait_4_3": {"width": 1600, "height": 1200, "name": "横屏 4:3", "ratio": "4:3"},
    "portrait_3_4": {"width": 1200, "height": 1600, "name": "竖屏 3:4", "ratio": "3:4"},
    "wide_21_9": {"width": 2560, "height": 1080, "name": "超宽屏 21:9", "ratio": "21:9"},
    "standard_1280": {"width": 1280, "height": 1280, "name": "标准 1280x1280", "ratio": "1:1"}
}

# 4. 视频风格预设
VIDEO_STYLES = {
    "cinematic": {
        "name": "电影感",
        "description": "电影级质感，专业镜头语言",
        "keywords": "cinematic, film grain, professional cinematography, dramatic lighting, shallow depth of field",
        "camera_movements": ["slow push", "dolly shot", "tracking shot", "crane shot"]
    },
    "documentary": {
        "name": "纪录片风格",
        "description": "自然、真实、纪实风格",
        "keywords": "documentary style, natural lighting, handheld camera, authentic, real",
        "camera_movements": ["handheld", "natural movement", "following shot"]
    },
    "commercial": {
        "name": "商业广告",
        "description": "商业广告、产品展示",
        "keywords": "commercial, professional, clean, bright, high quality, product showcase",
        "camera_movements": ["smooth rotation", "zoom in", "reveal shot"]
    },
    "vlog": {
        "name": "Vlog风格",
        "description": "日常Vlog、轻松自然",
        "keywords": "vlog style, casual, natural, everyday, authentic, personal",
        "camera_movements": ["handheld", "selfie angle", "walking shot"]
    },
    "timelapse": {
        "name": "延时摄影",
        "description": "延时、快进效果",
        "keywords": "timelapse, fast motion, time compression, dynamic",
        "camera_movements": ["fixed position", "slow pan", "wide angle"]
    }
}

# 5. 生成配置模板
GENERATION_CONFIGS = {
    "high_quality": {
        "name": "高质量配置",
        "description": "适合高质量图像生成",
        "width": 2048,
        "height": 2048,
        "negative_prompt": "low resolution, blurry, distorted, low quality, worst quality",
        "quality_tags": "masterpiece, best quality, ultra detailed, 8k, hdr"
    },
    "fast_generation": {
        "name": "快速生成配置",
        "description": "适合快速预览和测试",
        "width": 1024,
        "height": 1024,
        "negative_prompt": "low quality, blurry",
        "quality_tags": "high quality, detailed"
    },
    "social_media": {
        "name": "社交媒体配置",
        "description": "适合社交媒体发布",
        "width": 1080,
        "height": 1080,
        "negative_prompt": "watermark, text, signature, username, low quality",
        "quality_tags": "high quality, vibrant, eye-catching, social media ready"
    },
    "artistic": {
        "name": "艺术创作配置",
        "description": "适合艺术创作和展示",
        "width": 1920,
        "height": 1920,
        "negative_prompt": "photorealistic, realistic, photo",
        "quality_tags": "artistic, creative, unique, masterpiece, gallery quality"
    }
}

# 6. 常用提示词模板库
PROMPT_TEMPLATES = {
    "portrait": "{subject}, {style}, {lighting}, {composition}, {quality}",
    "landscape": "{scene}, {time_of_day}, {weather}, {mood}, {style}, {quality}",
    "product": "{product}, {background}, {lighting}, {angle}, {style}, {quality}",
    "animal": "{animal}, {pose}, {environment}, {style}, {lighting}, {quality}",
    "abstract": "{concept}, {colors}, {style}, {composition}, {mood}, {quality}"
}

# ========== Resource 注册函数 ==========

def register_resources(mcp):
    """
    注册所有 Resource 到 FastMCP 实例
    
    Args:
        mcp: FastMCP 实例
    """
    
    # 使用 @mcp.resource() 装饰器注册资源
    # URI 格式: resource://资源名称
    @mcp.resource("resource://image_styles")
    def get_image_styles() -> dict:
        """获取图像风格预设"""
        return IMAGE_STYLES
    
    @mcp.resource("resource://negative_prompts")
    def get_negative_prompts() -> dict:
        """获取负面提示词库"""
        return NEGATIVE_PROMPTS
    
    @mcp.resource("resource://image_sizes")
    def get_image_sizes() -> dict:
        """获取图像尺寸预设"""
        return IMAGE_SIZES
    
    @mcp.resource("resource://video_styles")
    def get_video_styles() -> dict:
        """获取视频风格预设"""
        return VIDEO_STYLES
    
    @mcp.resource("resource://generation_configs")
    def get_generation_configs() -> dict:
        """获取生成配置模板"""
        return GENERATION_CONFIGS
    
    @mcp.resource("resource://prompt_templates")
    def get_prompt_templates() -> dict:
        """获取提示词模板库"""
        return PROMPT_TEMPLATES
    
    logger.info("已注册 6 个 Resource 资源，可在 MCP Inspector 的 Resources 标签页中查看")

