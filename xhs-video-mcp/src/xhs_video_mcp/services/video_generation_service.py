"""视频生成主服务 - 编排整个流程"""
import os
import re
import math
from typing import Optional, Dict, Any
from loguru import logger

from ..config import settings
from ..models.schema import VideoParams, VideoAspect, VideoConcatMode
from .llm_service import LLMService
from .voice_service import VoiceService
from .subtitle_service import SubtitleService
from .material_service import MaterialService
from .video_service import VideoService


class VideoGenerationService:
    """视频生成主服务，编排整个生成流程"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.voice_service = VoiceService()
        self.subtitle_service = SubtitleService()
        self.material_service = MaterialService()
        self.video_service = VideoService()
        # 输出整体设备信息摘要
        self._log_summary()
    
    def _log_summary(self):
        """输出设备信息摘要"""
        logger.info("=" * 60)
        logger.info("🔧 Device Configuration Summary")
        logger.info("=" * 60)
        
        # 视频编码设备
        video_device = "GPU (NVENC)" if self.video_service.video_codec in ["h264_nvenc", "hevc_nvenc"] else "CPU"
        logger.info(f"  📹 Video Encoding: {video_device} ({self.video_service.video_codec})")
        
        # 字幕生成设备
        if settings.subtitle_provider.lower() == "whisper":
            subtitle_device = "CUDA" if self.subtitle_service.device == "cuda" else "CPU"
            logger.info(f"  📝 Subtitle Generation: {subtitle_device} (Whisper)")
        else:
            logger.info(f"  📝 Subtitle Generation: CPU (Edge-TTS)")
        
        # TTS 设备（Edge-TTS 使用 CPU）
        logger.info(f"  🎤 TTS Generation: CPU (Edge-TTS)")
        
        logger.info("=" * 60)
    
    async def generate(
        self,
        params: VideoParams,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成视频的完整流程
        
        Args:
            params: 视频生成参数
            output_dir: 输出目录（可选）
            
        Returns:
            生成结果字典，包含：
            - success: 是否成功
            - video_path: 视频文件路径
            - audio_path: 音频文件路径
            - subtitle_path: 字幕文件路径
            - script: 生成的脚本
            - terms: 生成的关键词
            - error: 错误信息（如果失败）
        """
        if output_dir is None:
            output_dir = settings.video_output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 输出当前使用的设备信息
        logger.info("🚀 Starting video generation with current device configuration:")
        video_device = "GPU (NVENC)" if self.video_service.video_codec in ["h264_nvenc", "hevc_nvenc"] else "CPU"
        logger.info(f"   - Video encoding: {video_device}")
        if settings.subtitle_provider.lower() == "whisper":
            subtitle_device = "CUDA" if self.subtitle_service.device == "cuda" else "CPU"
            logger.info(f"   - Subtitle generation: {subtitle_device}")
        else:
            logger.info(f"   - Subtitle generation: CPU (Edge-TTS)")
        
        try:
            # 1. 生成脚本
            logger.info("Step 1: Generating video script")
            video_script = params.video_script
            if not video_script:
                video_script = self.llm_service.generate_script(
                    video_subject=params.video_subject,
                    language=params.video_language or "",
                    paragraph_number=params.paragraph_number,
                )
            
            if not video_script:
                return {
                    "success": False,
                    "error": "Failed to generate video script"
                }
            
            logger.success(f"Script generated, length: {len(video_script)}")
            
            # 2. 生成关键词
            logger.info("Step 2: Generating search terms")
            video_terms = params.video_terms
            if not video_terms and params.video_source != "local":
                video_terms = self.llm_service.generate_terms(
                    video_subject=params.video_subject,
                    video_script=video_script,
                    amount=5,
                )
            
            if video_terms:
                if isinstance(video_terms, str):
                    video_terms = [term.strip() for term in re.split(r"[,，]", video_terms)]
                elif isinstance(video_terms, list):
                    video_terms = [term.strip() for term in video_terms]
            
            logger.success(f"Terms generated: {video_terms}")
            
            # 3. 生成音频
            logger.info("Step 3: Generating audio")
            audio_file = os.path.join(output_dir, "audio.mp3")
            sub_maker = None
            
            if params.custom_audio_file and os.path.exists(params.custom_audio_file):
                audio_file = params.custom_audio_file
                logger.info(f"Using custom audio file: {audio_file}")
            else:
                try:
                    logger.info(f"Generating TTS audio: voice={params.voice_name}, rate={params.voice_rate}")
                    logger.info(f"Audio output file: {audio_file}")
                    logger.info(f"Script length: {len(video_script)} characters")
                    
                    # TTS 现在是异步方法，直接 await
                    sub_maker = await self.voice_service.tts(
                        text=video_script,
                        voice_name=params.voice_name,
                        voice_rate=params.voice_rate,
                        voice_file=audio_file,
                    )
                    
                    if sub_maker is None:
                        error_msg = (
                            f"TTS failed: voice_name={params.voice_name}, "
                            f"voice_rate={params.voice_rate}, "
                            f"script_length={len(video_script)}"
                        )
                        logger.error(error_msg)
                        # 检查音频文件是否生成
                        if os.path.exists(audio_file):
                            file_size = os.path.getsize(audio_file)
                            logger.warning(f"Audio file exists but sub_maker is None, file_size={file_size} bytes")
                        else:
                            logger.error(f"Audio file not created: {audio_file}")
                        
                        return {
                            "success": False,
                            "error": f"Failed to generate audio: {error_msg}",
                            "details": {
                                "voice_name": params.voice_name,
                                "voice_rate": params.voice_rate,
                                "script_length": len(video_script),
                                "audio_file": audio_file,
                                "file_exists": os.path.exists(audio_file),
                            }
                        }
                except Exception as e:
                    error_msg = f"TTS exception: {str(e)}"
                    logger.error(error_msg)
                    import traceback
                    logger.error(traceback.format_exc())
                    return {
                        "success": False,
                        "error": f"Failed to generate audio: {error_msg}",
                        "details": {
                            "exception": str(e),
                            "voice_name": params.voice_name,
                            "voice_rate": params.voice_rate,
                        }
                    }
            
            audio_duration = self.voice_service.get_audio_duration(sub_maker) if sub_maker else 0
            if audio_duration == 0:
                # 尝试从文件获取时长
                try:
                    from moviepy import AudioFileClip
                    with AudioFileClip(audio_file) as clip:
                        audio_duration = clip.duration
                except:
                    return {
                        "success": False,
                        "error": "Failed to get audio duration"
                    }
            
            logger.success(f"Audio generated, duration: {audio_duration:.2f}s")
            
            # 4. 生成字幕
            logger.info("Step 4: Generating subtitle")
            subtitle_path = ""
            
            if params.subtitle_enabled and sub_maker:
                subtitle_path = os.path.join(output_dir, "subtitle.srt")
                
                if settings.subtitle_provider.lower() == "edge":
                    success = self.voice_service.create_subtitle(
                        sub_maker=sub_maker,
                        text=video_script,
                        subtitle_file=subtitle_path
                    )
                    if not success:
                        logger.warning("Edge subtitle generation failed, trying Whisper")
                        if settings.subtitle_provider.lower() == "whisper":
                            self.subtitle_service.create(
                                audio_file=audio_file,
                                subtitle_file=subtitle_path
                            )
                elif settings.subtitle_provider.lower() == "whisper":
                    self.subtitle_service.create(
                        audio_file=audio_file,
                        subtitle_file=subtitle_path
                    )
                
                if os.path.exists(subtitle_path):
                    logger.success(f"Subtitle generated: {subtitle_path}")
                else:
                    logger.warning("Subtitle file not created")
                    subtitle_path = ""
            
            # 5. 获取视频素材
            logger.info("Step 5: Downloading video materials")
            downloaded_videos = []
            
            if params.video_source == "local" and params.video_materials:
                # 使用本地素材
                downloaded_videos = [material.url for material in params.video_materials]
            else:
                # 从网络下载
                if video_terms:
                    downloaded_videos = self.material_service.download_videos(
                        search_terms=video_terms,
                        source=params.video_source,
                        video_aspect=params.video_aspect,
                        video_concat_mode=params.video_concat_mode,
                        audio_duration=audio_duration * params.video_count,
                        max_clip_duration=params.video_clip_duration,
                    )
            
            if not downloaded_videos:
                return {
                    "success": False,
                    "error": "Failed to download video materials"
                }
            
            logger.success(f"Downloaded {len(downloaded_videos)} videos")
            
            # 6. 合成视频
            logger.info("Step 6: Combining videos")
            combined_video_path = os.path.join(output_dir, "combined.mp4")
            
            video_concat_mode = (
                params.video_concat_mode
                if params.video_count == 1
                else VideoConcatMode.random
            )
            
            self.video_service.combine_videos(
                combined_video_path=combined_video_path,
                video_paths=downloaded_videos,
                audio_file=audio_file,
                video_aspect=params.video_aspect,
                video_concat_mode=video_concat_mode,
                video_transition_mode=params.video_transition_mode,
                max_clip_duration=params.video_clip_duration,
                threads=params.n_threads,
            )
            
            logger.success(f"Videos combined: {combined_video_path}")
            
            # 7. 生成最终视频
            logger.info("Step 7: Generating final video")
            final_video_path = os.path.join(output_dir, "final.mp4")
            
            self.video_service.generate_video(
                video_path=combined_video_path,
                audio_path=audio_file,
                subtitle_path=subtitle_path,
                output_file=final_video_path,
                params=params,
            )
            
            logger.success(f"Final video generated: {final_video_path}")
            
            return {
                "success": True,
                "video_path": final_video_path,
                "audio_path": audio_file,
                "subtitle_path": subtitle_path if subtitle_path else None,
                "script": video_script,
                "terms": video_terms if video_terms else [],
                "combined_video_path": combined_video_path,
            }
        
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

