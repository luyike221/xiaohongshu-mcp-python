#!/usr/bin/env python3
"""一键启动流式前后端服务

快速启动 AI Social Scheduler 流式 API 服务
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

import uvicorn
from ai_social_scheduler.app import SocialSchedulerApp
from ai_social_scheduler.api.streaming_api import create_streaming_router
from ai_social_scheduler.graph.streaming import StreamingGraphExecutor
from ai_social_scheduler.router import RouterStrategy
from ai_social_scheduler.tools.logging import get_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("Initializing AI Social Scheduler...")
    
    # 创建调度器应用
    scheduler_app = SocialSchedulerApp(
        router_strategy=RouterStrategy.RULE_FIRST
    )
    
    # 初始化
    await scheduler_app.initialize()
    
    # 创建流式执行器
    streaming_executor = StreamingGraphExecutor(
        compiled_graph=scheduler_app.graph_executor.graph
    )
    
    # 保存到应用状态
    app.state.scheduler_app = scheduler_app
    app.state.streaming_executor = streaming_executor
    
    # 注册流式路由
    streaming_router = create_streaming_router(
        executor=streaming_executor
    )
    app.include_router(streaming_router)
    
    logger.info("✅ Application initialized successfully")
    
    yield
    
    # 关闭时清理（如果需要）
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """创建流式应用"""
    app = FastAPI(
        title="AI Social Scheduler - 流式 API",
        description="支持实时展示 Graph 处理流程的 API",
        version="2.0.0",
        lifespan=lifespan,
    )
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """根路径 - 显示演示页面"""
        html_path = project_root / "examples" / "streaming_demo.html"
        
        if html_path.exists():
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return {
                "message": "AI Social Scheduler 流式 API",
                "docs": "/docs",
                "streaming_endpoint": "/api/v1/chat/stream",
            }
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        if app.state.scheduler_app and app.state.scheduler_app._initialized:
            return {
                "status": "healthy",
                "initialized": True,
                "stats": app.state.scheduler_app.get_stats(),
            }
        else:
            return {
                "status": "initializing",
                "initialized": False,
            }
    
    @app.get("/api/v1/stats")
    async def get_stats():
        """获取统计信息"""
        if app.state.scheduler_app:
            return app.state.scheduler_app.get_stats()
        return {"error": "App not initialized"}
    
    return app


def main():
    """主函数"""
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8020"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()  # 确保小写
    
    # 创建应用
    app = create_app()
    
    # 打印启动信息
    print("\n" + "="*60)
    print("  🚀 AI Social Scheduler 流式服务")
    print("="*60)
    print(f"\n  📊 前端地址: http://localhost:{port}")
    print(f"  📖 API 文档: http://localhost:{port}/docs")
    print(f"  🔄 流式接口: http://localhost:{port}/api/v1/chat/stream")
    print(f"  ❤️  健康检查: http://localhost:{port}/health")
    print("\n" + "="*60)
    print("  提示: 按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    # 启动服务
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()

