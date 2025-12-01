"""核心模块

包含：
- models: 数据模型定义
- state: LangGraph 状态定义
- graph: LangGraph 图定义
"""

from .models import (
    AgentConfig,
    GraphConfig,
    IntentType,
    NextAgent,
    RouterDecision,
    TaskContext,
    TaskStatus,
)
from .state import (
    AgentInputState,
    AgentOutputState,
    AgentState,
    RouterInputState,
    RouterOutputState,
    create_initial_state,
    get_last_ai_message,
    get_last_human_message,
    is_task_completed,
    merge_metadata,
    should_continue,
    update_decision,
    update_task_context,
)
from .graph import (
    ConversationRunner,
    MAX_ITERATIONS,
    NODE_ROUTER,
    NODE_WAIT,
    NODE_XHS_AGENT,
    SocialSchedulerGraph,
    create_graph,
    get_compiled_graph,
    route_from_agent,
    route_from_router,
)

__all__ = [
    # 枚举
    "NextAgent",
    "TaskStatus",
    "IntentType",
    # 模型
    "RouterDecision",
    "TaskContext",
    "AgentConfig",
    "GraphConfig",
    # 状态
    "AgentState",
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
    # 图相关
    "NODE_ROUTER",
    "NODE_XHS_AGENT",
    "NODE_WAIT",
    "MAX_ITERATIONS",
    "SocialSchedulerGraph",
    "create_graph",
    "get_compiled_graph",
    "route_from_router",
    "route_from_agent",
    "ConversationRunner",
]

