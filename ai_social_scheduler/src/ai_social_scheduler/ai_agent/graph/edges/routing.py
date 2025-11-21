"""路由决策"""

from typing import Literal

from ..state import AgentState


def route_decision(state: AgentState) -> Literal["content", "interaction", "analysis"]:
    """路由决策函数"""
    # TODO: 实现路由决策逻辑
    current_agent = state.get("current_agent", "content")
    return current_agent  # type: ignore

