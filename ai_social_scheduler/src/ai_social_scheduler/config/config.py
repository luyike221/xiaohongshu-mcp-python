"""配置管理 (Pydantic Settings)"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "xiaohongshu-agent"
    app_version: str = "0.1.0"
    debug: bool = False

    # LLM 配置
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_provider: str = "openai"  # openai 或 anthropic
    default_model: str = "gpt-4"

    # 数据库配置
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/xiaohongshu"
    database_echo: bool = False

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # Celery 配置
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # 存储配置
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None
    minio_bucket: Optional[str] = None

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"  # json 或 text

    # 监控配置
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 9090


# 全局配置实例
settings = Settings()

