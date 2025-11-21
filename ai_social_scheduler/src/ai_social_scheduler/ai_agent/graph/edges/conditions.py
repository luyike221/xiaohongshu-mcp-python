"""条件判断"""

from ..state import AgentState


def should_continue(state: AgentState) -> bool:
    """判断是否继续执行"""
    # TODO: 实现条件判断逻辑
    return state.get("status") != "completed"


def has_error(state: AgentState) -> bool:
    """判断是否有错误"""
    return state.get("error") is not None

