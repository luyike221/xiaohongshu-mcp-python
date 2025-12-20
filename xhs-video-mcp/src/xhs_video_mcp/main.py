"""MCP 服务主入口"""
import sys
from typing import Optional
from loguru import logger

# 配置日志格式，确保错误信息可见（在导入其他模块之前）
logger.remove()  # 移除默认处理器
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

from fastmcp import FastMCP
from .config import settings
from .models.schema import VideoParams, VideoAspect, VideoConcatMode, VideoTransitionMode
from .services.video_generation_service import VideoGenerationService

# 创建 MCP 应用实例
mcp = FastMCP("XHS Video MCP")

# 创建视频生成服务实例
video_service = VideoGenerationService()


@mcp.tool()
async def generate_video(
    video_subject: str,
    video_script: Optional[str] = None,
    video_aspect: str = "9:16",
    voice_name: str = "zh-CN-XiaoxiaoNeural-Female",
    video_source: str = "pexels",
    subtitle_enabled: bool = True,
    bgm_type: str = "random",
    video_clip_duration: int = 5,
    video_count: int = 1,
    video_concat_mode: str = "random",
    video_transition_mode: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    生成剪辑风格的视频
    
    根据视频主题生成完整的视频，包括：
    1. 自动生成视频脚本（如果未提供）
    2. 生成搜索关键词
    3. 使用TTS生成音频
    4. 生成字幕
    5. 从Pexels/Pixabay下载视频素材
    6. 合成最终视频（添加字幕、背景音乐、转场效果）
    
    Args:
        video_subject: 视频主题，例如"春天的花海"、"如何在家做拿铁"等（必需）
        video_script: 视频脚本（可选，如果不提供会自动生成）
        video_aspect: 视频比例，"9:16"（竖屏）或 "16:9"（横屏），默认 "9:16"
        voice_name: 语音名称，默认 "zh-CN-XiaoxiaoNeural-Female"
        video_source: 素材来源，"pexels" 或 "pixabay"，默认 "pexels"
        subtitle_enabled: 是否启用字幕，默认 True
        bgm_type: 背景音乐类型，"random" 或 "none"，默认 "random"
        video_clip_duration: 视频片段最大时长（秒），默认 5
        video_count: 生成视频数量，默认 1
        video_concat_mode: 视频拼接模式，"random" 或 "sequential"，默认 "random"
        video_transition_mode: 视频转场模式，"none"、"fade_in"、"fade_out"、"slide_in"、"slide_out"、"shuffle"，默认 None
        output_dir: 输出目录（可选，默认使用配置中的输出目录）
    
    Returns:
        包含生成结果的字典：
        - success (bool): 是否成功
        - video_path (str): 生成的视频文件路径
        - audio_path (str): 音频文件路径
        - subtitle_path (str): 字幕文件路径（如果生成）
        - script (str): 生成的脚本
        - terms (list): 生成的关键词列表
        - combined_video_path (str): 合成视频路径（未添加字幕）
        - error (str): 错误信息（如果失败）
    
    Example:
        ```python
        result = await generate_video(
            video_subject="春天的花海",
            video_aspect="9:16",
            voice_name="zh-CN-XiaoxiaoNeural-Female"
        )
        ```
    """
    try:
        logger.info(f"Generating video for subject: {video_subject}")
        
        # 构建视频参数
        params = VideoParams(
            video_subject=video_subject,
            video_script=video_script,
            video_aspect=VideoAspect(video_aspect),
            voice_name=voice_name,
            video_source=video_source,
            subtitle_enabled=subtitle_enabled,
            bgm_type=bgm_type,
            video_clip_duration=video_clip_duration,
            video_count=video_count,
            video_concat_mode=VideoConcatMode(video_concat_mode),
            video_transition_mode=VideoTransitionMode(video_transition_mode) if video_transition_mode else None,
        )
        
        # 生成视频（异步方法）
        result = await video_service.generate(
            params=params,
            output_dir=output_dir,
        )
        
        if result["success"]:
            logger.success(f"Video generated successfully: {result['video_path']}")
        else:
            logger.error(f"Video generation failed: {result.get('error')}")
        
        return result
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Video generation error: {e}")
        logger.error(f"Error traceback:\n{error_detail}")
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_detail
        }


def main():
    """启动 MCP 服务器"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(
        description="小红书视频生成 MCP 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "8005")),
        help="MCP 服务器端口 (默认: 8005)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("MCP_HOST", "0.0.0.0"),
        help="MCP 服务器主机 (默认: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("小红书视频生成 MCP 服务启动")
    logger.info(f"服务器地址: http://{args.host}:{args.port}")
    logger.info("=" * 60)
    
    # 启动 FastMCP HTTP 服务器
    mcp.run(transport="http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()

