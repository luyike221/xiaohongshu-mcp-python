"""配置模块

提供配置加载和管理功能
"""

# 先导入 settings、model_config 和 mcp_config（避免循环导入）
from .config import settings
from .model_config import model_config
from .mcp_config import mcp_config

# loader 模块延迟导入（避免循环导入）
# 使用 __getattr__ 实现延迟导入
def __getattr__(name):
    if name == "ConfigLoader":
        from .loader import ConfigLoader
        return ConfigLoader
    if name == "load_config":
        from .loader import load_config
        return load_config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "settings",
    "model_config",
    "mcp_config",
    "ConfigLoader",
    "load_config",
]
