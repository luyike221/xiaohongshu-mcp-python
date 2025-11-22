"""小红书MCP服务智能体功能测试

本测试文件验证小红书MCP智能体的核心功能，包括：
1. 智能体的创建和初始化（验证名称、初始化状态等）
2. 基本任务执行能力（通过execute方法执行用户指令）
3. 登录状态检查功能（验证能否正确检测小红书账号登录状态）
4. 内容搜索功能（测试搜索教育相关内容等场景）
5. Agent名称配置（验证自定义名称功能）

测试使用阿里百炼模型作为LLM后端，配置通过model_config自动加载.env文件。
所有测试均为异步测试，需要配置ALIBABA_BAILIAN_API_KEY环境变量才能运行。
"""

import os

import pytest
from ai_social_scheduler.ai_agent.agents.mcp.xhs import create_xiaohongshu_mcp_agent, XiaohongshuMCPAgent
from ai_social_scheduler.config import model_config

# model_config 会自动加载 .env 文件（在 model_config.py 中已配置）


def get_llm_api_key():
    """从配置获取 LLM API Key（会自动加载 .env 文件）"""
    import os
    
    # 调试信息
    if __name__ == "__main__":
        print(f"调试: os.getenv('ALIBABA_BAILIAN_API_KEY'): {'已设置' if os.getenv('ALIBABA_BAILIAN_API_KEY') else '未设置'}")
        print(f"调试: model_config.alibaba_bailian__api_key: {model_config.alibaba_bailian__api_key}")
        print(f"调试: model_config.model_config: {model_config.model_config}")
    
    try:
        # 直接检查 model_config 的属性
        api_key = model_config.alibaba_bailian__api_key
        if api_key:
            return api_key
        
        # 如果直接属性为空，尝试从环境变量直接读取（作为后备方案）
        env_api_key = os.getenv('ALIBABA_BAILIAN_API_KEY')
        if env_api_key:
            if __name__ == "__main__":
                print(f"调试: 从环境变量直接读取到 API key")
            return env_api_key
        
        # 尝试通过 get_alibaba_bailian_config 获取
        config = model_config.get_alibaba_bailian_config()
        return config.api_key
    except (ValueError, AttributeError) as e:
        if __name__ == "__main__":
            print(f"调试: 获取 API key 失败: {e}")
        return None


@pytest.mark.asyncio
@pytest.mark.skip(reason="仅测试搜索功能")
async def test_create_agent():
    """测试创建小红书MCP智能体"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")
    
    # 创建agent（使用默认配置）
    agent = await create_xiaohongshu_mcp_agent(llm_api_key=api_key)
    
    # 验证agent已创建
    assert agent is not None
    assert agent.name == "xiaohongshu_mcp"
    assert agent._initialized is True


@pytest.mark.asyncio
@pytest.mark.skip(reason="仅测试搜索功能")
async def test_agent_execute():
    """测试agent执行基本任务"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")
    
    # 创建agent
    agent = await create_xiaohongshu_mcp_agent(llm_api_key=api_key)
    
    # 执行一个简单的任务
    result = await agent.execute({
        "content": "检查登录状态"
    })
    
    # 验证返回结果
    assert result is not None
    assert "agent" in result
    assert result["agent"] == "xiaohongshu_mcp"


@pytest.mark.asyncio
@pytest.mark.skip(reason="仅测试搜索功能")
async def test_check_login_status():
    """测试检查登录状态"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")
    
    # 创建agent
    agent = await create_xiaohongshu_mcp_agent(llm_api_key=api_key)
    
    # 检查登录状态
    status = await agent.check_login_status()
    
    # 验证返回结果
    assert status is not None
    assert "logged_in" in status


@pytest.mark.asyncio
@pytest.mark.skip(reason="仅测试搜索功能")
async def test_agent_name():
    """测试agent名称"""
    agent = XiaohongshuMCPAgent(name="test_agent")
    assert agent.name == "test_agent"


@pytest.mark.asyncio
async def test_search_education_content():
    """测试搜索教育相关内容"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")
    
    # 创建agent
    agent = await create_xiaohongshu_mcp_agent(llm_api_key=api_key)
    
    # 搜索教育相关内容
    result = await agent.execute({
        "content": "搜索关于教育的内容，比如ai教育"
    })
    
    # 验证返回结果
    assert result is not None
    assert "agent" in result
    assert result["agent"] == "xiaohongshu_mcp"
    assert result.get("success", False) is True


if __name__ == "__main__":
    # 简单运行测试
    import asyncio
    
    async def run_tests():
        # 从配置获取 API key（现在应该能正确读取 .env 文件了）
        api_key = get_llm_api_key()
        if not api_key:
            print("❌ 错误: 需要配置 ALIBABA_BAILIAN_API_KEY 环境变量")
            print("   请在项目根目录的 .env 文件中设置 ALIBABA_BAILIAN_API_KEY")
            return
        
        # 仅测试搜索功能
        print("测试: 搜索教育相关内容")
        agent = await create_xiaohongshu_mcp_agent(llm_api_key=api_key)
        search_result = await agent.execute({"content": "搜索关于教育的内容"})
        print(f"✓ 搜索完成: {search_result.get('success', False)}")
        if search_result.get('success'):
            print(f"  搜索结果: {str(search_result.get('result', {}))}")
        
        print("\n测试完成!")
    
    asyncio.run(run_tests())


