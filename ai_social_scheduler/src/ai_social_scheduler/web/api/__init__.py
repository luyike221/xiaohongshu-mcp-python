"""API 路由"""

from fastapi import APIRouter

from .content import router as content_router

# 创建主路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(content_router)

__all__ = ["api_router"]
