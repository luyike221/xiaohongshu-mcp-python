"""测试小红书 Agent 节点

示例：在上层 Supervisor Agent 中使用小红书节点
"""

import asyncio
from typing import Annotated, Literal
from typing_extensions import TypedDict

import pytest
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages

# 导入节点（可以通过 __init__.py 导入）
from ai_social_scheduler.agent.xhs import create_xhs_agent_node


# ============================================================================
# 定义上层状态
# ============================================================================

class SupervisorState(TypedDict):
    """上层 Supervisor 的状态"""
    messages: Annotated[list[BaseMessage], add_messages]
    next: str  # 下一个要调用的节点


# ============================================================================
# Supervisor 节点：决策路由
# ============================================================================

async def supervisor_node(state: SupervisorState) -> dict:
    """Supervisor 节点，决定调用哪个专业 Agent"""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # 简单的路由逻辑（实际可以用 LLM 决策）
    # 注意：目前只实现了 xhs_agent，其他节点暂时返回结束
    if "小红书" in last_message or "发布" in last_message or "生成" in last_message:
        return {"next": "xhs_agent"}
    elif "研究" in last_message or "调研" in last_message:
        # research_agent 节点尚未实现，暂时返回结束
        return {"next": "__end__"}
    else:
        return {"next": "__end__"}


# ============================================================================
# 路由函数
# ============================================================================

def router(state: SupervisorState) -> Literal["xhs_agent", "__end__"]:
    """根据 supervisor 的决策进行路由"""
    next_node = state.get("next", "__end__")
    if next_node == "xhs_agent":
        return "xhs_agent"
    else:
        return "__end__"


# ============================================================================
# 构建上层图
# ============================================================================

def create_supervisor_workflow():
    """创建 Supervisor 工作流"""
    # 创建各个专业节点
    xhs_agent = create_xhs_agent_node()
    # research_agent = create_research_agent_node()  # 其他节点
    # analysis_agent = create_analysis_agent_node()  # 其他节点
    
    # 构建上层图
    workflow = StateGraph(SupervisorState)
    
    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("xhs_agent", xhs_agent)  # 小红书节点
    # workflow.add_node("research_agent", research_agent)  # 其他节点
    
    # 设置流程
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        router,
        {
            "xhs_agent": "xhs_agent",
            "__end__": END,
        }
    )
    
    # 各专业节点完成后回到 supervisor
    workflow.add_edge("xhs_agent", "supervisor")
    # workflow.add_edge("research_agent", "supervisor")
    
    # 编译
    return workflow.compile()


# ============================================================================
# 使用示例
# ============================================================================

@pytest.mark.asyncio
async def test_xhs_agent_direct():
    """直接测试小红书 Agent 节点"""
    print("=" * 60)
    print("测试 1: 直接调用小红书 Agent 节点")
    print("=" * 60)
    
    xhs_agent = create_xhs_agent_node()
    
    # 创建测试状态
    state = {
        "messages": [
            HumanMessage(content="帮我生成一篇关于咖啡的小红书笔记，需要3张图片")
        ]
    }
    
    try:
        result = await xhs_agent(state)
        print("\n✅ 节点执行成功")
        print(f"返回消息数量: {len(result.get('messages', []))}")
        if result.get("messages"):
            last_message = result["messages"][-1]
            print(f"最后一条消息类型: {type(last_message).__name__}")
            if hasattr(last_message, "content"):
                print(f"消息内容:\n{last_message.content}")
    except Exception as e:
        print(f"\n❌ 节点执行失败: {e}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
async def test_supervisor_workflow():
    """测试 Supervisor 工作流"""
    print("\n" + "=" * 60)
    print("测试 2: Supervisor 工作流（包含路由）")
    print("=" * 60)
    
    app = create_supervisor_workflow()
    
    # 用户请求
    try:
        result = await app.ainvoke({
            "messages": [HumanMessage(content="帮我生成一篇关于咖啡的小红书笔记")]
        })
        
        print("\n✅ 工作流执行成功")
        print(f"消息数量: {len(result.get('messages', []))}")
        
        if result.get("messages"):
            print("\n所有消息:")
            for i, msg in enumerate(result["messages"], 1):
                print(f"\n消息 {i}:")
                print(f"  类型: {type(msg).__name__}")
                if hasattr(msg, "content"):
                    content = msg.content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    print(f"  内容: {content}")
        
        # 打印最后一条消息的完整内容
        if result.get("messages"):
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                print(f"\n最后一条消息的完整内容:\n{last_message.content}")
                
    except Exception as e:
        print(f"\n❌ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()


@pytest.mark.asyncio
async def test_supervisor_routing():
    """测试 Supervisor 路由功能"""
    print("\n" + "=" * 60)
    print("测试 3: Supervisor 路由决策")
    print("=" * 60)
    
    test_cases = [
        ("帮我生成一篇关于咖啡的小红书笔记", "应该路由到 xhs_agent"),
        ("我想研究一下市场趋势", "应该结束（research_agent 未实现）"),
        ("你好", "应该结束"),
    ]
    
    for user_input, expected in test_cases:
        state = {
            "messages": [HumanMessage(content=user_input)],
            "next": ""
        }
        
        result = await supervisor_node(state)
        next_node = result.get("next", "")
        print(f"\n输入: {user_input}")
        print(f"路由到: {next_node}")
        print(f"预期: {expected}")


# 注意：pytest 会自动发现和运行所有 test_* 函数
# 如果需要直接运行，可以使用: pytest tests/integration/test_xhs_agent_node.py

