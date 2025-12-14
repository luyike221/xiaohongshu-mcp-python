"""
应用配置模块
使用 python-dotenv 管理环境变量，支持开发和生产环境
"""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# 加载 .env 文件
# 注意：这里不能使用 get_project_root()，因为函数定义在后面
# 所以先使用相对路径，如果 get_project_root() 可用则使用它
_temp_root = Path(__file__).parent.parent.parent.parent
env_path = _temp_root / ".env"
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
    
    # 浏览器可执行文件路径（用于使用本地浏览器）
    # 如果未设置，则使用 Playwright 自带的浏览器
    # Ubuntu 常见路径：
    # - Google Chrome: /usr/bin/google-chrome 或 /usr/bin/google-chrome-stable
    # - Chromium: /usr/bin/chromium 或 /usr/bin/chromium-browser
    BROWSER_EXECUTABLE_PATH: str | None = os.getenv("BROWSER_EXECUTABLE_PATH", None)
    
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
    
    # 发布测试配置
    # 如果设置为 true，发布时会阻塞，不点击发布按钮（用于测试）
    PUBLISH_BLOCK_TEST: bool = os.getenv("PUBLISH_BLOCK_TEST", "false").lower() in ("true", "1", "yes")
    
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
            "publish_block_test": cls.PUBLISH_BLOCK_TEST,
        }
    
    @classmethod
    def __repr__(cls) -> str:
        """配置的字符串表示"""
        return f"Settings(ENV={cls.ENV}, HEADLESS={cls.BROWSER_HEADLESS}, LOG_LEVEL={cls.LOG_LEVEL})"


# 创建全局配置实例
settings = Settings()


def get_project_root() -> Path:
    """
    获取项目根目录（xhs-browser-automation-mcp目录）
    
    从当前文件位置向上查找，直到找到包含 pyproject.toml 和 src/xiaohongshu_mcp_python 的目录
    这样可以确保即使代码被安装到外部目录，也能找到正确的项目根目录
    
    重要：项目根目录最高只能是 xhs-browser-automation-mcp 目录，
    不能是父级目录（/root/project/ai_project/yx_运营/xhs_小红书运营/）
    
    Returns:
        项目根目录路径（xhs-browser-automation-mcp目录）
    """
    # 从当前文件位置开始
    current_file = Path(__file__).resolve()
    
    # 定义项目根目录的标识：必须包含 src/xiaohongshu_mcp_python 目录
    # 这是最可靠的标识，因为这是项目的源代码目录结构
    required_src_dir = Path("src") / "xiaohongshu_mcp_python"
    
    # 首先尝试查找包含 src/xiaohongshu_mcp_python 的目录
    # 这是最可靠的标识，因为这是项目的源代码目录结构
    for parent in current_file.parents:
        # 检查是否包含 src/xiaohongshu_mcp_python 目录
        src_dir = parent / required_src_dir
        if src_dir.exists() and src_dir.is_dir():
            # 进一步验证是否包含 pyproject.toml（确保是项目根目录）
            if (parent / "pyproject.toml").exists():
                # 关键验证：确保目录名是 xhs-browser-automation-mcp
                # 这样可以防止返回父级目录（/root/project/ai_project/yx_运营/xhs_小红书运营/）
                if parent.name == "xhs-browser-automation-mcp":
                    return parent
                # 如果目录名不匹配，继续查找（不返回，确保只返回正确的目录）
                continue
    
    # 如果上面的方法找不到，尝试从当前文件位置向上查找包含 pyproject.toml 的目录
    # 然后验证是否包含 src/xiaohongshu_mcp_python
    for parent in current_file.parents:
        if (parent / "pyproject.toml").exists():
            # 检查是否包含 src/xiaohongshu_mcp_python 目录
            if (parent / required_src_dir).exists():
                # 关键验证：确保目录名是 xhs-browser-automation-mcp
                if parent.name == "xhs-browser-automation-mcp":
                    return parent
                # 如果目录名不匹配，继续查找（不返回，确保只返回正确的目录）
                continue
    
    # 如果都找不到，使用 fallback：当前文件所在目录向上4级
    # settings.py 在 src/xiaohongshu_mcp_python/config/ 下
    # 所以向上4级就是项目根目录
    fallback_root = current_file.parent.parent.parent.parent
    
    # 验证 fallback_root 是否是有效的项目根目录
    if (fallback_root / required_src_dir).exists():
        # 关键验证：确保目录名是 xhs-browser-automation-mcp
        if fallback_root.name == "xhs-browser-automation-mcp":
            return fallback_root
    
    # 如果所有方法都找不到正确的目录，返回 fallback_root
    # 这样可以避免在找不到项目根目录时抛出异常
    # 但理论上不应该到达这里，因为当前文件就在 xhs-browser-automation-mcp 目录下
    return fallback_root

