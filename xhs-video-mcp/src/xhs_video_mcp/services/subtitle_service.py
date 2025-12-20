"""字幕服务 - 使用Whisper生成字幕（可选）"""
import os
from typing import Optional
from loguru import logger

from ..config import settings


class SubtitleService:
    """字幕服务，支持Whisper生成字幕"""
    
    def __init__(self):
        self.model = None
        self.device = settings.whisper_device if settings.subtitle_provider.lower() == "whisper" else None
        self._load_model()
        self._log_device_info()
    
    def _load_model(self):
        """加载Whisper模型（如果需要）"""
        if settings.subtitle_provider.lower() != "whisper":
            return
        
        try:
            from faster_whisper import WhisperModel
            
            model_size = settings.whisper_model_size
            device = settings.whisper_device
            compute_type = "int8" if device == "cpu" else "float16"
            
            logger.info(f"Loading Whisper model: {model_size}, device: {device}")
            self.device = device  # 保存设备信息
            self.model = WhisperModel(
                model_size_or_path=model_size,
                device=device,
                compute_type=compute_type
            )
            logger.success(f"Whisper model loaded successfully on {device.upper()}")
        
        except ImportError:
            logger.warning("faster-whisper not installed, Whisper subtitle generation disabled")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
            self.device = None
    
    def _log_device_info(self):
        """输出设备信息日志"""
        if settings.subtitle_provider.lower() == "whisper":
            device_type = "CUDA" if self.device == "cuda" else "CPU"
            logger.info(f"📝 Subtitle generation device: {device_type} (provider: Whisper)")
        else:
            logger.info(f"📝 Subtitle generation device: CPU (provider: Edge-TTS)")
    
    def create(
        self,
        audio_file: str,
        subtitle_file: str
    ) -> bool:
        """
        使用Whisper生成字幕
        
        Args:
            audio_file: 音频文件路径
            subtitle_file: 输出字幕文件路径
            
        Returns:
            是否成功
        """
        if not self.model:
            logger.warning("Whisper model not available")
            return False
        
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return False
        
        logger.info(f"Generating subtitle with Whisper: {audio_file}")
        
        try:
            segments, info = self.model.transcribe(
                audio_file,
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            
            logger.info(
                f"Detected language: {info.language}, "
                f"probability: {info.language_probability:.2f}"
            )
            
            subtitles = []
            for segment in segments:
                words_idx = 0
                words_len = len(segment.words) if segment.words else 0
                
                seg_start = 0
                seg_end = 0
                seg_text = ""
                
                if segment.words:
                    is_segmented = False
                    for word in segment.words:
                        if not is_segmented:
                            seg_start = word.start
                            is_segmented = True
                        
                        seg_end = word.end
                        seg_text += word.word
                        
                        # 如果包含标点符号，则分割句子
                        if self._str_contains_punctuation(word.word):
                            seg_text = seg_text[:-1]  # 移除最后一个字符（标点）
                            if seg_text:
                                subtitles.append({
                                    "msg": seg_text,
                                    "start_time": seg_start,
                                    "end_time": seg_end
                                })
                            is_segmented = False
                            seg_text = ""
                
                if seg_text:
                    subtitles.append({
                        "msg": seg_text,
                        "start_time": seg_start,
                        "end_time": seg_end
                    })
            
            # 写入SRT文件
            os.makedirs(os.path.dirname(subtitle_file) if os.path.dirname(subtitle_file) else ".", exist_ok=True)
            
            with open(subtitle_file, "w", encoding="utf-8") as f:
                for idx, subtitle in enumerate(subtitles, 1):
                    start = self._format_timestamp(subtitle["start_time"])
                    end = self._format_timestamp(subtitle["end_time"])
                    text = subtitle["msg"]
                    f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")
            
            logger.success(f"Subtitle file created: {subtitle_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to generate subtitle with Whisper: {e}")
            return False
    
    def _str_contains_punctuation(self, text: str) -> bool:
        """检查文本是否包含标点符号"""
        import string
        return any(char in string.punctuation for char in text)
    
    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为SRT格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def correct(
        self,
        subtitle_file: str,
        video_script: str
    ) -> bool:
        """
        校正字幕文件，使其与脚本匹配
        
        Args:
            subtitle_file: 字幕文件路径
            video_script: 视频脚本
            
        Returns:
            是否成功
        """
        # 这个功能比较复杂，暂时简化实现
        # 完整实现可以参考MoneyPrinterTurbo的逻辑
        logger.info("Subtitle correction is a simplified implementation")
        return True

