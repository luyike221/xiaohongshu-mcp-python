"""LangGraph 状态定义

定义了图运行时的状态结构，使用 TypedDict 和 Annotated 类型
支持消息追加模式和状态管理
"""

from typing import Annotated, Any, Optional, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .models import NextAgent, RouterDecision, TaskContext, TaskStatus


# ============================================================================
# 状态 Reducer 函数
# ============================================================================

def update_task_context(
    current: Optional[TaskContext],
    new: Optional[TaskContext]
) -> Optional[TaskContext]:
    """TaskContext 更新策略
    
    如果新值为 None，保持原值；否则使用新值
    """
    if new is None:
        return current
    return new


def update_decision(
    current: Optional[RouterDecision],
    new: Optional[RouterDecision]
) -> Optional[RouterDecision]:
    """RouterDecision 更新策略"""
    if new is None:
        return current
    return new


def merge_metadata(
    current: dict[str, Any],
    new: dict[str, Any]
) -> dict[str, Any]:
    """合并 metadata 字典"""
    if not current:
        current = {}
    if new:
        current.update(new)
    return current


# ============================================================================
# 主状态定义
# ============================================================================

class AgentState(TypedDict, total=False):
    """Agent 运行状态
    
    这是整个图的共享状态，包含所有节点需要访问和修改的数据
    
    设计原则：
    1. messages 使用 add_messages reducer 支持追加模式
    2. 其他字段使用自定义 reducer 或默认覆盖
    3. 支持可选字段以增强灵活性
    
    Attributes:
        messages: 对话消息历史，支持追加模式
        current_agent: 当前正在执行的 Agent 名称
        decision: Router 的最新决策结果
        task_context: 当前任务的上下文信息
        iteration_count: 当前迭代次数（防止无限循环）
        metadata: 额外的元数据
    """
    
    # 核心字段 - 消息历史（使用 add_messages reducer 实现追加）
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Router 决策相关
    current_agent: str
    decision: Optional[RouterDecision]
    
    # 任务上下文
    task_context: Optional[TaskContext]
    
    # 控制字段
    iteration_count: int
    
    # 元数据（可扩展）
    metadata: dict[str, Any]


# ============================================================================
# 子状态定义（用于特定节点）
# ============================================================================

class RouterInputState(TypedDict):
    """Router 节点的输入状态"""
    messages: Sequence[BaseMessage]
    task_context: Optional[TaskContext]
    metadata: dict[str, Any]


class RouterOutputState(TypedDict):
    """Router 节点的输出状态"""
    messages: Sequence[BaseMessage]
    decision: RouterDecision
    current_agent: str


class AgentInputState(TypedDict):
    """Agent 节点的输入状态"""
    messages: Sequence[BaseMessage]
    decision: RouterDecision
    task_context: Optional[TaskContext]


class AgentOutputState(TypedDict):
    """Agent 节点的输出状态"""
    messages: Sequence[BaseMessage]
    task_context: Optional[TaskContext]


# ============================================================================
# 状态工厂函数
# ============================================================================

def create_initial_state(
    user_message: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None
) -> AgentState:
    """创建初始状态
    
    Args:
        user_message: 可选的初始用户消息
        metadata: 可选的初始元数据
    
    Returns:
        初始化的 AgentState
    """
    from langchain_core.messages import HumanMessage
    
    messages: list[BaseMessage] = []
    if user_message:
        messages.append(HumanMessage(content=user_message))
    
    return AgentState(
        messages=messages,
        current_agent="router",
        decision=None,
        task_context=None,
        iteration_count=0,
        metadata=metadata or {},
    )


def get_last_human_message(state: AgentState) -> Optional[str]:
    """获取最后一条用户消息"""
    from langchain_core.messages import HumanMessage
    
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            return msg.content
    return None


def get_last_ai_message(state: AgentState) -> Optional[str]:
    """获取最后一条 AI 消息"""
    from langchain_core.messages import AIMessage
    
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, AIMessage):
            return msg.content
    return None


def is_task_completed(state: AgentState) -> bool:
    """检查当前任务是否已完成"""
    task_context = state.get("task_context")
    if task_context is None:
        return True
    return task_context.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]


def should_continue(state: AgentState, max_iterations: int = 10) -> bool:
    """判断是否应该继续执行
    
    防止无限循环
    """
    iteration_count = state.get("iteration_count", 0)
    return iteration_count < max_iterations


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 主状态
    "AgentState",
    # 子状态
    "RouterInputState",
    "RouterOutputState",
    "AgentInputState",
    "AgentOutputState",
    # Reducer 函数
    "update_task_context",
    "update_decision",
    "merge_metadata",
    # 工厂函数
    "create_initial_state",
    # 辅助函数
    "get_last_human_message",
    "get_last_ai_message",
    "is_task_completed",
    "should_continue",
]
