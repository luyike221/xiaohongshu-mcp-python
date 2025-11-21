"""主工作流定义"""

from typing import Any, Dict

from langgraph.graph import StateGraph

from .state import AgentState


def create_workflow() -> StateGraph:
    """创建主工作流图"""
    # TODO: 实现工作流图构建逻辑
    workflow = StateGraph(AgentState)
    return workflow.compile()


async def run_workflow(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """运行工作流"""
    workflow = create_workflow()
    result = await workflow.ainvoke(initial_state)
    return result

