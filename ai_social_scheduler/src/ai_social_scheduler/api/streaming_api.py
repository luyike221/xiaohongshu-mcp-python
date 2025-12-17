"""流式 API 端点 - 实时展示 Graph 处理流程

提供 SSE (Server-Sent Events) 接口，让前端实时看到处理进度
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ..graph.streaming import StreamingGraphExecutor, stream_graph_sse
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 路由器
# ============================================================================

def create_streaming_router(
    executor: StreamingGraphExecutor,
) -> APIRouter:
    """创建流式 API 路由器
    
    Args:
        executor: 流式图执行器
    
    Returns:
        FastAPI 路由器
    """
    router = APIRouter(prefix="/api/v1", tags=["streaming"])
    
    @router.get("/chat/stream")
    async def chat_stream(
        message: str = Query(..., description="用户消息"),
        thread_id: Optional[str] = Query(None, description="会话ID（可选，不提供则自动生成）"),
        user_id: Optional[str] = Query(None, description="用户ID（可选）"),
    ):
        """流式聊天接口（SSE）
        
        实时推送 Graph 执行进度
        
        ### 事件类型
        
        **主图事件**：
        - `started`: 开始执行
        - `node_start`: 节点开始执行
        - `node_output`: 节点输出数据
        - `node_end`: 节点执行结束
        - `message`: AI 消息
        - `error`: 错误
        - `completed`: 执行完成
        
        **子图事件**（当节点包含子图时）：
        - `subgraph_start`: 子图开始执行
        - `subgraph_node_start`: 子图节点开始执行
        - `subgraph_node_output`: 子图节点输出数据
        - `subgraph_node_end`: 子图节点执行结束
        - `subgraph_end`: 子图执行完成
        
        ### 使用示例
        
        JavaScript:
        ```javascript
        const eventSource = new EventSource(
            '/api/v1/chat/stream?message=帮我写一篇小红书&thread_id=user_123'
        );
        
        eventSource.addEventListener('node_start', (event) => {
            const data = JSON.parse(event.data);
            console.log('节点开始:', data.node);
        });
        
        eventSource.addEventListener('node_output', (event) => {
            const data = JSON.parse(event.data);
            console.log('节点输出:', data);
        });
        
        // 子图事件监听
        eventSource.addEventListener('subgraph_start', (event) => {
            const data = JSON.parse(event.data);
            console.log('子图开始:', data.subgraph_name, '在节点', data.parent_node);
        });
        
        eventSource.addEventListener('subgraph_node_output', (event) => {
            const data = JSON.parse(event.data);
            console.log('子图节点输出:', data.subgraph_node, '在', data.parent_node);
        });
        
        eventSource.addEventListener('subgraph_end', (event) => {
            const data = JSON.parse(event.data);
            console.log('子图完成:', data.parent_node);
        });
        
        eventSource.addEventListener('completed', (event) => {
            console.log('执行完成');
            eventSource.close();
        });
        
        eventSource.addEventListener('error', (event) => {
            console.error('错误:', event);
            eventSource.close();
        });
        ```
        
        ### 响应格式
        
        SSE 格式，每个事件包含：
        - `event`: 事件类型
        - `data`: JSON 格式的事件数据
        
        Example:
        ```
        event: node_start
        data: {"node": "router", "timestamp": "2025-12-16T10:30:00"}
        
        event: node_output
        data: {"node": "router", "task": {...}, "message": {...}}
        
        event: subgraph_start
        data: {"parent_node": "xhs_agent", "subgraph_name": "xhs_workflow", "timestamp": "2025-12-16T10:30:01"}
        
        event: subgraph_node_start
        data: {"parent_node": "xhs_agent", "subgraph_node": "generate_content", "timestamp": "2025-12-16T10:30:02"}
        
        event: subgraph_node_output
        data: {"parent_node": "xhs_agent", "subgraph_node": "generate_content", "message": {...}}
        
        event: subgraph_node_end
        data: {"parent_node": "xhs_agent", "subgraph_node": "generate_content", "timestamp": "2025-12-16T10:30:03"}
        
        event: subgraph_end
        data: {"parent_node": "xhs_agent", "timestamp": "2025-12-16T10:30:10"}
        
        event: completed
        data: {"thread_id": "user_123", "timestamp": "2025-12-16T10:30:05"}
        ```
        """
        # 生成 thread_id（如果未提供）
        if not thread_id:
            thread_id = str(uuid.uuid4())
            logger.info("Generated new thread_id", thread_id=thread_id)
        
        logger.info(
            "SSE streaming request",
            thread_id=thread_id,
            user_id=user_id,
            message_length=len(message)
        )
        
        # 返回 SSE 流式响应
        return StreamingResponse(
            stream_graph_sse(
                executor=executor,
                user_input=message,
                thread_id=thread_id,
                user_id=user_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )
    
    return router


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "create_streaming_router",
]

