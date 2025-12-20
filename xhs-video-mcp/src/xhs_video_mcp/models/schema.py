"""数据模型定义"""
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel


class VideoConcatMode(str, Enum):
    """视频拼接模式"""
    random = "random"
    sequential = "sequential"


class VideoTransitionMode(str, Enum):
    """视频转场模式"""
    none = "none"
    shuffle = "shuffle"
    fade_in = "fade_in"
    fade_out = "fade_out"
    slide_in = "slide_in"
    slide_out = "slide_out"


class VideoAspect(str, Enum):
    """视频比例"""
    landscape = "16:9"  # 横屏
    portrait = "9:16"   # 竖屏
    square = "1:1"      # 正方形
    
    def to_resolution(self) -> tuple[int, int]:
        """转换为分辨率"""
        if self == VideoAspect.landscape:
            return 1920, 1080
        elif self == VideoAspect.portrait:
            return 1080, 1920
        elif self == VideoAspect.square:
            return 1080, 1080
        return 1080, 1920


class MaterialInfo(BaseModel):
    """素材信息"""
    provider: str = "pexels"
    url: str = ""
    duration: int = 0


class VideoParams(BaseModel):
    """视频生成参数"""
    video_subject: str
    video_script: Optional[str] = None
    video_terms: Optional[Union[str, List[str]]] = None
    video_aspect: VideoAspect = VideoAspect.portrait
    video_concat_mode: VideoConcatMode = VideoConcatMode.random
    video_transition_mode: Optional[VideoTransitionMode] = None
    video_clip_duration: int = 5
    video_count: int = 1
    video_source: str = "pexels"
    video_materials: Optional[List[MaterialInfo]] = None
    custom_audio_file: Optional[str] = None
    video_language: Optional[str] = ""
    voice_name: str = "zh-CN-XiaoxiaoNeural-Female"
    voice_volume: float = 1.0
    voice_rate: float = 1.0
    bgm_type: str = "random"
    bgm_file: Optional[str] = None
    bgm_volume: float = 0.2
    subtitle_enabled: bool = True
    subtitle_position: str = "bottom"  # top, bottom, center
    custom_position: float = 70.0
    font_name: str = "STHeitiMedium.ttc"
    text_fore_color: str = "#FFFFFF"
    text_background_color: Union[bool, str] = True
    font_size: int = 60
    stroke_color: str = "#000000"
    stroke_width: float = 1.5
    n_threads: int = 2
    paragraph_number: int = 1

