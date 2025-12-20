"""配置管理模块"""
import os
from pathlib import Path
from typing import Optional, List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from dotenv import load_dotenv

# 加载 .env 文件
# 优先从项目根目录查找 .env 文件
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # 如果项目根目录没有，尝试当前工作目录
    load_dotenv()


class Settings(BaseSettings):
    """应用配置"""
    
    # LLM 配置
    llm_provider: str = Field(default="openai", description="LLM提供商: openai, moonshot, deepseek, qwen等")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI Base URL")
    openai_model_name: str = Field(default="gpt-3.5-turbo", description="OpenAI 模型名称")
    
    moonshot_api_key: Optional[str] = Field(default=None, description="Moonshot API Key")
    moonshot_model_name: str = Field(default="moonshot-v1-8k", description="Moonshot 模型名称")
    
    deepseek_api_key: Optional[str] = Field(default=None, description="DeepSeek API Key")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", description="DeepSeek Base URL")
    deepseek_model_name: str = Field(default="deepseek-chat", description="DeepSeek 模型名称")
    
    # 视频素材配置
    pexels_api_keys: Optional[Union[str, List[str]]] = Field(default=None, description="Pexels API Keys（多个用逗号分隔）")
    pixabay_api_keys: Optional[Union[str, List[str]]] = Field(default=None, description="Pixabay API Keys（多个用逗号分隔）")
    
    @field_validator("pexels_api_keys", mode="before")
    @classmethod
    def parse_pexels_keys(cls, v):
        """解析 Pexels API Keys"""
        if v is None:
            return None
        if isinstance(v, list):
            # 如果已经是列表，直接返回
            return v if v else None
        if isinstance(v, str):
            # 支持逗号分隔的多个key
            keys = [key.strip() for key in v.split(",") if key.strip()]
            return keys if keys else None
        return v
    
    @field_validator("pixabay_api_keys", mode="before")
    @classmethod
    def parse_pixabay_keys(cls, v):
        """解析 Pixabay API Keys"""
        if v is None:
            return None
        if isinstance(v, list):
            # 如果已经是列表，直接返回
            return v if v else None
        if isinstance(v, str):
            # 支持逗号分隔的多个key
            keys = [key.strip() for key in v.split(",") if key.strip()]
            return keys if keys else None
        return v
    
    # TTS 配置
    voice_provider: str = Field(default="edge", description="TTS提供商: edge, azure, gemini")
    azure_speech_key: Optional[str] = Field(default=None, description="Azure Speech Key")
    azure_speech_region: Optional[str] = Field(default=None, description="Azure Speech Region")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API Key")
    
    # 字幕配置
    subtitle_provider: str = Field(default="edge", description="字幕提供商: edge, whisper")
    whisper_model_size: str = Field(default="large-v3", description="Whisper模型大小")
    whisper_device: str = Field(default="cpu", description="Whisper设备: cpu, cuda")
    
    # 视频配置
    video_output_dir: str = Field(default="./output", description="视频输出目录")
    material_cache_dir: str = Field(default="./cache/materials", description="素材缓存目录")
    max_clip_duration: int = Field(default=5, description="最大片段时长（秒）")
    video_fps: int = Field(default=30, description="视频帧率")
    video_gpu_acceleration: bool = Field(default=False, description="是否启用GPU加速（需要NVIDIA GPU和NVENC支持）")
    video_codec: str = Field(default="auto", description="视频编码器: auto, libx264, h264_nvenc, hevc_nvenc")
    
    # 代理配置
    proxy_enabled: bool = Field(default=False, description="是否启用代理")
    proxy_http: Optional[str] = Field(default=None, description="HTTP代理地址")
    proxy_https: Optional[str] = Field(default=None, description="HTTPS代理地址")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # 支持从环境变量读取配置
        env_prefix="",  # 不使用前缀，直接使用变量名
    )
    
    @property
    def proxy(self) -> Optional[dict]:
        """获取代理配置"""
        if not self.proxy_enabled:
            return None
        proxies = {}
        if self.proxy_http:
            proxies["http"] = self.proxy_http
        if self.proxy_https:
            proxies["https"] = self.proxy_https
        return proxies if proxies else None


settings = Settings()

