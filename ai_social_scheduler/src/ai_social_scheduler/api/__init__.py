"""FastAPI API 模块"""

# 使用延迟导入，避免在导入 streaming_api 时触发 app.py 的导入
# 只有在真正需要时才导入 app 模块
__all__ = ["app", "create_app"]

def __getattr__(name):
    """延迟导入，只有在访问时才导入"""
    if name in ("app", "create_app"):
        from .app import app, create_app
        if name == "app":
            return app
        elif name == "create_app":
            return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

