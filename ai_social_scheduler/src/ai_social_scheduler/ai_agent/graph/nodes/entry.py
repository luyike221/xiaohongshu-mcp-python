"""入口路由节点"""

from typing import Dict, Any

from ..state import AgentState


async def entry_node(state: AgentState) -> Dict[str, Any]:
    """入口路由节点"""
    # TODO: 实现入口路由逻辑
    return {"current_agent": "supervisor"}

