"""Agent 模块

包含：
- base: Agent 基类和注册表
- router: 路由 Agent
- xhs: 小红书相关 Agent
"""

from .base import AgentRegistry, BaseAgent
from .router import (
    ROUTER_SYSTEM_PROMPT,
    RouterAgent,
    RouterOutput,
    create_router_agent,
)
from .xhs.xhs_agent import (
    XHSAgentNode,
    create_xhs_agent_node,
    create_xhs_tool,
)

__all__ = [
    # 基类
    "BaseAgent",
    "AgentRegistry",
    # Router
    "RouterAgent",
    "RouterOutput",
    "create_router_agent",
    "ROUTER_SYSTEM_PROMPT",
    # XHS Agent
    "XHSAgentNode",
    "create_xhs_agent_node",
    "create_xhs_tool",
]

