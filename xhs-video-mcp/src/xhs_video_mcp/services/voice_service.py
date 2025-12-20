"""语音服务 - TTS和字幕生成"""
import asyncio
import os
import re
from typing import Optional
from loguru import logger
import edge_tts
from edge_tts import SubMaker

from ..config import settings


class VoiceService:
    """语音服务，用于TTS和字幕生成"""
    
    async def tts(
        self,
        text: str,
        voice_name: str,
        voice_rate: float,
        voice_file: str,
    ) -> Optional[SubMaker]:
        """
        文本转语音（异步方法）
        
        Args:
            text: 要转换的文本
            voice_name: 语音名称（如：zh-CN-XiaoxiaoNeural）
            voice_rate: 语音速率（1.0为正常速度）
            voice_file: 输出音频文件路径
            
        Returns:
            SubMaker对象（用于生成字幕），失败返回None
        """
        # 解析语音名称（移除-Female/-Male后缀）
        voice_name = voice_name.replace("-Female", "").replace("-Male", "").strip()
        
        text = text.strip()
        rate_str = self._convert_rate_to_percent(voice_rate)
        
        logger.info(f"Starting TTS, voice: {voice_name}, rate: {rate_str}")
        
        for i in range(3):  # 重试3次
            try:
                communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
                sub_maker = edge_tts.SubMaker()
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(voice_file) if os.path.dirname(voice_file) else ".", exist_ok=True)
                
                with open(voice_file, "wb") as file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            file.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            sub_maker.create_sub(
                                (chunk["offset"], chunk["duration"]),
                                chunk["text"]
                            )
                
                if not sub_maker:
                    logger.warning(f"TTS attempt {i+1} failed: sub_maker is None")
                    continue
                
                # 检查音频文件是否生成
                if not os.path.exists(voice_file) or os.path.getsize(voice_file) == 0:
                    logger.warning(f"TTS attempt {i+1} failed: audio file not created or empty")
                    continue
                
                # 检查 SubMaker 是否有字幕数据
                # SubMaker 通过 create_sub 方法添加数据后，会有 offset 和 subs 属性
                # 使用 getattr 安全访问属性
                subs_attr = getattr(sub_maker, 'subs', None)
                offset_attr = getattr(sub_maker, 'offset', None)
                
                # 如果音频文件存在，即使没有字幕数据也继续（字幕可以后续生成）
                if subs_attr is None or offset_attr is None or len(subs_attr) == 0 or len(offset_attr) == 0:
                    logger.warning(
                        f"TTS attempt {i+1}: Audio file generated but SubMaker has no subtitle data. "
                        f"File size: {os.path.getsize(voice_file)} bytes. "
                        f"SubMaker attributes: {[attr for attr in dir(sub_maker) if not attr.startswith('_')]}, "
                        f"subs: {len(subs_attr) if subs_attr else 'None'}, "
                        f"offset: {len(offset_attr) if offset_attr else 'None'}"
                    )
                    # 即使没有字幕数据，音频文件已生成，返回 sub_maker
                    logger.info("Continuing with audio file, subtitle can be generated later")
                    return sub_maker
                
                logger.success(f"TTS completed, output: {voice_file}")
                return sub_maker
            
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                logger.error(f"TTS attempt {i+1} failed: {e}")
                logger.debug(f"TTS error details:\n{error_detail}")
                if i == 2:  # 最后一次尝试
                    logger.error(f"All TTS attempts failed. Last error: {e}")
                    return None
        
        return None
    
    def _convert_rate_to_percent(self, rate: float) -> str:
        """将速率转换为百分比字符串"""
        if rate == 1.0:
            return "+0%"
        percent = round((rate - 1.0) * 100)
        if percent > 0:
            return f"+{percent}%"
        else:
            return f"{percent}%"
    
    def create_subtitle(
        self,
        sub_maker: SubMaker,
        text: str,
        subtitle_file: str
    ) -> bool:
        """
        创建字幕文件
        
        Args:
            sub_maker: SubMaker对象
            text: 原始文本
            subtitle_file: 输出字幕文件路径
            
        Returns:
            是否成功
        """
        from edge_tts.submaker import mktimestamp
        from xml.sax.saxutils import unescape
        
        def _format_text(txt: str) -> str:
            """格式化文本"""
            txt = txt.replace("[", " ").replace("]", " ")
            txt = txt.replace("(", " ").replace(")", " ")
            txt = txt.replace("{", " ").replace("}", " ")
            return txt.strip()
        
        def formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
            """格式化字幕条目"""
            start_t = mktimestamp(start_time).replace(".", ",")
            end_t = mktimestamp(end_time).replace(".", ",")
            return f"{idx}\n{start_t} --> {end_t}\n{sub_text}\n"
        
        text = _format_text(text)
        start_time = -1.0
        sub_items = []
        sub_index = 0
        
        # 按标点符号分割脚本
        script_lines = self._split_string_by_punctuations(text)
        
        def match_line(sub_line: str, script_index: int) -> str:
            """匹配字幕行和脚本行"""
            if len(script_lines) <= script_index:
                return ""
            
            script_line = script_lines[script_index]
            if sub_line == script_line:
                return script_line.strip()
            
            # 移除标点符号后比较
            sub_line_clean = re.sub(r"[^\w\s]", "", sub_line)
            script_line_clean = re.sub(r"[^\w\s]", "", script_line)
            if sub_line_clean == script_line_clean:
                return script_line.strip()
            
            return ""
        
        sub_line = ""
        
        try:
            # 安全地获取 offset 和 subs
            # SubMaker 使用 create_sub 方法后，会有 offset 和 subs 属性
            offsets = getattr(sub_maker, 'offset', None)
            subs = getattr(sub_maker, 'subs', None)
            
            if offsets is None or subs is None:
                logger.warning(f"SubMaker missing offset or subs attribute. Available attributes: {[attr for attr in dir(sub_maker) if not attr.startswith('_')]}")
                return False
            
            if not offsets or not subs or len(offsets) == 0 or len(subs) == 0:
                logger.warning(f"SubMaker has empty offset or subs: offset={len(offsets) if offsets else 0}, subs={len(subs) if subs else 0}")
                return False
            
            if len(offsets) != len(subs):
                logger.warning(f"SubMaker offset and subs length mismatch: offset={len(offsets)}, subs={len(subs)}")
                return False
            
            for offset, sub in zip(offsets, subs):
                _start_time, end_time = offset
                if start_time < 0:
                    start_time = _start_time
                
                sub = unescape(sub)
                sub_line += sub
                sub_text = match_line(sub_line, sub_index)
                
                if sub_text:
                    sub_index += 1
                    # mktimestamp 期望 100纳秒单位，不需要转换
                    line = formatter(
                        idx=sub_index,
                        start_time=start_time,
                        end_time=end_time,
                        sub_text=sub_text
                    )
                    sub_items.append(line)
                    start_time = -1.0
                    sub_line = ""
            
            if len(sub_items) == len(script_lines):
                # 确保输出目录存在
                os.makedirs(os.path.dirname(subtitle_file) if os.path.dirname(subtitle_file) else ".", exist_ok=True)
                
                with open(subtitle_file, "w", encoding="utf-8") as file:
                    file.write("\n".join(sub_items) + "\n")
                
                logger.success(f"Subtitle file created: {subtitle_file}")
                return True
            else:
                logger.warning(
                    f"Subtitle mismatch: sub_items={len(sub_items)}, script_lines={len(script_lines)}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Failed to create subtitle: {e}")
            return False
    
    def _split_string_by_punctuations(self, text: str) -> list:
        """按标点符号分割文本"""
        import re
        # 按句号、问号、感叹号、换行符分割
        sentences = re.split(r"[。！？\n]+", text)
        return [s.strip() for s in sentences if s.strip()]
    
    def get_audio_duration(self, sub_maker: Optional[SubMaker]) -> float:
        """获取音频时长（秒）"""
        if not sub_maker:
            return 0.0
        
        # 安全地获取 offset 属性
        offset = getattr(sub_maker, 'offset', None)
        if not offset or len(offset) == 0:
            return 0.0
        
        try:
            # offset是100纳秒单位，转换为秒
            # offset 格式: [(start, end), ...]
            last_offset = offset[-1]
            if isinstance(last_offset, tuple) and len(last_offset) >= 2:
                return last_offset[1] / 10000000
            else:
                logger.warning(f"Invalid offset format: {last_offset}")
                return 0.0
        except Exception as e:
            logger.error(f"Failed to get audio duration from sub_maker: {e}")
            return 0.0

