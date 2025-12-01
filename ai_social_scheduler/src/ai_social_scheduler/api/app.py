"""FastAPI 应用

提供 HTTP 接口来调用 LangGraph
"""

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from ..core import get_compiled_graph
from ..tools.logging import get_logger

logger = get_logger(__name__)

# 全局 checkpointer（用于状态持久化）
_checkpointer: Optional[MemorySaver] = None
_app_instance: Optional[FastAPI] = None


# ============================================================================
# 请求/响应模型
# ============================================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(description="用户消息")
    thread_id: Optional[str] = Field(
        default=None,
        description="对话线程 ID，如果不提供则自动生成"
    )
    reset: bool = Field(
        default=False,
        description="是否重置对话（创建新的 thread_id）"
    )


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str = Field(description="AI 回复")
    thread_id: str = Field(description="对话线程 ID")
    message_count: int = Field(description="当前对话消息数")




# ============================================================================
# FastAPI 应用
# ============================================================================

def create_app(
    checkpointer: Optional[MemorySaver] = None,
    enable_cors: bool = True,
    title: str = "小红书运营 Agent API",
    version: str = "0.1.0",
) -> FastAPI:
    """创建 FastAPI 应用
    
    Args:
        checkpointer: 状态检查点器（用于持久化）
        enable_cors: 是否启用 CORS
        title: API 标题
        version: API 版本
    
    Returns:
        FastAPI 应用实例
    """
    global _checkpointer, _app_instance
    
    # 初始化 checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()
    _checkpointer = checkpointer
    
    # 创建 FastAPI 应用
    app = FastAPI(
        title=title,
        version=version,
        description="基于 LangGraph 的小红书运营 Agent API",
    )
    
    # 启用 CORS
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # ========================================================================
    # 路由定义
    # ========================================================================
    
    @app.post("/api/v1/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """聊天接口
        
        发送消息并获取 AI 回复
        
        Example:
            POST /api/v1/chat
            {
                "message": "帮我写一篇小红书",
                "thread_id": "user_123"  # 可选
            }
        """
        try:
            # 获取或创建 thread_id
            thread_id = request.thread_id
            if not thread_id or request.reset:
                thread_id = str(uuid.uuid4())
                logger.info(f"New conversation started", thread_id=thread_id)
            
            # 获取编译后的图
            app_graph = get_compiled_graph(checkpointer=_checkpointer)
            
            # 获取当前状态
            current_state = await app_graph.aget_state(
                {"configurable": {"thread_id": thread_id}}
            )
            
            if current_state.values:
                # 继续现有对话 - 添加新消息
                await app_graph.aupdate_state(
                    {"configurable": {"thread_id": thread_id}},
                    {"messages": [HumanMessage(content=request.message)]}
                )
                # 继续执行
                result = await app_graph.ainvoke(
                    None,
                    config={"configurable": {"thread_id": thread_id}}
                )
            else:
                # 新对话
                result = await app_graph.ainvoke(
                    {"messages": [HumanMessage(content=request.message)]},
                    config={"configurable": {"thread_id": thread_id}}
                )
            
            # 提取 AI 回复
            messages = result.get("messages", [])
            response_text = ""
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content:
                    response_text = msg.content
                    break
            
            if not response_text:
                response_text = "抱歉，我没有收到回复。"
            
            logger.info(
                f"Chat completed",
                thread_id=thread_id,
                message_length=len(request.message),
                response_length=len(response_text)
            )
            
            return ChatResponse(
                response=response_text,
                thread_id=thread_id,
                message_count=len(messages)
            )
            
        except Exception as e:
            logger.error(f"Chat failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"处理消息时出错: {str(e)}")
    
    _app_instance = app
    return app


# ============================================================================
# 便捷函数
# ============================================================================

def get_app() -> FastAPI:
    """获取 FastAPI 应用实例"""
    if _app_instance is None:
        return create_app()
    return _app_instance


# 创建默认应用实例
app = create_app()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "app",
    "create_app",
    "get_app",
    "ChatRequest",
    "ChatResponse",
]

