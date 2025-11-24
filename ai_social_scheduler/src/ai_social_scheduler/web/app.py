"""FastAPI 应用主文件"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from ..ai_agent.tools.logging import get_logger

logger = get_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="小红书运营Agent API",
    description="基于LangGraph的小红书运营Agent API服务",
    version="0.1.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "小红书运营Agent API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    """应用启动事件"""
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭事件"""
    logger.info("Application shutdown")

