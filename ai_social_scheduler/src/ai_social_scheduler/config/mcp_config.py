"""MCP服务配置管理"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载 .env 文件
env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class MCPConfig(BaseSettings):
    """MCP服务配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 小红书MCP服务配置
    xiaohongshu_mcp_url: str = "http://127.0.0.1:8002/mcp"
    xiaohongshu_mcp_transport: str = "streamable_http"  # streamable_http 或 stdio


# 全局MCP配置实例
mcp_config = MCPConfig()

