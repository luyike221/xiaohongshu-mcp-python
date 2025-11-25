"""
应用配置模块
使用 python-dotenv 管理环境变量，支持开发和生产环境
"""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # 尝试加载项目根目录的 .env
    project_root = Path(__file__).parent.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


# 环境类型
Environment = Literal["development", "production"]


class Settings:
    """应用配置类"""
    
    # 环境配置
    ENV: Environment = os.getenv("ENV", "development").lower()  # 默认开发环境
    
    # 是否为开发环境
    IS_DEVELOPMENT: bool = ENV == "development"
    IS_PRODUCTION: bool = ENV == "production"
    
    # 浏览器配置
    # 如果未设置 BROWSER_HEADLESS，则根据环境自动决定
    _browser_headless_env = os.getenv("BROWSER_HEADLESS", "").strip().lower()
    if _browser_headless_env in ("true", "1", "yes"):
        BROWSER_HEADLESS: bool = True
    elif _browser_headless_env in ("false", "0", "no"):
        BROWSER_HEADLESS: bool = False
    else:
        # 未设置时，根据环境自动决定：生产环境默认无头，开发环境默认有头
        BROWSER_HEADLESS: bool = IS_PRODUCTION
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG" if IS_DEVELOPMENT else "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}"
    )
    LOG_FILE: str | None = os.getenv("LOG_FILE", None)  # 如果设置，日志会写入文件
    
    # 服务器配置
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    
    # 全局用户配置
    GLOBAL_USER: str = os.getenv("GLOBAL_USER", "luyike")
    
    # 浏览器超时配置
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "60000"))
    ELEMENT_TIMEOUT: int = int(os.getenv("ELEMENT_TIMEOUT", "30000"))
    
    # 调试配置（仅开发环境）
    DEBUG: bool = IS_DEVELOPMENT
    DEBUG_SCREENSHOTS: bool = os.getenv("DEBUG_SCREENSHOTS", "false").lower() in ("true", "1", "yes") if IS_DEVELOPMENT else False
    
    @classmethod
    def get_summary(cls) -> dict:
        """获取配置摘要"""
        return {
            "environment": cls.ENV,
            "is_development": cls.IS_DEVELOPMENT,
            "is_production": cls.IS_PRODUCTION,
            "browser_headless": cls.BROWSER_HEADLESS,
            "log_level": cls.LOG_LEVEL,
            "server_host": cls.SERVER_HOST,
            "server_port": cls.SERVER_PORT,
            "global_user": cls.GLOBAL_USER,
            "debug": cls.DEBUG,
        }
    
    @classmethod
    def __repr__(cls) -> str:
        """配置的字符串表示"""
        return f"Settings(ENV={cls.ENV}, HEADLESS={cls.BROWSER_HEADLESS}, LOG_LEVEL={cls.LOG_LEVEL})"


# 创建全局配置实例
settings = Settings()


def get_project_root() -> Path:
    """
    获取项目根目录（xiaohongshu_mcp目录）
    
    从当前文件位置向上查找，直到找到包含 pyproject.toml 的目录
    
    Returns:
        项目根目录路径
    """
    # 从当前文件位置开始
    current_file = Path(__file__).resolve()
    
    # 向上查找，直到找到包含 pyproject.toml 的目录
    for parent in current_file.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    
    # 如果找不到，返回当前文件所在目录的父目录的父目录（通常是项目根目录）
    # settings.py 在 src/xiaohongshu_mcp_python/config/ 下
    # 所以向上3级就是项目根目录
    return current_file.parent.parent.parent.parent

