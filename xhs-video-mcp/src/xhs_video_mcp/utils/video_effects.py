"""视频转场效果工具"""
from moviepy import Clip, vfx


def fadein_transition(clip: Clip, duration: float) -> Clip:
    """淡入效果"""
    return clip.with_effects([vfx.FadeIn(duration)])


def fadeout_transition(clip: Clip, duration: float) -> Clip:
    """淡出效果"""
    return clip.with_effects([vfx.FadeOut(duration)])


def slidein_transition(clip: Clip, duration: float, side: str) -> Clip:
    """滑入效果"""
    return clip.with_effects([vfx.SlideIn(duration, side)])


def slideout_transition(clip: Clip, duration: float, side: str) -> Clip:
    """滑出效果"""
    return clip.with_effects([vfx.SlideOut(duration, side)])

