"""视频服务 - 合成视频"""
import os
import random
import shutil
import itertools
import gc
from typing import List
from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    afx,
    concatenate_videoclips,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import ImageFont

from ..config import settings
from ..models.schema import VideoAspect, VideoConcatMode, VideoTransitionMode, VideoParams
from ..utils.video_effects import (
    fadein_transition,
    fadeout_transition,
    slidein_transition,
    slideout_transition,
)


class SubClippedVideoClip:
    """子剪辑信息"""
    def __init__(self, file_path, start_time=None, end_time=None, width=None, height=None, duration=None):
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.width = width
        self.height = height
        if duration is None:
            self.duration = end_time - start_time if start_time and end_time else 0
        else:
            self.duration = duration


class VideoService:
    """视频服务，用于合成视频"""
    
    def __init__(self):
        self.audio_codec = "aac"
        self.fps = settings.video_fps
        # 根据配置选择视频编码器
        self.video_codec = self._get_video_codec()
        # 输出设备信息
        self._log_device_info()
    
    def _get_video_codec(self) -> str:
        """获取视频编码器"""
        codec = settings.video_codec.lower()
        
        # 如果设置为 auto，自动检测
        if codec == "auto":
            if settings.video_gpu_acceleration:
                # 检查是否有 NVENC 支持
                if self._check_nvenc_support():
                    logger.info("GPU acceleration enabled, using h264_nvenc")
                    return "h264_nvenc"
                else:
                    logger.warning("GPU acceleration requested but NVENC not available, falling back to libx264")
                    return "libx264"
            else:
                return "libx264"
        
        # 用户指定编码器
        if codec in ["libx264", "h264_nvenc", "hevc_nvenc"]:
            if codec in ["h264_nvenc", "hevc_nvenc"] and not self._check_nvenc_support():
                logger.warning(f"{codec} not available, falling back to libx264")
                return "libx264"
            return codec
        
        logger.warning(f"Unknown codec {codec}, using libx264")
        return "libx264"
    
    def _check_nvenc_support(self) -> bool:
        """检查系统是否支持 NVENC 硬件编码"""
        try:
            import subprocess
            # 检查 FFmpeg 是否支持 h264_nvenc
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "h264_nvenc" in result.stdout:
                logger.info("NVENC hardware encoder detected")
                return True
        except Exception as e:
            logger.debug(f"Failed to check NVENC support: {e}")
        return False
    
    def _log_device_info(self):
        """输出设备信息日志"""
        device_type = "GPU (NVENC)" if self.video_codec in ["h264_nvenc", "hevc_nvenc"] else "CPU"
        logger.info(f"📹 Video encoding device: {device_type} (codec: {self.video_codec})")
        
        # 检查 CUDA 是否可用（用于其他可能的 GPU 加速）
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
                logger.info(f"🎮 CUDA available: {gpu_count} GPU(s) - {gpu_name}")
            else:
                logger.info("🎮 CUDA not available (using CPU)")
        except ImportError:
            logger.debug("PyTorch not installed, cannot check CUDA availability")
        except Exception as e:
            logger.debug(f"Failed to check CUDA: {e}")
    
    def close_clip(self, clip):
        """关闭视频剪辑，释放资源"""
        if clip is None:
            return
        
        try:
            if hasattr(clip, 'reader') and clip.reader is not None:
                clip.reader.close()
            
            if hasattr(clip, 'audio') and clip.audio is not None:
                if hasattr(clip.audio, 'reader') and clip.audio.reader is not None:
                    clip.audio.reader.close()
                del clip.audio
            
            if hasattr(clip, 'mask') and clip.mask is not None:
                if hasattr(clip.mask, 'reader') and clip.mask.reader is not None:
                    clip.mask.reader.close()
                del clip.mask
            
            if hasattr(clip, 'clips') and clip.clips:
                for child_clip in clip.clips:
                    if child_clip is not clip:
                        self.close_clip(child_clip)
                clip.clips = []
        
        except Exception as e:
            logger.error(f"Failed to close clip: {e}")
        
        del clip
        gc.collect()
    
    def _delete_files(self, files: List[str] | str):
        """删除文件"""
        if isinstance(files, str):
            files = [files]
        
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
    
    def _get_bgm_file(self, bgm_type: str = "random", bgm_file: str = "") -> str:
        """获取背景音乐文件"""
        if not bgm_type:
            return ""
        
        if bgm_file and os.path.exists(bgm_file):
            return bgm_file
        
        # 如果没有指定bgm文件，返回空（可以后续扩展）
        return ""
    
    def combine_videos(
        self,
        combined_video_path: str,
        video_paths: List[str],
        audio_file: str,
        video_aspect: VideoAspect = VideoAspect.portrait,
        video_concat_mode: VideoConcatMode = VideoConcatMode.random,
        video_transition_mode: VideoTransitionMode = None,
        max_clip_duration: int = 5,
        threads: int = 2,
    ) -> str:
        """
        拼接视频片段
        
        Args:
            combined_video_path: 输出视频路径
            video_paths: 输入视频路径列表
            audio_file: 音频文件路径
            video_aspect: 视频比例
            video_concat_mode: 拼接模式
            video_transition_mode: 转场模式
            max_clip_duration: 最大片段时长
            threads: 线程数
            
        Returns:
            合成的视频路径
        """
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration
        audio_clip.close()
        
        logger.info(f"Audio duration: {audio_duration} seconds")
        logger.info(f"Maximum clip duration: {max_clip_duration} seconds")
        
        output_dir = os.path.dirname(combined_video_path)
        os.makedirs(output_dir, exist_ok=True)
        
        aspect = VideoAspect(video_aspect)
        video_width, video_height = aspect.to_resolution()
        
        processed_clips = []
        subclipped_items = []
        video_duration = 0
        
        # 将视频分割成片段
        for video_path in video_paths:
            clip = VideoFileClip(video_path)
            clip_duration = clip.duration
            clip_w, clip_h = clip.size
            self.close_clip(clip)
            
            start_time = 0
            while start_time < clip_duration:
                end_time = min(start_time + max_clip_duration, clip_duration)
                if clip_duration - start_time >= max_clip_duration:
                    subclipped_items.append(SubClippedVideoClip(
                        file_path=video_path,
                        start_time=start_time,
                        end_time=end_time,
                        width=clip_w,
                        height=clip_h
                    ))
                start_time = end_time
                if video_concat_mode == VideoConcatMode.sequential:
                    break
        
        # 随机打乱（如果需要）
        if video_concat_mode == VideoConcatMode.random:
            random.shuffle(subclipped_items)
        
        logger.debug(f"Total subclipped items: {len(subclipped_items)}")
        
        # 处理每个片段
        for i, subclipped_item in enumerate(subclipped_items):
            if video_duration > audio_duration:
                break
            
            logger.debug(
                f"Processing clip {i+1}: {subclipped_item.width}x{subclipped_item.height}, "
                f"current duration: {video_duration:.2f}s, "
                f"remaining: {audio_duration - video_duration:.2f}s"
            )
            
            try:
                clip = VideoFileClip(subclipped_item.file_path).subclipped(
                    subclipped_item.start_time,
                    subclipped_item.end_time
                )
                clip_duration = clip.duration
                clip_w, clip_h = clip.size
                
                # 调整尺寸
                if clip_w != video_width or clip_h != video_height:
                    clip_ratio = clip.w / clip.h
                    video_ratio = video_width / video_height
                    
                    if clip_ratio == video_ratio:
                        clip = clip.resized(new_size=(video_width, video_height))
                    else:
                        if clip_ratio > video_ratio:
                            scale_factor = video_width / clip_w
                        else:
                            scale_factor = video_height / clip_h
                        
                        new_width = int(clip_w * scale_factor)
                        new_height = int(clip_h * scale_factor)
                        
                        background = ColorClip(
                            size=(video_width, video_height),
                            color=(0, 0, 0)
                        ).with_duration(clip_duration)
                        clip_resized = clip.resized(new_size=(new_width, new_height)).with_position("center")
                        clip = CompositeVideoClip([background, clip_resized])
                
                # 应用转场效果
                if video_transition_mode:
                    shuffle_side = random.choice(["left", "right", "top", "bottom"])
                    if video_transition_mode == VideoTransitionMode.fade_in:
                        clip = fadein_transition(clip, 1)
                    elif video_transition_mode == VideoTransitionMode.fade_out:
                        clip = fadeout_transition(clip, 1)
                    elif video_transition_mode == VideoTransitionMode.slide_in:
                        clip = slidein_transition(clip, 1, shuffle_side)
                    elif video_transition_mode == VideoTransitionMode.slide_out:
                        clip = slideout_transition(clip, 1, shuffle_side)
                    elif video_transition_mode == VideoTransitionMode.shuffle:
                        transition_funcs = [
                            lambda c: fadein_transition(c, 1),
                            lambda c: fadeout_transition(c, 1),
                            lambda c: slidein_transition(c, 1, shuffle_side),
                            lambda c: slideout_transition(c, 1, shuffle_side),
                        ]
                        shuffle_transition = random.choice(transition_funcs)
                        clip = shuffle_transition(clip)
                
                if clip.duration > max_clip_duration:
                    clip = clip.subclipped(0, max_clip_duration)
                
                # 写入临时文件
                clip_file = os.path.join(output_dir, f"temp-clip-{i+1}.mp4")
                clip.write_videofile(
                    clip_file,
                    logger=None,
                    fps=self.fps,
                    codec=self.video_codec
                )
                self.close_clip(clip)
                
                processed_clips.append(SubClippedVideoClip(
                    file_path=clip_file,
                    duration=clip.duration,
                    width=clip_w,
                    height=clip_h
                ))
                video_duration += clip.duration
            
            except Exception as e:
                logger.error(f"Failed to process clip: {e}")
        
        # 如果视频时长不够，循环片段
        if video_duration < audio_duration:
            logger.warning(
                f"Video duration ({video_duration:.2f}s) is shorter than audio duration "
                f"({audio_duration:.2f}s), looping clips"
            )
            base_clips = processed_clips.copy()
            for clip in itertools.cycle(base_clips):
                if video_duration >= audio_duration:
                    break
                processed_clips.append(clip)
                video_duration += clip.duration
        
        # 合并视频片段
        logger.info("Starting clip merging process")
        if not processed_clips:
            logger.warning("No clips available for merging")
            return combined_video_path
        
        if len(processed_clips) == 1:
            logger.info("Using single clip directly")
            shutil.copy(processed_clips[0].file_path, combined_video_path)
            self._delete_files([processed_clips[0].file_path])
            return combined_video_path
        
        # 逐步合并视频
        base_clip_path = processed_clips[0].file_path
        temp_merged_video = os.path.join(output_dir, "temp-merged-video.mp4")
        temp_merged_next = os.path.join(output_dir, "temp-merged-next.mp4")
        
        shutil.copy(base_clip_path, temp_merged_video)
        
        for i, clip in enumerate(processed_clips[1:], 1):
            logger.info(f"Merging clip {i}/{len(processed_clips)-1}, duration: {clip.duration:.2f}s")
            
            try:
                base_clip = VideoFileClip(temp_merged_video)
                next_clip = VideoFileClip(clip.file_path)
                
                merged_clip = concatenate_videoclips([base_clip, next_clip])
                
                # 准备编码参数
                codec_params = {}
                if self.video_codec == "h264_nvenc":
                    # NVENC 编码参数优化
                    codec_params = {
                        "codec": self.video_codec,
                        "preset": "fast",  # fast, medium, slow
                        "crf": 23,  # 质量控制，18-28 之间
                    }
                elif self.video_codec == "hevc_nvenc":
                    codec_params = {
                        "codec": self.video_codec,
                        "preset": "fast",
                        "crf": 23,
                    }
                else:
                    codec_params = {
                        "codec": self.video_codec,
                        "preset": "medium",
                    }
                
                merged_clip.write_videofile(
                    filename=temp_merged_next,
                    threads=threads,
                    logger=None,
                    temp_audiofile_path=output_dir,
                    audio_codec=self.audio_codec,
                    fps=self.fps,
                    **codec_params
                )
                self.close_clip(base_clip)
                self.close_clip(next_clip)
                self.close_clip(merged_clip)
                
                self._delete_files(temp_merged_video)
                os.rename(temp_merged_next, temp_merged_video)
            
            except Exception as e:
                logger.error(f"Failed to merge clip: {e}")
                continue
        
        os.rename(temp_merged_video, combined_video_path)
        
        # 清理临时文件
        clip_files = [clip.file_path for clip in processed_clips]
        self._delete_files(clip_files)
        
        logger.info("Video combining completed")
        return combined_video_path
    
    def _find_font_file(self, font_name: str) -> str:
        """
        查找字体文件
        
        Args:
            font_name: 字体文件名或路径
            
        Returns:
            字体文件路径，如果找不到则返回 None
        """
        if not font_name:
            font_name = "STHeitiMedium.ttc"
        
        # 如果已经是完整路径且存在，直接返回
        if os.path.isabs(font_name) and os.path.exists(font_name):
            return font_name
        
        # 搜索路径列表
        search_paths = [
            # 1. 项目资源目录
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "resource", "fonts", font_name),
            # 2. 当前工作目录的 resource/fonts
            os.path.join(os.getcwd(), "resource", "fonts", font_name),
            # 3. 系统字体目录（Linux）
            f"/usr/share/fonts/{font_name}",
            f"/usr/local/share/fonts/{font_name}",
            # 4. macOS 字体目录
            f"/System/Library/Fonts/{font_name}",
            f"/Library/Fonts/{font_name}",
            f"~/Library/Fonts/{font_name}",
            # 5. Windows 字体目录
            f"C:/Windows/Fonts/{font_name}",
            # 6. 直接使用字体名（MoviePy 可能会自动查找）
            font_name,
        ]
        
        # 展开用户目录
        search_paths = [os.path.expanduser(path) for path in search_paths]
        
        # 尝试查找字体文件
        for path in search_paths:
            if os.path.exists(path):
                logger.debug(f"Found font file: {path}")
                return path
        
        # 如果找不到，尝试使用系统默认字体
        logger.warning(f"Font file not found: {font_name}, trying to use system default")
        
        # 尝试常见的系统字体
        system_fonts = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:/Windows/Fonts/arial.ttf",  # Windows
        ]
        
        for sys_font in system_fonts:
            sys_font = os.path.expanduser(sys_font)
            if os.path.exists(sys_font):
                logger.info(f"Using system font: {sys_font}")
                return sys_font
        
        # 最后尝试：返回字体名，让 MoviePy 自己处理
        logger.warning(f"Could not find font file, using font name directly: {font_name}")
        return font_name
    
    def _wrap_text(self, text: str, max_width: int, font_path: str, fontsize: int = 60):
        """文本换行"""
        font = None
        if font_path:
            try:
                # 尝试加载字体
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, fontsize)
                else:
                    # 如果路径不存在，尝试直接使用字体名
                    try:
                        font = ImageFont.truetype(font_path, fontsize)
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Failed to load font {font_path}: {e}")
        
        # 如果字体加载失败，使用默认字体
        if font is None:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        def get_text_size(inner_text):
            inner_text = inner_text.strip()
            if font:
                try:
                    left, top, right, bottom = font.getbbox(inner_text)
                    return right - left, bottom - top
                except:
                    pass
            # 简单估算
            return len(inner_text) * fontsize // 2, fontsize
        
        width, height = get_text_size(text)
        if width <= max_width:
            return text, height
        
        words = text.split(" ")
        wrapped_lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_width, _ = get_text_size(test_line)
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word
        
        if current_line:
            wrapped_lines.append(current_line)
        
        result = "\n".join(wrapped_lines)
        height = len(wrapped_lines) * height
        return result, height
    
    def generate_video(
        self,
        video_path: str,
        audio_path: str,
        subtitle_path: str,
        output_file: str,
        params: VideoParams,
    ):
        """
        生成最终视频（添加字幕和背景音乐）
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            subtitle_path: 字幕文件路径
            output_file: 输出文件路径
            params: 视频参数
        """
        aspect = VideoAspect(params.video_aspect)
        video_width, video_height = aspect.to_resolution()
        
        logger.info(f"Generating video: {video_width}x{video_height}")
        logger.info(f"Video: {video_path}")
        logger.info(f"Audio: {audio_path}")
        logger.info(f"Subtitle: {subtitle_path}")
        logger.info(f"Output: {output_file}")
        
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # 字体路径查找和验证
        font_path = self._find_font_file(params.font_name) if params.subtitle_enabled else None
        if params.subtitle_enabled:
            logger.info(f"Font: {font_path}")
        
        def create_text_clip(subtitle_item):
            """创建字幕剪辑"""
            phrase = subtitle_item[1]
            max_width = video_width * 0.9
            wrapped_txt, txt_height = self._wrap_text(
                phrase,
                max_width=int(max_width),
                font_path=font_path,
                fontsize=params.font_size
            )
            
            # 安全地创建 TextClip
            try:
                _clip = TextClip(
                    text=wrapped_txt,
                    font=font_path,
                    font_size=params.font_size,
                    color=params.text_fore_color,
                    bg_color=params.text_background_color,
                    stroke_color=params.stroke_color,
                    stroke_width=params.stroke_width,
                )
            except ValueError as e:
                # 如果字体失败，尝试不使用字体参数
                logger.warning(f"Failed to create TextClip with font {font_path}: {e}, trying without font")
                try:
                    _clip = TextClip(
                        text=wrapped_txt,
                        font_size=params.font_size,
                        color=params.text_fore_color,
                        bg_color=params.text_background_color,
                        stroke_color=params.stroke_color,
                        stroke_width=params.stroke_width,
                    )
                except Exception as e2:
                    logger.error(f"Failed to create TextClip: {e2}, using minimal settings")
                    _clip = TextClip(
                        text=wrapped_txt,
                        font_size=params.font_size,
                    )
            duration = subtitle_item[0][1] - subtitle_item[0][0]
            _clip = _clip.with_start(subtitle_item[0][0])
            _clip = _clip.with_end(subtitle_item[0][1])
            _clip = _clip.with_duration(duration)
            
            # 设置字幕位置
            if params.subtitle_position == "bottom":
                _clip = _clip.with_position(("center", video_height * 0.95 - _clip.h))
            elif params.subtitle_position == "top":
                _clip = _clip.with_position(("center", video_height * 0.05))
            elif params.subtitle_position == "center":
                _clip = _clip.with_position(("center", "center"))
            else:  # custom
                margin = 10
                max_y = video_height - _clip.h - margin
                min_y = margin
                custom_y = (video_height - _clip.h) * (params.custom_position / 100)
                custom_y = max(min_y, min(custom_y, max_y))
                _clip = _clip.with_position(("center", custom_y))
            
            return _clip
        
        # 加载视频和音频
        video_clip = VideoFileClip(video_path).without_audio()
        audio_clip = AudioFileClip(audio_path).with_effects(
            [afx.MultiplyVolume(params.voice_volume)]
        )
        
        # 添加字幕
        if subtitle_path and os.path.exists(subtitle_path) and params.subtitle_enabled:
            def make_textclip(text):
                # 安全地创建 TextClip，处理字体错误
                try:
                    return TextClip(
                        text=text,
                        font=font_path,
                        font_size=params.font_size,
                    )
                except ValueError as e:
                    # 如果字体失败，尝试不使用字体参数
                    logger.warning(f"Failed to create TextClip with font {font_path}: {e}, trying without font")
                    try:
                        return TextClip(
                            text=text,
                            font_size=params.font_size,
                        )
                    except Exception as e2:
                        logger.error(f"Failed to create TextClip: {e2}")
                        # 最后尝试使用默认设置
                        return TextClip(text=text)
            
            sub = SubtitlesClip(
                subtitles=subtitle_path,
                encoding="utf-8",
                make_textclip=make_textclip
            )
            text_clips = []
            for item in sub.subtitles:
                clip = create_text_clip(subtitle_item=item)
                text_clips.append(clip)
            video_clip = CompositeVideoClip([video_clip, *text_clips])
        
        # 添加背景音乐
        bgm_file = self._get_bgm_file(bgm_type=params.bgm_type, bgm_file=params.bgm_file or "")
        if bgm_file:
            try:
                bgm_clip = AudioFileClip(bgm_file).with_effects([
                    afx.MultiplyVolume(params.bgm_volume),
                    afx.AudioFadeOut(3),
                    afx.AudioLoop(duration=video_clip.duration),
                ])
                audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
            except Exception as e:
                logger.error(f"Failed to add BGM: {e}")
        
        # 合成最终视频
        video_clip = video_clip.with_audio(audio_clip)
        
        # 准备编码参数
        codec_params = {}
        if self.video_codec == "h264_nvenc":
            # NVENC 编码参数优化
            codec_params = {
                "codec": self.video_codec,
                "preset": "fast",  # fast, medium, slow
                "crf": 23,  # 质量控制，18-28 之间
            }
        elif self.video_codec == "hevc_nvenc":
            codec_params = {
                "codec": self.video_codec,
                "preset": "fast",
                "crf": 23,
            }
        else:
            codec_params = {
                "codec": self.video_codec,
                "preset": "medium",
            }
        
        video_clip.write_videofile(
            output_file,
            audio_codec=self.audio_codec,
            temp_audiofile_path=output_dir,
            threads=params.n_threads or 2,
            logger=None,
            fps=self.fps,
            **codec_params
        )
        video_clip.close()
        self.close_clip(video_clip)
        
        logger.success(f"Final video generated: {output_file}")

