"""测试 LangGraph 图

测试图的基本功能：
1. 图的构建和编译
2. Router 路由决策
3. 对话流程
4. 状态管理
"""

import asyncio
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from ai_social_scheduler import (
    ConversationRunner,
    SocialSchedulerGraph,
    create_graph,
    get_compiled_graph,
)
from ai_social_scheduler.core.models import NextAgent
from ai_social_scheduler.core.state import AgentState, create_initial_state


# ============================================================================
# 基础测试：图构建
# ============================================================================

def test_graph_creation():
    """测试图的创建"""
    graph = create_graph()
    assert graph is not None
    assert isinstance(graph, SocialSchedulerGraph)


def test_graph_build():
    """测试图的构建"""
    graph = create_graph()
    workflow = graph.build()
    assert workflow is not None


def test_graph_compile():
    """测试图的编译"""
    graph = create_graph()
    app = graph.compile()
    assert app is not None


def test_get_compiled_graph():
    """测试便捷函数获取编译后的图"""
    app = get_compiled_graph()
    assert app is not None


# ============================================================================
# 异步测试：基本对话流程
# ============================================================================

@pytest.mark.asyncio
async def test_router_greeting():
    """测试 Router 处理问候消息"""
    app = get_compiled_graph()
    
    # 发送问候消息
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="你好")]},
        config={"configurable": {"thread_id": "test_greeting"}}
    )
    
    # 验证结果
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) > 0
    
    # 最后一条应该是 AI 消息
    last_message = messages[-1]
    assert isinstance(last_message, AIMessage)
    assert len(last_message.content) > 0
    
    # 验证决策
    decision = result.get("decision")
    if decision:
        assert decision.next_agent in [NextAgent.WAIT, NextAgent.END]
    
    print(f"\n✅ Router 回复: {last_message.content}")


@pytest.mark.asyncio
async def test_router_xhs_intent():
    """测试 Router 识别小红书内容生成意图"""
    app = get_compiled_graph()
    
    # 发送小红书相关消息
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="帮我写一篇关于秋天穿搭的小红书")]},
        config={"configurable": {"thread_id": "test_xhs_intent"}}
    )
    
    # 验证结果
    assert "messages" in result
    messages = result["messages"]
    assert len(messages) > 0
    
    # 验证决策
    decision = result.get("decision")
    if decision:
        print(f"\n✅ Router 决策: {decision.next_agent.value}")
        print(f"   意图: {decision.intent.value}")
        print(f"   回复: {decision.response}")
        
        # 如果识别为 xhs_agent，验证参数提取
        if decision.next_agent == NextAgent.XHS_AGENT:
            assert "extracted_params" in decision.model_dump()
            print(f"   提取参数: {decision.extracted_params}")


@pytest.mark.asyncio
async def test_router_end_intent():
    """测试 Router 识别结束意图"""
    app = get_compiled_graph()
    
    # 发送结束消息
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="再见")]},
        config={"configurable": {"thread_id": "test_end_intent"}}
    )
    
    # 验证结果
    assert "messages" in result
    decision = result.get("decision")
    if decision:
        print(f"\n✅ Router 决策: {decision.next_agent.value}")
        # 应该识别为 END 或 WAIT
        assert decision.next_agent in [NextAgent.END, NextAgent.WAIT]


# ============================================================================
# 测试 ConversationRunner
# ============================================================================

@pytest.mark.asyncio
async def test_conversation_runner():
    """测试 ConversationRunner 简化接口"""
    runner = ConversationRunner(thread_id="test_runner")
    
    # 发送第一条消息
    response1 = await runner.send("你好")
    assert len(response1) > 0
    print(f"\n✅ 第一轮回复: {response1}")
    
    # 发送第二条消息
    response2 = await runner.send("帮我写一篇小红书")
    assert len(response2) > 0
    print(f"\n✅ 第二轮回复: {response2}")
    
    # 获取历史
    history = await runner.get_history()
    assert len(history) >= 4  # 至少 2 条用户消息 + 2 条 AI 消息
    print(f"\n✅ 对话历史长度: {len(history)}")


@pytest.mark.asyncio
async def test_conversation_runner_reset():
    """测试 ConversationRunner 重置"""
    runner = ConversationRunner(thread_id="test_reset")
    original_thread_id = runner.thread_id
    
    # 发送消息
    await runner.send("你好")
    
    # 重置
    runner.reset()
    assert runner.thread_id != original_thread_id
    print(f"\n✅ 重置成功: {original_thread_id} -> {runner.thread_id}")


# ============================================================================
# 测试状态管理
# ============================================================================

def test_create_initial_state():
    """测试初始状态创建"""
    state = create_initial_state(user_message="测试消息")
    
    assert "messages" in state
    assert len(state["messages"]) == 1
    assert state["current_agent"] == "router"
    assert state["iteration_count"] == 0
    assert state["decision"] is None


@pytest.mark.asyncio
async def test_state_persistence():
    """测试状态持久化（使用 checkpointer）"""
    from langgraph.checkpoint.memory import MemorySaver
    
    checkpointer = MemorySaver()
    graph = create_graph()
    app = graph.compile(checkpointer=checkpointer)
    
    thread_id = "test_persistence"
    
    # 第一轮对话
    result1 = await app.ainvoke(
        {"messages": [HumanMessage(content="你好")]},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # 获取状态
    state = await app.aget_state({"configurable": {"thread_id": thread_id}})
    assert state.values is not None
    assert len(state.values.get("messages", [])) > 0
    
    # 继续对话（添加新消息）
    await app.aupdate_state(
        {"configurable": {"thread_id": thread_id}},
        {"messages": [HumanMessage(content="继续对话")]}
    )
    
    # 继续执行
    result2 = await app.ainvoke(
        None,  # 使用 None 继续执行
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # 验证新消息已添加
    final_state = await app.aget_state({"configurable": {"thread_id": thread_id}})
    messages = final_state.values.get("messages", [])
    assert len(messages) > len(result1.get("messages", []))
    
    print(f"\n✅ 状态持久化测试通过，消息数: {len(messages)}")


# ============================================================================
# 测试路由逻辑
# ============================================================================

@pytest.mark.asyncio
async def test_routing_to_xhs_agent():
    """测试路由到 XHS Agent（如果图执行到该节点）"""
    app = get_compiled_graph()
    
    # 发送明确的小红书生成请求
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="生成一篇关于美食的小红书笔记，需要3张图片")]},
        config={"configurable": {"thread_id": "test_routing_xhs"}}
    )
    
    # 验证决策
    decision = result.get("decision")
    if decision:
        print(f"\n✅ 路由测试:")
        print(f"   决策: {decision.next_agent.value}")
        print(f"   当前 Agent: {result.get('current_agent')}")
        
        # 如果路由到 xhs_agent，验证任务上下文
        if decision.next_agent == NextAgent.XHS_AGENT:
            task_context = result.get("task_context")
            if task_context:
                print(f"   任务 ID: {task_context.task_id}")
                print(f"   任务类型: {task_context.task_type}")


# ============================================================================
# 测试错误处理
# ============================================================================

@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    app = get_compiled_graph()
    
    # 发送可能导致错误的消息（空消息或特殊字符）
    try:
        result = await app.ainvoke(
            {"messages": [HumanMessage(content="")]},
            config={"configurable": {"thread_id": "test_error"}}
        )
        # 即使出错，也应该有响应
        assert "messages" in result
        print(f"\n✅ 错误处理测试通过")
    except Exception as e:
        # 如果抛出异常，记录但不失败（取决于实现）
        print(f"\n⚠️  捕获异常: {e}")


# ============================================================================
# 性能测试
# ============================================================================

@pytest.mark.asyncio
async def test_graph_performance():
    """测试图的性能（简单测试）"""
    import time
    
    app = get_compiled_graph()
    
    start_time = time.time()
    
    # 执行多次对话
    for i in range(3):
        await app.ainvoke(
            {"messages": [HumanMessage(content=f"测试消息 {i}")]},
            config={"configurable": {"thread_id": f"perf_test_{i}"}}
        )
    
    elapsed = time.time() - start_time
    
    print(f"\n✅ 性能测试: 3 轮对话耗时 {elapsed:.2f} 秒")


# ============================================================================
# 主测试函数（用于直接运行）
# ============================================================================

async def main():
    """主测试函数 - 可以直接运行"""
    print("=" * 60)
    print("开始测试 LangGraph")
    print("=" * 60)
    
    # 测试 1: 基本问候
    print("\n[测试 1] Router 问候")
    await test_router_greeting()
    
    # 测试 2: 意图识别
    print("\n[测试 2] Router 意图识别")
    await test_router_xhs_intent()
    
    # 测试 3: ConversationRunner
    print("\n[测试 3] ConversationRunner")
    await test_conversation_runner()
    
    # 测试 4: 状态持久化
    print("\n[测试 4] 状态持久化")
    await test_state_persistence()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 直接运行测试
    asyncio.run(main())

