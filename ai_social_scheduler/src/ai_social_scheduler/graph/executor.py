"""图执行器 - 执行 LangGraph

重构核心：封装图的执行逻辑
"""

from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 图执行器
# ============================================================================

class GraphExecutor:
    """图执行器 - 简化图的执行
    
    核心职责：
    1. 执行图
    2. 管理会话状态
    3. 处理中断和恢复
    4. 提取响应
    """
    
    def __init__(self, compiled_graph):
        """初始化图执行器
        
        Args:
            compiled_graph: 编译后的图
        """
        self.graph = compiled_graph
        logger.info("GraphExecutor initialized")
    
    async def invoke(
        self,
        user_input: str,
        thread_id: str,
        user_id: Optional[str] = None,
        messages: Optional[list[BaseMessage]] = None,
    ) -> str:
        """执行图并返回响应
        
        Args:
            user_input: 用户输入
            thread_id: 会话 ID
            user_id: 用户 ID
            messages: 历史消息（可选）
        
        Returns:
            AI 响应内容
        """
        logger.info(
            "Invoking graph",
            thread_id=thread_id,
            input_length=len(user_input)
        )
        
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
            # 继续现有对话 - 获取历史消息并添加新消息
            logger.info("Continuing existing conversation")
            
            # 获取现有消息
            existing_messages = current_state.values.get("messages", [])
            existing_messages.append(HumanMessage(content=user_input))
            
            # 重新执行（从 START 开始，这样会重新路由）
            result = await self.graph.ainvoke(
                {
                    "messages": existing_messages,
                    "thread_id": current_state.values.get("thread_id", thread_id),
                    "user_id": current_state.values.get("user_id", user_id or ""),
                    "iteration_count": 0,  # 重置迭代计数
                    "metadata": current_state.values.get("metadata", {}),
                    "task": None,  # 清空任务，让 router_node 创建新任务
                },
                config
            )
        else:
            # 新对话
            logger.info("Starting new conversation")
            
            initial_messages = messages or []
            initial_messages.append(HumanMessage(content=user_input))
            
            result = await self.graph.ainvoke(
                {
                    "messages": initial_messages,
                    "thread_id": thread_id,
                    "user_id": user_id or "",
                    "iteration_count": 0,
                    "metadata": {},
                },
                config
            )
        
        # 提取响应
        response = self._extract_response(result)
        
        logger.info(
            "Graph execution completed",
            thread_id=thread_id,
            response_length=len(response)
        )
        
        return response
    
    def _extract_response(self, result: dict[str, Any]) -> str:
        """从结果中提取响应"""
        messages = result.get("messages", [])
        
        # 从后往前查找最后一条 AI 消息
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
        
        return "无响应"
    
    async def get_history(self, thread_id: str) -> list[BaseMessage]:
        """获取对话历史
        
        Args:
            thread_id: 会话 ID
        
        Returns:
            消息列表
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = await self.graph.aget_state(config)
        
        if state.values:
            return state.values.get("messages", [])
        
        return []
    
    async def reset(self, thread_id: str):
        """重置会话
        
        Args:
            thread_id: 会话 ID
        """
        # LangGraph 的 MemorySaver 不直接支持删除
        # 这里记录日志，实际清理需要重新初始化
        logger.info(f"Session reset requested: {thread_id}")


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "GraphExecutor",
]

