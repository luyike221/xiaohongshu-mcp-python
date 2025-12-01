"""小红书运营 Agent 主包

主要组件：
- SocialSchedulerGraph: LangGraph 工作流图
- ConversationRunner: 简化的对话运行器
- RouterAgent: 路由决策 Agent
- XHSAgentNode: 小红书内容生成节点
"""

__version__ = "0.1.0"

# 导出核心组件
from .core import (
    AgentState,
    ConversationRunner,
    SocialSchedulerGraph,
    create_graph,
    get_compiled_graph,
)
from .agents import (
    RouterAgent,
    XHSAgentNode,
    create_router_agent,
    create_xhs_agent_node,
)

__all__ = [
    # 版本
    "__version__",
    # 图
    "SocialSchedulerGraph",
    "create_graph",
    "get_compiled_graph",
    # 对话运行器
    "ConversationRunner",
    # 状态
    "AgentState",
    # Agents
    "RouterAgent",
    "XHSAgentNode",
    "create_router_agent",
    "create_xhs_agent_node",
]

