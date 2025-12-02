"""配置设置"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

 
import image_video_mcp


_project_root = Path(image_video_mcp.__file__).parent.parent.parent
_env_path = _project_root / ".env"
load_dotenv(dotenv_path=_env_path)


class WanT2IConfig(BaseSettings):
    """通义万相 T2I 模型配置"""

    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API 配置
    api_key: str = Field(..., description="DashScope API Key")
    endpoint: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
        description="API 端点（北京地域）",
    )
    model: str = Field(
        default="wan2.5-t2i-preview",
        description="模型名称",
    )
    timeout: int = Field(
        default=120,
        description="请求超时时间（秒）",
    )
    max_retries: int = Field(
        default=3,
        description="最大重试次数",
    )

    # 默认参数
    default_size: str = Field(
        default="1280*1280",
        description="默认图像尺寸",
    )
    default_n: int = Field(
        default=1,
        description="默认生成图像数量",
    )


class GoogleGenAIConfig(BaseSettings):
    """Google GenAI 配置"""

    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API 配置
    api_key: str = Field(..., description="Google GenAI API Key")
    base_url: Optional[str] = Field(
        default=None,
        description="自定义 API 端点（可选）",
    )
    model: str = Field(
        default="gemini-3-pro-image-preview",
        description="模型名称",
    )
    temperature: float = Field(
        default=1.0,
        description="温度参数",
    )
    default_aspect_ratio: str = Field(
        default="3:4",
        description="默认宽高比",
    )


class Settings(BaseSettings):
    """全局设置"""

    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    # 通义万相 T2I 配置
    wan_t2i__api_key: Optional[str] = Field(default=None, alias="DASHSCOPE_API_KEY")
    wan_t2i__endpoint: Optional[str] = Field(
        default=None, alias="WAN_T2I_ENDPOINT"
    )
    wan_t2i__model: Optional[str] = Field(default=None, alias="WAN_T2I_MODEL")
    wan_t2i__timeout: Optional[int] = Field(default=None, alias="WAN_T2I_TIMEOUT")
    wan_t2i__max_retries: Optional[int] = Field(
        default=None, alias="WAN_T2I_MAX_RETRIES"
    )
    wan_t2i__default_size: Optional[str] = Field(
        default=None, alias="WAN_T2I_DEFAULT_SIZE"
    )
    wan_t2i__default_n: Optional[int] = Field(default=None, alias="WAN_T2I_DEFAULT_N")

    # Google GenAI 配置
    google_genai__api_key: Optional[str] = Field(default=None, alias="GOOGLE_GENAI_API_KEY")
    google_genai__base_url: Optional[str] = Field(default=None, alias="GOOGLE_GENAI_BASE_URL")
    google_genai__model: Optional[str] = Field(default=None, alias="GOOGLE_GENAI_MODEL")
    google_genai__temperature: Optional[float] = Field(default=None, alias="GOOGLE_GENAI_TEMPERATURE")
    google_genai__default_aspect_ratio: Optional[str] = Field(
        default=None, alias="GOOGLE_GENAI_DEFAULT_ASPECT_RATIO"
    )

    def get_wan_t2i_config(self) -> WanT2IConfig:
        """获取通义万相 T2I 配置"""
        if not self.wan_t2i__api_key:
            raise ValueError("通义万相 T2I API Key 必须配置（DASHSCOPE_API_KEY）")

        return WanT2IConfig(
            api_key=self.wan_t2i__api_key,
            endpoint=self.wan_t2i__endpoint
            or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
            model=self.wan_t2i__model or "wan2.5-t2i-preview",
            timeout=self.wan_t2i__timeout or 120,
            max_retries=self.wan_t2i__max_retries or 3,
            default_size=self.wan_t2i__default_size or "1280*1280",
            default_n=self.wan_t2i__default_n or 1,
        )

    def get_google_genai_config(self) -> GoogleGenAIConfig:
        """获取 Google GenAI 配置"""
        if not self.google_genai__api_key:
            raise ValueError("Google GenAI API Key 必须配置（GOOGLE_GENAI_API_KEY）")

        return GoogleGenAIConfig(
            api_key=self.google_genai__api_key,
            base_url=self.google_genai__base_url,
            model=self.google_genai__model or "gemini-3-pro-image-preview",
            temperature=self.google_genai__temperature or 1.0,
            default_aspect_ratio=self.google_genai__default_aspect_ratio or "3:4",
        )


# 全局设置实例
settings = Settings()

