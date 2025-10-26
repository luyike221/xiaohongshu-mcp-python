"""
FastAPI HTTP 服务器实现
提供小红书 MCP 服务的 HTTP API 接口
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .service import XiaohongshuService
from .browser import BrowserManager
from .managers.user_session_manager import get_user_session_manager

logger = logging.getLogger(__name__)

# 请求/响应模型
class ErrorResponse(BaseModel):
    error: str
    code: str
    details: Optional[Any] = None

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    message: Optional[str] = None

class PublishRequest(BaseModel):
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    images: List[str] = Field(default=[], description="图片列表（URL或本地路径）")
    tags: List[str] = Field(default=[], description="标签列表")

class PublishVideoRequest(BaseModel):
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    video: str = Field(..., description="视频文件路径")
    tags: List[str] = Field(default=[], description="标签列表")

class SearchRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")
    page: int = Field(default=1, description="页码")
    limit: int = Field(default=20, description="每页数量")

class FeedDetailRequest(BaseModel):
    feed_id: str = Field(..., description="笔记ID")

class UserProfileRequest(BaseModel):
    user_id: str = Field(..., description="用户ID")
    xsec_token: Optional[str] = Field(None, description="安全令牌")

class PostCommentRequest(BaseModel):
    feed_id: str = Field(..., description="笔记ID")
    content: str = Field(..., description="评论内容")
    xsec_token: Optional[str] = Field(None, description="安全令牌")

# 全局变量
app_state = {
    "xiaohongshu_service": None,
    "browser_manager": None,
    "user_session_manager": None
}

# 为 XiaohongshuService 添加简化接口方法
class XiaohongshuServiceWrapper:
    def __init__(self, service):
        self.service = service
    
    def __getattr__(self, name):
        return getattr(self.service, name)
    
    async def publish_content(
        self,
        title: str,
        content: str,
        images: List[str] = None,
        tags: List[str] = None,
        username: Optional[str] = None
    ) -> Any:
        """
        发布图文内容的简化接口
        
        Args:
            title: 标题
            content: 内容
            images: 图片列表
            tags: 标签列表
            username: 用户名
            
        Returns:
            发布结果
        """
        from .types import PublishImageContent
        
        # 构建发布内容对象
        publish_content_obj = PublishImageContent(
            title=title,
            content=content,
            images=images or [],
            tags=tags or []
        )
        
        # 调用原始方法
        return await self.service.publish_content(publish_content_obj, username)
    
    async def publish_video(
        self,
        title: str,
        content: str,
        video: str,
        tags: List[str] = None,
        username: Optional[str] = None
    ) -> Any:
        """
        发布视频内容的简化接口
        
        Args:
            title: 标题
            content: 内容
            video: 视频文件路径
            tags: 标签列表
            username: 用户名
            
        Returns:
            发布结果
        """
        from .types import PublishVideoContent
        
        # 构建发布内容对象
        publish_content_obj = PublishVideoContent(
            title=title,
            content=content,
            video_path=video,
            tags=tags or []
        )
        
        # 调用原始方法
        return await self.service.publish_video(publish_content_obj, username)
    
    async def search_content(
        self,
        keyword: str,
        page: int = 1,
        limit: int = 20,
        username: Optional[str] = None
    ) -> Any:
        """
        搜索内容的简化接口
        
        Args:
            keyword: 搜索关键词
            page: 页码
            limit: 每页数量
            username: 用户名
            
        Returns:
            搜索结果
        """
        # 调用原始方法
        return await self.service.search_content(keyword, page, username)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("初始化 FastAPI 应用...")
    
    # 初始化浏览器管理器
    browser_manager = BrowserManager()
    app_state["browser_manager"] = browser_manager
    
    # 初始化用户会话管理器
    user_session_manager = get_user_session_manager()
    app_state["user_session_manager"] = user_session_manager
    
    # 初始化小红书服务
    xiaohongshu_service = XiaohongshuService(browser_manager)
    app_state["xiaohongshu_service"] = XiaohongshuServiceWrapper(xiaohongshu_service)
    
    logger.info("FastAPI 应用初始化完成")
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭 FastAPI 应用...")
    
    if app_state["xiaohongshu_service"]:
        await app_state["xiaohongshu_service"].cleanup()
    
    if app_state["browser_manager"]:
        await app_state["browser_manager"].stop()
    
    logger.info("FastAPI 应用已关闭")

# 创建 FastAPI 应用
app = FastAPI(
    title="小红书 MCP HTTP API",
    description="小红书 MCP 服务的 HTTP API 接口",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
            details=getattr(exc, 'details', None)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"服务器内部错误: {exc}, path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="服务器内部错误",
            code="INTERNAL_ERROR",
            details=str(exc)
        ).dict()
    )

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return SuccessResponse(
        data={
            "status": "healthy",
            "service": "xiaohongshu-mcp-python",
            "account": "ai-report",
            "timestamp": "now"
        },
        message="服务正常"
    )

# 登录管理 API
@app.get("/api/v1/login/status")
async def check_login_status():
    """检查登录状态"""
    try:
        user_session_manager = app_state["user_session_manager"]
        
        # 使用默认用户检查登录状态
        status = await user_session_manager.get_user_session_status("default")
        
        if status and status["status"] == "logged_in":
            return SuccessResponse(
                data={
                    "is_logged_in": True,
                    "username": status.get("username", "default")
                },
                message="检查登录状态成功"
            )
        else:
            return SuccessResponse(
                data={
                    "is_logged_in": False,
                    "username": None
                },
                message="用户未登录"
            )
            
    except Exception as e:
        logger.error(f"检查登录状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="检查登录状态失败"
        )

@app.get("/api/v1/login/qrcode")
async def get_login_qrcode():
    """获取登录二维码"""
    try:
        user_session_manager = app_state["user_session_manager"]
        
        # 获取登录二维码
        qrcode_info = await user_session_manager.get_login_qrcode("default")
        
        return SuccessResponse(
            data={
                "qrcode_url": qrcode_info.image_url,
                "qrcode_data": qrcode_info.image_data,
                "token": qrcode_info.token
            },
            message="获取登录二维码成功"
        )
        
    except Exception as e:
        logger.error(f"获取登录二维码失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取登录二维码失败"
        )

# 内容发布 API
@app.post("/api/v1/publish")
async def publish_content(request: PublishRequest):
    """发布图文内容"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 执行发布
        result = await xiaohongshu_service.publish_content(
            title=request.title,
            content=request.content,
            images=request.images,
            tags=request.tags,
            username="default"
        )
        
        return SuccessResponse(
            data={
                "title": request.title,
                "content": request.content,
                "images": len(request.images),
                "status": "发布完成",
                "post_id": getattr(result, 'post_id', None)
            },
            message="发布成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布内容失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="发布失败"
        )

@app.post("/api/v1/publish_video")
async def publish_video(request: PublishVideoRequest):
    """发布视频内容"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 执行发布
        result = await xiaohongshu_service.publish_video(
            title=request.title,
            content=request.content,
            video=request.video,
            tags=request.tags,
            username="default"
        )
        
        return SuccessResponse(
            data={
                "title": request.title,
                "content": request.content,
                "video": request.video,
                "status": "发布完成"
            },
            message="视频发布成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发布视频失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="视频发布失败"
        )

# 内容获取 API
@app.get("/api/v1/feeds/list")
async def list_feeds():
    """获取推荐内容列表"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 获取推荐内容
        result = await xiaohongshu_service.get_feeds_list(username="default")
        
        return SuccessResponse(
            data=result.dict() if hasattr(result, 'dict') else result.__dict__,
            message="获取推荐内容成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取推荐内容失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取推荐内容失败"
        )

@app.get("/api/v1/feeds/search")
async def search_feeds(keyword: str, page: int = 1, limit: int = 20):
    """搜索内容"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 执行搜索
        result = await xiaohongshu_service.search_content(
            keyword=keyword,
            page=page,
            limit=limit,
            username="default"
        )
        
        return SuccessResponse(
            data=result.dict() if hasattr(result, 'dict') else result.__dict__,
            message="搜索内容成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索内容失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="搜索内容失败"
        )

@app.post("/api/v1/feeds/detail")
async def get_feed_detail(request: FeedDetailRequest):
    """获取笔记详情"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 获取笔记详情
        result = await xiaohongshu_service.get_feed_detail(
            feed_id=request.feed_id,
            username="default"
        )
        
        return SuccessResponse(
            data=result.dict() if hasattr(result, 'dict') else result.__dict__,
            message="获取笔记详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取笔记详情失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取笔记详情失败"
        )

@app.post("/api/v1/user/profile")
async def get_user_profile(request: UserProfileRequest):
    """获取用户主页信息"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 获取用户信息
        result = await xiaohongshu_service.get_user_profile(
            user_id=request.user_id,
            username="default"
        )
        
        return SuccessResponse(
            data=result.dict() if hasattr(result, 'dict') else result.__dict__,
            message="获取用户主页成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户主页失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取用户主页失败"
        )

@app.post("/api/v1/feeds/comment")
async def post_comment(request: PostCommentRequest):
    """发表评论"""
    try:
        xiaohongshu_service = app_state["xiaohongshu_service"]
        
        # 检查登录状态
        user_session_manager = app_state["user_session_manager"]
        status = await user_session_manager.get_user_session_status("default")
        
        if not status or status["status"] != "logged_in":
            raise HTTPException(
                status_code=401,
                detail="用户未登录，请先登录"
            )
        
        # 发表评论
        result = await xiaohongshu_service.post_comment_to_feed(
            feed_id=request.feed_id,
            content=request.content,
            username="default"
        )
        
        return SuccessResponse(
            data=result.dict() if hasattr(result, 'dict') else result.__dict__,
            message="发表评论成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发表评论失败: {e}")
        raise HTTPException(
            status_code=500,
            detail="发表评论失败"
        )

if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    uvicorn.run(
        "xiaohongshu_mcp_python.http_server:app",
        host="0.0.0.0",
        port=18060,
        reload=False,
        log_level="info"
    )