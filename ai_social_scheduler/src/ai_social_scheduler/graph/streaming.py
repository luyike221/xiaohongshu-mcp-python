"""图执行流式接口 - 实时展示处理流程

支持 SSE (Server-Sent Events) 实时推送 Graph 执行进度

重构说明：
- 子图已直接作为节点添加到主图
- LangGraph 原生支持子图流式输出
- 简化了事件处理逻辑
"""

import json
from typing import Any, AsyncIterator, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 事件类型定义
# ============================================================================

class StreamEventType:
    """流式事件类型"""
    STARTED = "started"                    # 开始执行
    NODE_START = "node_start"              # 节点开始
    NODE_OUTPUT = "node_output"            # 节点输出
    NODE_END = "node_end"                  # 节点结束
    ROUTING = "routing"                    # 路由中
    MESSAGE = "message"                    # 消息
    ERROR = "error"                        # 错误
    COMPLETED = "completed"                # 完成
    METADATA = "metadata"                  # 元数据
    # 子图相关事件 - LangGraph 原生支持
    SUBGRAPH_START = "subgraph_start"      # 子图开始
    SUBGRAPH_NODE_START = "subgraph_node_start"  # 子图节点开始
    SUBGRAPH_NODE_OUTPUT = "subgraph_node_output"  # 子图节点输出
    SUBGRAPH_NODE_END = "subgraph_node_end"  # 子图节点结束
    SUBGRAPH_END = "subgraph_end"          # 子图结束


# ============================================================================
# 流式执行器
# ============================================================================

class StreamingGraphExecutor:
    """流式图执行器
    
    重构后：利用 LangGraph 原生子图流式支持
    """
    
    def __init__(self, compiled_graph):
        """初始化流式执行器
        
        Args:
            compiled_graph: 编译后的图
        """
        self.graph = compiled_graph
        logger.info("StreamingGraphExecutor initialized (with subgraph support)")
    
    async def stream(
        self,
        user_input: str,
        thread_id: str,
        user_id: Optional[str] = None,
        messages: Optional[list[BaseMessage]] = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """流式执行图并逐步返回事件
        
        Args:
            user_input: 用户输入
            thread_id: 会话 ID
            user_id: 用户 ID
            messages: 历史消息（可选）
        
        Yields:
            事件字典 {"type": "event_type", "data": {...}}
        """
        logger.info(
            "Starting streaming execution",
            thread_id=thread_id,
            input_length=len(user_input)
        )
        
        # 发送开始事件
        yield {
            "type": StreamEventType.STARTED,
            "data": {
                "thread_id": thread_id,
                "user_id": user_id or "",
                "timestamp": self._get_timestamp(),
            }
        }
        
        try:
            # 构建运行配置
            config = {
                "configurable": {
                    "thread_id": thread_id,
                }
            }
            
            # 获取当前状态
            current_state = await self.graph.aget_state(config)
            
            # 构建输入
            if current_state.values:
                # 继续现有对话
                logger.info("Continuing existing conversation")
                
                existing_messages = current_state.values.get("messages", [])
                existing_messages.append(HumanMessage(content=user_input))
                
                input_data = {
                    "messages": existing_messages,
                    "thread_id": current_state.values.get("thread_id", thread_id),
                    "user_id": current_state.values.get("user_id", user_id or ""),
                    "iteration_count": 0,
                    "metadata": current_state.values.get("metadata", {}),
                    "task": None,
                }
            else:
                # 新对话
                logger.info("Starting new conversation")
                
                initial_messages = messages or []
                initial_messages.append(HumanMessage(content=user_input))
                
                input_data = {
                    "messages": initial_messages,
                    "thread_id": thread_id,
                    "user_id": user_id or "",
                    "iteration_count": 0,
                    "metadata": {},
                }
            
            # 流式执行图 - LangGraph 自动处理子图流式输出
            # 使用 stream_mode="updates" 获取每个节点的更新
            # subgraphs=True 启用子图流式输出
            async for event in self.graph.astream(
                input_data, 
                config, 
                stream_mode="updates",
                subgraphs=True  # 关键：启用子图流式输出
            ):
                # 调试：记录原始事件格式
                logger.debug(
                    "Received raw event",
                    event_type=type(event).__name__,
                    event_repr=repr(event)[:500],  # 限制长度避免日志过长
                    event_str=str(event)[:500],
                    is_dict=isinstance(event, dict),
                    is_tuple=isinstance(event, tuple),
                    is_list=isinstance(event, list),
                )
                
                # 处理事件并转换为前端友好格式
                for processed_event in self._process_graph_event(event):
                    yield processed_event
            
            # 发送完成事件
            yield {
                "type": StreamEventType.COMPLETED,
                "data": {
                    "thread_id": thread_id,
                    "timestamp": self._get_timestamp(),
                }
            }
            
            logger.info("Streaming execution completed", thread_id=thread_id)
            
        except Exception as e:
            logger.error(
                "Streaming execution failed",
                error=str(e),
                error_type=type(e).__name__,
                thread_id=thread_id,
                exc_info=True,
            )
            yield {
                "type": StreamEventType.ERROR,
                "data": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": self._get_timestamp(),
                }
            }
    
    def _process_graph_event(self, event: dict) -> list[dict[str, Any]]:
        """处理图事件并转换为前端友好格式
        
        LangGraph 的 stream_mode="updates" 返回格式:
        - 主图节点: {"node_name": node_output}
        - 子图节点: {"parent_node:subgraph_node": subgraph_output}
        
        Args:
            event: LangGraph 原始事件
        
        Returns:
            处理后的事件列表
        """
        results = []
        
        # 调试：详细记录事件信息
        logger.debug(
            "Processing graph event",
            event_type=type(event).__name__,
            event_id=id(event),
            has_items=hasattr(event, 'items'),
            has_keys=hasattr(event, 'keys'),
            has_getitem=hasattr(event, '__getitem__'),
        )
        
        # 转换事件格式：LangGraph 返回元组格式 ((node_path_tuple), output_dict)
        # 需要转换为字典格式 {node_name: node_output}
        if isinstance(event, tuple) and len(event) == 2:
            # 格式: (('xhs_workflow:...', 'generate_content:...'), {'model': {...}})
            node_path, node_output = event
            
            # 组合节点路径为节点名（用于识别子图节点）
            if isinstance(node_path, tuple):
                node_name = ":".join(str(p) for p in node_path)
            else:
                node_name = str(node_path)
            
            # 确保输出是字典
            if not isinstance(node_output, dict):
                node_output = {"output": node_output}
            
            event = {node_name: node_output}
            logger.debug(f"Converted tuple event: {node_name}")
        elif not isinstance(event, dict):
            # 未知格式，返回错误
            logger.error(f"Unexpected event type: {type(event).__name__}")
            results.append({
                "type": StreamEventType.ERROR,
                "data": {
                    "error": f"Unexpected event type: {type(event).__name__}",
                    "event_type": type(event).__name__,
                    "timestamp": self._get_timestamp(),
                }
            })
            return results
        
        # 处理事件中的每个节点
        try:
            for node_name, node_output in event.items():
                
                # 检查是否是子图节点（包含多个 ":"，格式为 "parent:...:subgraph:..."）
                if node_name.count(":") >= 2:
                    # 子图节点格式: "xhs_workflow:...:generate_content:..."
                    # 提取父节点名和子图节点名（去掉ID部分）
                    parts = node_name.split(":")
                    parent_node = parts[0]  # 例如: "xhs_workflow"
                    # 找到子图节点名（通常是第二个或第三个部分）
                    subgraph_node = parts[2] if len(parts) > 2 else parts[1]  # 例如: "generate_content" 或 "publish"
                    
                    # 子图节点开始
                    results.append({
                        "type": StreamEventType.SUBGRAPH_NODE_START,
                        "data": {
                            "parent_node": parent_node,
                            "subgraph_node": subgraph_node,
                            "node": node_name,  # 保留完整节点名用于调试
                            "timestamp": self._get_timestamp(),
                        }
                    })
                    
                    # 提取子图节点输出信息
                    event_data = self._extract_node_info(node_name, node_output)
                    event_data["parent_node"] = parent_node
                    event_data["subgraph_node"] = subgraph_node
                    
                    # 子图节点输出
                    results.append({
                        "type": StreamEventType.SUBGRAPH_NODE_OUTPUT,
                        "data": event_data
                    })
                    
                    # 子图节点结束
                    results.append({
                        "type": StreamEventType.SUBGRAPH_NODE_END,
                        "data": {
                            "parent_node": parent_node,
                            "subgraph_node": subgraph_node,
                            "timestamp": self._get_timestamp(),
                        }
                    })
                else:
                    # 主图节点
                    # 节点开始
                    results.append({
                        "type": StreamEventType.NODE_START,
                        "data": {
                            "node": node_name,
                            "timestamp": self._get_timestamp(),
                        }
                    })
                    
                    # 提取节点输出信息
                    event_data = self._extract_node_info(node_name, node_output)
                    
                    # 节点输出
                    results.append({
                        "type": StreamEventType.NODE_OUTPUT,
                        "data": event_data
                    })
                    
                    # 节点结束
                    results.append({
                        "type": StreamEventType.NODE_END,
                        "data": {
                            "node": node_name,
                            "timestamp": self._get_timestamp(),
                        }
                    })
        except Exception as e:
            logger.error(
                "Error processing graph event",
                error=str(e),
                error_type=type(e).__name__,
                event_type=type(event).__name__,
                event_keys=list(event.keys())[:10] if isinstance(event, dict) else "N/A",
                exc_info=True,
            )
            # 返回错误事件
            results.append({
                "type": StreamEventType.ERROR,
                "data": {
                    "error": f"Failed to process event: {str(e)}",
                    "error_type": type(e).__name__,
                    "timestamp": self._get_timestamp(),
                }
            })
        
        return results
    
    def _extract_node_info(
        self,
        node_name: str,
        node_output: dict[str, Any]
    ) -> dict[str, Any]:
        """从节点输出中提取关键信息
        
        Args:
            node_name: 节点名称
            node_output: 节点输出
        
        Returns:
            提取的信息
        """
        # 确保 node_output 是字典
        if not isinstance(node_output, dict):
            if hasattr(node_output, '__dict__'):
                node_output = node_output.__dict__
            else:
                node_output = {"output": node_output}
        
        data = {
            "node": node_name,
            "timestamp": self._get_timestamp(),
        }
        
        # 提取任务信息
        task = node_output.get("task")
        if task:
            data["task"] = {
                "task_id": task.task_id,
                "task_type": task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                "target_nodes": task.target_nodes,
                "progress": self._get_task_progress(task),
            }
        
        # 提取消息信息
        messages = node_output.get("messages", [])
        if messages:
            # 获取最后一条消息
            last_message = messages[-1] if messages else None
            if last_message:
                data["message"] = {
                    "type": last_message.type if hasattr(last_message, 'type') else "unknown",
                    "content": last_message.content if hasattr(last_message, 'content') else "",
                }
        
        # 提取元数据
        metadata = node_output.get("metadata", {})
        if metadata:
            data["metadata"] = metadata
        
        return data
    
    def _get_task_progress(self, task) -> dict[str, Any]:
        """获取任务进度信息
        
        Args:
            task: 任务对象
        
        Returns:
            进度信息
        """
        return {
            "current_node": task.current_node,
            "route_path": task.route_path,
            "retry_count": task.retry_count,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# ============================================================================
# SSE 格式化工具
# ============================================================================

class SSEFormatter:
    """SSE 格式化工具
    
    将事件转换为 SSE 格式
    """
    
    @staticmethod
    def format(event: dict[str, Any]) -> str:
        """格式化事件为 SSE 格式
        
        SSE 格式:
        event: event_type
        data: json_data
        
        Args:
            event: 事件字典
        
        Returns:
            SSE 格式字符串
        """
        event_type = event.get("type", "message")
        event_data = event.get("data", {})
        
        # 确保数据可以被 JSON 序列化
        try:
            json_data = json.dumps(event_data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize event data: {e}")
            json_data = json.dumps({"error": "Failed to serialize data"})
        
        # SSE 格式
        return f"event: {event_type}\ndata: {json_data}\n\n"
    
    @staticmethod
    def format_heartbeat() -> str:
        """格式化心跳事件"""
        return ": heartbeat\n\n"


# ============================================================================
# FastAPI SSE 响应包装器
# ============================================================================

async def stream_graph_sse(
    executor: StreamingGraphExecutor,
    user_input: str,
    thread_id: str,
    user_id: Optional[str] = None,
) -> AsyncIterator[str]:
    """FastAPI SSE 响应包装器
    
    将流式事件转换为 SSE 格式并发送
    
    Args:
        executor: 流式执行器
        user_input: 用户输入
        thread_id: 会话 ID
        user_id: 用户 ID
    
    Yields:
        SSE 格式的字符串
    """
    formatter = SSEFormatter()
    
    try:
        async for event in executor.stream(user_input, thread_id, user_id):
            # 转换为 SSE 格式
            sse_data = formatter.format(event)
            yield sse_data
    except Exception as e:
        # 发送错误事件
        error_event = {
            "type": StreamEventType.ERROR,
            "data": {"error": str(e)}
        }
        yield formatter.format(error_event)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "StreamEventType",
    "StreamingGraphExecutor",
    "SSEFormatter",
    "stream_graph_sse",
]
