"""小红书MCP服务智能体功能测试"""

import pytest
from ai_social_scheduler.ai_agent.agents.mcp.xhs import create_xiaohongshu_mcp_agent, XiaohongshuMCPAgent


@pytest.mark.asyncio
async def test_create_agent():
    """测试创建小红书MCP智能体"""
    # 创建agent（使用默认配置）
    agent = await create_xiaohongshu_mcp_agent()
    
    # 验证agent已创建
    assert agent is not None
    assert agent.name == "xiaohongshu_mcp"
    assert agent._initialized is True


@pytest.mark.asyncio
async def test_agent_execute():
    """测试agent执行基本任务"""
    # 创建agent
    agent = await create_xiaohongshu_mcp_agent()
    
    # 执行一个简单的任务
    result = await agent.execute({
        "content": "检查登录状态"
    })
    
    # 验证返回结果
    assert result is not None
    assert "agent" in result
    assert result["agent"] == "xiaohongshu_mcp"


@pytest.mark.asyncio
async def test_check_login_status():
    """测试检查登录状态"""
    # 创建agent
    agent = await create_xiaohongshu_mcp_agent()
    
    # 检查登录状态
    status = await agent.check_login_status()
    
    # 验证返回结果
    assert status is not None
    assert "logged_in" in status


@pytest.mark.asyncio
async def test_agent_name():
    """测试agent名称"""
    agent = XiaohongshuMCPAgent(name="test_agent")
    assert agent.name == "test_agent"


if __name__ == "__main__":
    # 简单运行测试
    import asyncio
    
    async def run_tests():
        print("测试1: 创建agent")
        agent = await create_xiaohongshu_mcp_agent()
        print(f"✓ Agent创建成功: {agent.name}")
        
        print("\n测试2: 检查登录状态")
        status = await agent.check_login_status()
        print(f"✓ 登录状态检查完成: {status}")
        
        print("\n测试3: 执行任务")
        result = await agent.execute({"content": "测试任务"})
        print(f"✓ 任务执行完成: {result.get('success', False)}")
        
        print("\n所有测试完成!")
    
    asyncio.run(run_tests())


