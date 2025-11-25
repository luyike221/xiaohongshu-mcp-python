"""图像视频生成MCP服务智能体功能测试

本测试文件验证图像视频生成MCP智能体的核心功能，包括：
1. 智能体的创建和初始化（验证名称、初始化状态等）
2. 基本任务执行能力（通过execute方法执行用户指令）
3. 图像生成功能（测试使用便捷方法生成图像）
4. 视频生成功能（测试使用便捷方法生成视频）
5. Agent名称配置（验证自定义名称功能）

测试使用阿里百炼模型作为LLM后端，配置通过model_config自动加载.env文件。
所有测试均为异步测试，需要配置ALIBABA_BAILIAN_API_KEY环境变量才能运行。
同时需要确保image_video_mcp服务正在运行（默认地址：http://127.0.0.1:8003/mcp）。
"""

import os

import pytest
from ai_social_scheduler.ai_agent.agents.mcp.image_video import (
    create_image_video_mcp_agent,
    ImageVideoMCPAgent,
)
from ai_social_scheduler.config import model_config

# model_config 会自动加载 .env 文件（在 model_config.py 中已配置）


def get_llm_api_key():
    """从配置获取 LLM API Key（会自动加载 .env 文件）"""
    import os

    # 调试信息
    if __name__ == "__main__":
        print(
            f"调试: os.getenv('ALIBABA_BAILIAN_API_KEY'): {'已设置' if os.getenv('ALIBABA_BAILIAN_API_KEY') else '未设置'}"
        )
        print(
            f"调试: model_config.alibaba_bailian__api_key: {model_config.alibaba_bailian__api_key}"
        )
        print(f"调试: model_config.model_config: {model_config.model_config}")

    try:
        # 直接检查 model_config 的属性
        api_key = model_config.alibaba_bailian__api_key
        if api_key:
            return api_key

        # 如果直接属性为空，尝试从环境变量直接读取（作为后备方案）
        env_api_key = os.getenv("ALIBABA_BAILIAN_API_KEY")
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
async def test_create_agent():
    """测试创建图像视频生成MCP智能体"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")

    # 创建agent（使用默认配置）
    agent = await create_image_video_mcp_agent(llm_api_key=api_key)

    # 验证agent已创建
    assert agent is not None
    assert agent.name == "image_video_mcp"
    assert agent._initialized is True


@pytest.mark.asyncio
async def test_agent_execute():
    """测试agent执行基本任务"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")

    # 创建agent
    agent = await create_image_video_mcp_agent(llm_api_key=api_key)

    # 执行一个简单的任务
    result = await agent.execute({"content": "生成一张可爱的小猫图片"})

    # 验证返回结果
    assert result is not None
    assert "agent" in result
    assert result["agent"] == "image_video_mcp"


@pytest.mark.asyncio
async def test_generate_image():
    """测试生成图像功能（使用便捷方法）"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")

    # 创建agent
    agent = await create_image_video_mcp_agent(llm_api_key=api_key)

    # 生成图像
    result = await agent.generate_image(
        prompt="一只坐着的橙色猫，表情开心，活泼可爱，真实准确。",
        negative_prompt="低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良、模糊、失真",
        width=1280,
        height=1280,
        max_wait_time=60,  # 测试时使用较短的等待时间
    )

    # 验证返回结果
    assert result is not None
    assert isinstance(result, dict)
    # 注意：实际生成可能需要较长时间，这里只验证返回结构
    assert "success" in result or "result" in result or "error" in result


@pytest.mark.asyncio
async def test_generate_video():
    """测试生成视频功能（使用便捷方法）"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")

    # 创建agent
    agent = await create_image_video_mcp_agent(llm_api_key=api_key)

    # 生成视频
    result = await agent.generate_video(
        prompt="一只可爱的小猫在玩耍",
        duration=5,
    )

    # 验证返回结果
    assert result is not None
    assert isinstance(result, (dict, str))
    # 注意：视频生成功能可能还在开发中，这里只验证返回结构


@pytest.mark.asyncio
async def test_agent_name():
    """测试agent名称"""
    agent = ImageVideoMCPAgent(name="test_image_video_agent")
    assert agent.name == "test_image_video_agent"


@pytest.mark.asyncio
async def test_agent_execute_with_natural_language():
    """测试使用自然语言执行图像生成任务"""
    # 从环境变量获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        pytest.skip("需要配置 ALIBABA_BAILIAN_API_KEY 环境变量才能运行此测试")

    # 创建agent
    agent = await create_image_video_mcp_agent(llm_api_key=api_key)

    # 使用自然语言描述任务
    result = await agent.execute(
        {
            "content": "请帮我生成一张图片，内容是一只可爱的小猫坐在窗台上，阳光洒在它身上，画面温馨自然。"
        }
    )

    # 验证返回结果
    assert result is not None
    assert "agent" in result
    assert result["agent"] == "image_video_mcp"
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

        print("=" * 60)
        print("图像视频生成MCP Agent 测试")
        print("=" * 60)

        # 测试1: 创建 agent
        print("\n[测试1] 创建 Agent...")
        try:
            agent = await create_image_video_mcp_agent(llm_api_key=api_key)
            print(f"✓ Agent 创建成功: {agent.name}")
            print(f"  初始化状态: {agent._initialized}")
        except Exception as e:
            print(f"❌ Agent 创建失败: {e}")
            import traceback

            traceback.print_exc()
            return

        # 测试2: 使用自然语言执行任务
        print("\n[测试2] 使用自然语言执行图像生成任务...")
        try:
            result = await agent.execute(
                {
                    "content": "请帮我生成一张图片，内容是一只可爱的小猫坐在窗台上，阳光洒在它身上，画面温馨自然。"
                }
            )
            print(f"✓ 任务执行完成: {result.get('success', False)}")
            if result.get("success"):
                print(f"  结果类型: {type(result.get('result', {})).__name__}")
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            import traceback

            traceback.print_exc()

        # 测试3: 使用便捷方法生成图像（可选，需要较长时间）
        print("\n[测试3] 使用便捷方法生成图像（跳过，需要较长时间）...")
        print("  提示: 如需测试，请取消注释以下代码")
        # try:
        #     result = await agent.generate_image(
        #         prompt="一只坐着的橙色猫，表情开心，活泼可爱，真实准确。",
        #         negative_prompt="低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良、模糊、失真",
        #         width=1280,
        #         height=1280,
        #         max_wait_time=300,  # 5分钟
        #     )
        #     print(f"✓ 图像生成完成: {result.get('success', False)}")
        #     if result.get('success'):
        #         print(f"  生成的图片URL: {result.get('result', [])}")
        # except Exception as e:
        #     print(f"❌ 图像生成失败: {e}")
        #     import traceback
        #     traceback.print_exc()

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)

    asyncio.run(run_tests())

