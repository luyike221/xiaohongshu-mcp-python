"""模型配置"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class AlibabaBailianConfig(BaseModel):
    """阿里百炼模型配置"""

    api_key: str = Field(..., description="API Key")
    api_secret: Optional[str] = Field(default=None, description="API Secret（可选，兼容模式通常不需要）")
    endpoint: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="API 端点",
    )
    model: str = Field(
        default="qwen-plus",
        description="模型名称，如 qwen-plus, qwen-turbo, qwen-max 等",
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大 token 数")
    timeout: int = Field(default=60, description="请求超时时间（秒）")


class DeepSeekOCRConfig(BaseModel):
    """DeepSeek OCR 模型配置"""

    api_key: str = Field(..., description="API Key")
    endpoint: str = Field(
        default="https://api.deepseek.com/v1/chat/completions",
        description="API 端点",
    )
    model: str = Field(
        default="deepseek-ocr",
        description="OCR 模型名称",
    )
    timeout: int = Field(default=60, description="请求超时时间（秒）")
    max_retries: int = Field(default=3, description="最大重试次数")


class ModelConfig(BaseSettings):
    """模型配置主类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    # 阿里百炼配置
    alibaba_bailian__api_key: Optional[str] = Field(default=None, alias="ALIBABA_BAILIAN_API_KEY")
    alibaba_bailian__api_secret: Optional[str] = Field(
        default=None, alias="ALIBABA_BAILIAN_API_SECRET"
    )
    alibaba_bailian__endpoint: Optional[str] = Field(
        default=None, alias="ALIBABA_BAILIAN_ENDPOINT"
    )
    alibaba_bailian__model: Optional[str] = Field(
        default=None, alias="ALIBABA_BAILIAN_MODEL"
    )
    alibaba_bailian__temperature: Optional[float] = Field(
        default=None, alias="ALIBABA_BAILIAN_TEMPERATURE"
    )
    alibaba_bailian__max_tokens: Optional[int] = Field(
        default=None, alias="ALIBABA_BAILIAN_MAX_TOKENS"
    )
    alibaba_bailian__timeout: Optional[int] = Field(
        default=None, alias="ALIBABA_BAILIAN_TIMEOUT"
    )

    @field_validator("alibaba_bailian__max_tokens", "alibaba_bailian__timeout", mode="before")
    @classmethod
    def parse_optional_int(cls, v):
        """将空字符串转换为 None"""
        if v == "" or v is None:
            return None
        return v

    # DeepSeek OCR 配置
    deepseek_ocr__api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_OCR_API_KEY")
    deepseek_ocr__endpoint: Optional[str] = Field(default=None, alias="DEEPSEEK_OCR_ENDPOINT")
    deepseek_ocr__model: Optional[str] = Field(default=None, alias="DEEPSEEK_OCR_MODEL")
    deepseek_ocr__timeout: Optional[int] = Field(default=None, alias="DEEPSEEK_OCR_TIMEOUT")
    deepseek_ocr__max_retries: Optional[int] = Field(
        default=None, alias="DEEPSEEK_OCR_MAX_RETRIES"
    )

    @field_validator("deepseek_ocr__timeout", "deepseek_ocr__max_retries", mode="before")
    @classmethod
    def parse_optional_int_ocr(cls, v):
        """将空字符串转换为 None"""
        if v == "" or v is None:
            return None
        return v

    def get_alibaba_bailian_config(self) -> AlibabaBailianConfig:
        """获取阿里百炼配置"""
        if not self.alibaba_bailian__api_key:
            raise ValueError("阿里百炼 API Key 必须配置")

        return AlibabaBailianConfig(
            api_key=self.alibaba_bailian__api_key,
            api_secret=self.alibaba_bailian__api_secret,
            endpoint=self.alibaba_bailian__endpoint
            or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=self.alibaba_bailian__model or "qwen-plus",
            temperature=self.alibaba_bailian__temperature or 0.7,
            max_tokens=self.alibaba_bailian__max_tokens,
            timeout=self.alibaba_bailian__timeout or 60,
        )

    def get_deepseek_ocr_config(self) -> DeepSeekOCRConfig:
        """获取 DeepSeek OCR 配置"""
        if not self.deepseek_ocr__api_key:
            raise ValueError("DeepSeek OCR API Key 必须配置")

        return DeepSeekOCRConfig(
            api_key=self.deepseek_ocr__api_key,
            endpoint=self.deepseek_ocr__endpoint
            or "https://api.deepseek.com/v1/chat/completions",
            model=self.deepseek_ocr__model or "deepseek-ocr",
            timeout=self.deepseek_ocr__timeout or 60,
            max_retries=self.deepseek_ocr__max_retries or 3,
        )


# 全局模型配置实例
model_config = ModelConfig()

