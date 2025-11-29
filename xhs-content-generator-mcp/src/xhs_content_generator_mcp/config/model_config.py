"""模型配置"""
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件
# 计算项目根目录的 .env 文件路径
# Path(__file__) = src/xhs_content_generator_mcp/config/model_config.py
# .parent = src/xhs_content_generator_mcp/config/
# .parent.parent = src/xhs_content_generator_mcp/
# .parent.parent.parent = src/
# .parent.parent.parent.parent = 项目根目录 xhs-content-generator-mcp/
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class GoogleGeminiConfig(BaseModel):
    """Google Gemini 模型配置"""

    api_key: str = Field(..., description="API Key")
    base_url: Optional[str] = Field(default=None, description="API 基础 URL（可选，自定义端点）")
    model: str = Field(
        default="gemini-2.0-flash-exp",
        description="模型名称，如 gemini-2.0-flash-exp, gemini-1.5-pro 等",
    )
    temperature: float = Field(default=1.0, ge=0.0, le=2.0, description="温度参数")
    max_output_tokens: int = Field(default=8000, description="最大输出 token 数")
    timeout: int = Field(default=300, description="请求超时时间（秒）")


class OpenAICompatibleConfig(BaseModel):
    """OpenAI 兼容接口配置"""

    api_key: str = Field(..., description="API Key")
    base_url: Optional[str] = Field(
        default=None,
        description="API 基础 URL（可选，默认使用 https://api.openai.com）",
    )
    model: str = Field(
        default="qwen-plus",
        description="模型名称，如 qwen-plus, qwen-turbo, qwen-max, gpt-4o, gpt-3.5-turbo 等",
    )
    temperature: float = Field(default=1.0, ge=0.0, le=2.0, description="温度参数")
    max_output_tokens: int = Field(default=8000, description="最大输出 token 数")
    timeout: int = Field(default=300, description="请求超时时间（秒）")
    endpoint_type: Optional[str] = Field(
        default=None, description="自定义端点路径（可选，默认 /v1/chat/completions）"
    )


class ModelConfig(BaseSettings):
    """模型配置主类"""

    model_config = SettingsConfigDict(
        # 使用绝对路径指向项目根目录的 .env 文件
        # 这样无论从哪个目录运行，都能正确找到 .env 文件
        # 如果文件不存在，BaseSettings 会忽略它，只从环境变量读取
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    # Google Gemini 配置
    google_gemini__api_key: Optional[str] = Field(
        default=None, alias="GEMINI_API_KEY"
    )
    google_gemini__base_url: Optional[str] = Field(
        default=None, alias="GEMINI_BASE_URL"
    )
    google_gemini__model: Optional[str] = Field(default=None, alias="GEMINI_MODEL")
    google_gemini__temperature: Optional[float] = Field(
        default=None, alias="GEMINI_TEMPERATURE"
    )
    google_gemini__max_output_tokens: Optional[int] = Field(
        default=None, alias="GEMINI_MAX_OUTPUT_TOKENS"
    )
    google_gemini__timeout: Optional[int] = Field(
        default=None, alias="GEMINI_TIMEOUT"
    )

    # OpenAI 兼容接口配置
    openai_compatible__api_key: Optional[str] = Field(
        default=None, alias="OPENAI_API_KEY"
    )
    openai_compatible__base_url: Optional[str] = Field(
        default=None, alias="OPENAI_BASE_URL"
    )
    openai_compatible__model: Optional[str] = Field(
        default=None, alias="OPENAI_MODEL"
    )
    openai_compatible__temperature: Optional[float] = Field(
        default=None, alias="OPENAI_TEMPERATURE"
    )
    openai_compatible__max_output_tokens: Optional[int] = Field(
        default=None, alias="OPENAI_MAX_OUTPUT_TOKENS"
    )
    openai_compatible__timeout: Optional[int] = Field(
        default=None, alias="OPENAI_TIMEOUT"
    )
    openai_compatible__endpoint_type: Optional[str] = Field(
        default=None, alias="OPENAI_ENDPOINT_TYPE"
    )
    openai_compatible__provider_name: Optional[str] = Field(
        default=None, alias="OPENAI_PROVIDER_NAME"
    )

    # 阿里百炼配置（兼容模式）
    alibaba_bailian__api_key: Optional[str] = Field(
        default=None, alias="ALIBABA_BAILIAN_API_KEY"
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

    # VL 模型配置（用于图片分析）
    vl_model__provider_type: Optional[str] = Field(
        default=None, alias="VL_MODEL_PROVIDER_TYPE"
    )
    vl_model__api_key: Optional[str] = Field(
        default=None, alias="VL_MODEL_API_KEY"
    )
    vl_model__base_url: Optional[str] = Field(
        default=None, alias="VL_MODEL_BASE_URL"
    )
    vl_model__model: Optional[str] = Field(
        default=None, alias="VL_MODEL_MODEL"
    )
    vl_model__temperature: Optional[float] = Field(
        default=None, alias="VL_MODEL_TEMPERATURE"
    )
    vl_model__max_output_tokens: Optional[int] = Field(
        default=None, alias="VL_MODEL_MAX_OUTPUT_TOKENS"
    )

    @field_validator(
        "google_gemini__max_output_tokens",
        "google_gemini__timeout",
        "openai_compatible__max_output_tokens",
        "openai_compatible__timeout",
        "alibaba_bailian__max_tokens",
        "alibaba_bailian__timeout",
        "vl_model__max_output_tokens",
        mode="before",
    )
    @classmethod
    def parse_optional_int(cls, v):
        """将空字符串转换为 None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator(
        "google_gemini__temperature",
        "openai_compatible__temperature",
        "alibaba_bailian__temperature",
        "vl_model__temperature",
        mode="before",
    )
    @classmethod
    def parse_optional_float(cls, v):
        """将空字符串转换为 None"""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return None
        return v

    def get_google_gemini_config(self) -> GoogleGeminiConfig:
        """获取 Google Gemini 配置"""
        if not self.google_gemini__api_key:
            raise ValueError("Google Gemini API Key 必须配置（设置环境变量 GEMINI_API_KEY）")

        return GoogleGeminiConfig(
            api_key=self.google_gemini__api_key,
            base_url=self.google_gemini__base_url,
            model=self.google_gemini__model or "gemini-2.0-flash-exp",
            temperature=self.google_gemini__temperature or 1.0,
            max_output_tokens=self.google_gemini__max_output_tokens or 8000,
            timeout=self.google_gemini__timeout or 300,
        )

    def get_openai_compatible_config(self) -> OpenAICompatibleConfig:
        """获取 OpenAI 兼容接口配置"""
        if not self.openai_compatible__api_key:
            raise ValueError(
                "OpenAI 兼容接口 API Key 必须配置（设置环境变量 OPENAI_API_KEY）"
            )

        return OpenAICompatibleConfig(
            api_key=self.openai_compatible__api_key,
            base_url=self.openai_compatible__base_url,
            model=self.openai_compatible__model or "qwen-plus",
            temperature=self.openai_compatible__temperature or 1.0,
            max_output_tokens=self.openai_compatible__max_output_tokens or 8000,
            timeout=self.openai_compatible__timeout or 300,
            endpoint_type=self.openai_compatible__endpoint_type,
        )

    def get_alibaba_bailian_config(self) -> OpenAICompatibleConfig:
        """获取阿里百炼配置（使用 OpenAI 兼容接口）"""
        if not self.alibaba_bailian__api_key:
            raise ValueError("阿里百炼 API Key 必须配置（设置环境变量 ALIBABA_BAILIAN_API_KEY）")

        return OpenAICompatibleConfig(
            api_key=self.alibaba_bailian__api_key,
            base_url=self.alibaba_bailian__endpoint or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=self.alibaba_bailian__model or "qwen-plus",
            temperature=self.alibaba_bailian__temperature or 0.3,
            max_output_tokens=self.alibaba_bailian__max_tokens or 8000,
            timeout=self.alibaba_bailian__timeout or 60,
            endpoint_type=None,  # 使用默认端点
        )

    def get_provider_config(
        self, provider_type: str, model: Optional[str] = None, temperature: Optional[float] = None, max_output_tokens: Optional[int] = None
    ) -> dict:
        """
        获取服务商配置字典（用于传递给客户端）
        
        Args:
            provider_type: 服务商类型，'google_gemini'、'openai_compatible' 或 'alibaba_bailian'
            model: 模型名称（可选，覆盖配置中的模型）
            temperature: 温度参数（可选，覆盖配置中的温度）
            max_output_tokens: 最大输出 token 数（可选，覆盖配置中的值）
        
        Returns:
            配置字典
        """
        if provider_type == "google_gemini":
            config = self.get_google_gemini_config()
            return {
                "type": "google_gemini",
                "api_key": config.api_key,
                "base_url": config.base_url,
                "model": model or config.model,
                "temperature": temperature if temperature is not None else config.temperature,
                "max_output_tokens": max_output_tokens if max_output_tokens is not None else config.max_output_tokens,
            }
        elif provider_type == "alibaba_bailian":
            config = self.get_alibaba_bailian_config()
            return {
                "type": "openai_compatible",
                "provider_name": "alibaba-bailian",
                "api_key": config.api_key,
                "base_url": config.base_url,
                "endpoint_type": config.endpoint_type,
                "model": model or config.model,
                "temperature": temperature if temperature is not None else config.temperature,
                "max_output_tokens": max_output_tokens if max_output_tokens is not None else config.max_output_tokens,
            }
        elif provider_type == "openai_compatible":
            config = self.get_openai_compatible_config()
            # 如果配置了 provider_name，使用它
            provider_name = self.openai_compatible__provider_name
            result = {
                "type": "openai_compatible",
                "api_key": config.api_key,
                "base_url": config.base_url,
                "endpoint_type": config.endpoint_type,
                "model": model or config.model,
                "temperature": temperature if temperature is not None else config.temperature,
                "max_output_tokens": max_output_tokens if max_output_tokens is not None else config.max_output_tokens,
            }
            if provider_name:
                result["provider_name"] = provider_name
            return result
        else:
            raise ValueError(f"不支持的服务商类型: {provider_type}")

    def get_vl_model_config(self) -> dict:
        """
        获取 VL 模型配置（用于图片分析）
        
        默认使用阿里云 qwen3-vl-plus 模型
        
        Returns:
            VL 模型配置字典，如果未配置则返回 None
        """
        # 如果单独配置了 VL 模型，使用配置的值
        if self.vl_model__api_key:
            provider_type = self.vl_model__provider_type or "openai_compatible"
            
            if provider_type == "openai_compatible":
                return {
                    "type": "openai_compatible",
                    "api_key": self.vl_model__api_key,
                    "base_url": self.vl_model__base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": self.vl_model__model or "qwen3-vl-plus",
                    "temperature": self.vl_model__temperature if self.vl_model__temperature is not None else 0.3,
                    "max_output_tokens": self.vl_model__max_output_tokens or 2000,
                }
            elif provider_type == "google_gemini":
                # 尝试使用 Google Gemini 配置
                try:
                    gemini_config = self.get_google_gemini_config()
                    return {
                        "type": "google_gemini",
                        "api_key": self.vl_model__api_key or gemini_config.api_key,
                        "base_url": self.vl_model__base_url or gemini_config.base_url,
                        "model": self.vl_model__model or gemini_config.model,
                        "temperature": self.vl_model__temperature if self.vl_model__temperature is not None else 0.3,
                        "max_output_tokens": self.vl_model__max_output_tokens or 2000,
                    }
                except ValueError:
                    return {
                        "type": "google_gemini",
                        "api_key": self.vl_model__api_key,
                        "base_url": self.vl_model__base_url,
                        "model": self.vl_model__model or "gemini-2.0-flash-exp",
                        "temperature": self.vl_model__temperature or 0.3,
                        "max_output_tokens": self.vl_model__max_output_tokens or 2000,
                    }
            else:
                # 其他类型的 VL 模型
                return {
                    "type": provider_type,
                    "api_key": self.vl_model__api_key,
                    "base_url": self.vl_model__base_url,
                    "model": self.vl_model__model or "gpt-4o",
                    "temperature": self.vl_model__temperature or 0.3,
                    "max_output_tokens": self.vl_model__max_output_tokens or 2000,
                }
        
        # 如果没有单独配置 VL 模型，尝试使用阿里百炼配置（默认使用 qwen3-vl-plus）
        try:
            bailian_config = self.get_alibaba_bailian_config()
            return {
                "type": "openai_compatible",
                "api_key": bailian_config.api_key,
                "base_url": bailian_config.base_url,
                "model": "qwen3-vl-plus",  # VL 模型使用 qwen3-vl-plus
                "temperature": 0.3,  # 图片分析使用较低温度
                "max_output_tokens": 2000,  # 图片分析不需要太多 token
            }
        except ValueError:
            # 如果阿里百炼也未配置，尝试使用 Google Gemini 配置（向后兼容）
            try:
                gemini_config = self.get_google_gemini_config()
                return {
                    "type": "google_gemini",
                    "api_key": gemini_config.api_key,
                    "base_url": gemini_config.base_url,
                    "model": gemini_config.model,
                    "temperature": 0.3,
                    "max_output_tokens": 2000,
                }
            except ValueError:
                # 如果都未配置，返回 None（表示未配置 VL 模型）
                return None


# 全局模型配置实例
model_config = ModelConfig()
