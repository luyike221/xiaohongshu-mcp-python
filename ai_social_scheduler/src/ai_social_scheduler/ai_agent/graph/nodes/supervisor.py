"""协调节点"""

from typing import Dict, Any

from ..state import AgentState


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """协调节点 - 决定路由到哪个 Agent"""
    # TODO: 实现协调逻辑
    return {"current_agent": "content"}

