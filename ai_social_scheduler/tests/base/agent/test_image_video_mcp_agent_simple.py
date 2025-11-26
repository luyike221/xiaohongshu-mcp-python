"""图像视频生成MCP服务智能体简单测试脚本

这是一个简单的测试脚本，可以直接运行来测试 image_video_mcp_agent。

使用方法:
    python test_image_video_mcp_agent_simple.py

前置条件:
    1. 配置 ALIBABA_BAILIAN_API_KEY 环境变量或在 .env 文件中设置
    2. 确保 image_video_mcp 服务正在运行（默认地址：http://127.0.0.1:8003/mcp）
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_social_scheduler.ai_agent.agents.mcp.image_video import (
    create_image_video_mcp_agent,
)
from ai_social_scheduler.config import model_config


def get_llm_api_key():
    """从配置获取 LLM API Key"""
    try:
        # 直接检查 model_config 的属性
        api_key = model_config.alibaba_bailian__api_key
        if api_key:
            return api_key

        # 如果直接属性为空，尝试从环境变量直接读取
        env_api_key = os.getenv("ALIBABA_BAILIAN_API_KEY")
        if env_api_key:
            return env_api_key

        # 尝试通过 get_alibaba_bailian_config 获取
        config = model_config.get_alibaba_bailian_config()
        return config.api_key
    except (ValueError, AttributeError) as e:
        print(f"⚠️  获取 API key 失败: {e}")
        return None


async def test_agent_basic():
    """测试 Agent 基本功能"""
    print("=" * 60)
    print("图像视频生成MCP Agent 基本功能测试")
    print("=" * 60)

    # 获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        print("❌ 错误: 需要配置 ALIBABA_BAILIAN_API_KEY 环境变量")
        print("   请在项目根目录的 .env 文件中设置 ALIBABA_BAILIAN_API_KEY")
        return False

    print(f"✓ API Key 已配置")

    # 测试1: 创建 agent
    print("\n[测试1] 创建 Agent...")
    try:
        agent = await create_image_video_mcp_agent(llm_api_key=api_key)
        print(f"✓ Agent 创建成功")
        print(f"  - 名称: {agent.name}")
        print(f"  - 初始化状态: {agent._initialized}")
        print(f"  - MCP URL: {agent.mcp_url}")
        print(f"  - MCP Transport: {agent.mcp_transport}")
    except Exception as e:
        print(f"❌ Agent 创建失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试2: 检查工具列表
    print("\n[测试2] 检查可用工具...")
    try:
        tools = agent._tools
        if tools:
            print(f"✓ 找到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool.name}")
        else:
            print("⚠️  未找到工具")
    except Exception as e:
        print(f"⚠️  检查工具失败: {e}")

    # 测试3: 使用自然语言执行任务
    print("\n[测试3] 使用自然语言执行图像生成任务...")
    print("  提示词: 请帮我生成一张图片，内容是一只可爱的小猫坐在窗台上")
    try:
        result = await agent.execute(
            {
                "content": "请帮我生成一张图片，内容是一只可爱的小猫坐在窗台上，阳光洒在它身上，画面温馨自然。"
            }
        )
        print(f"✓ 任务执行完成")
        print(f"  - 成功: {result.get('success', False)}")
        print(f"  - Agent: {result.get('agent', 'N/A')}")
        if result.get("result"):
            print(f"  - 结果类型: {type(result.get('result')).__name__}")
    except Exception as e:
        print(f"❌ 任务执行失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 测试4: 使用便捷方法生成图像（可选，需要较长时间）
    print("\n[测试4] 使用便捷方法生成图像...")
    print("  提示: 此测试需要较长时间（可能需要几分钟），是否继续？")
    print("  提示: 如需测试，请修改代码取消注释以下部分")
    # try:
    #     print("  开始生成图像...")
    #     result = await agent.generate_image(
    #         prompt="一只坐着的橙色猫，表情开心，活泼可爱，真实准确。",
    #         negative_prompt="低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良、模糊、失真",
    #         width=1280,
    #         height=1280,
    #         max_wait_time=300,  # 5分钟
    #     )
    #     print(f"✓ 图像生成完成")
    #     print(f"  - 成功: {result.get('success', False)}")
    #     if result.get('success'):
    #         urls = result.get('result', [])
    #         print(f"  - 生成的图片数量: {len(urls)}")
    #         for i, url in enumerate(urls, 1):
    #             print(f"  - 图片 {i}: {url}")
    #     else:
    #         print(f"  - 错误: {result.get('error', 'N/A')}")
    # except Exception as e:
    #     print(f"❌ 图像生成失败: {e}")
    #     import traceback
    #     traceback.print_exc()

    # 清理
    print("\n[清理] 关闭 Agent...")
    try:
        await agent.close()
        print("✓ Agent 已关闭")
    except Exception as e:
        print(f"⚠️  关闭 Agent 时出错: {e}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    return True


async def test_generate_image_direct():
    """直接测试图像生成功能（需要较长时间）"""
    print("=" * 60)
    print("图像生成功能直接测试")
    print("=" * 60)
    print("⚠️  注意: 此测试需要较长时间（可能需要几分钟）")
    print("=" * 60)

    # 获取 API key
    api_key = get_llm_api_key()
    if not api_key:
        print("❌ 错误: 需要配置 ALIBABA_BAILIAN_API_KEY 环境变量")
        return False

    # 创建 agent
    agent = await create_image_video_mcp_agent(llm_api_key=api_key)

    try:
        print("\n开始生成图像...")
        print("提示词: 一只坐着的橙色猫，表情开心，活泼可爱，真实准确。")
        print("尺寸: 1280x1280")
        print("等待时间: 最多5分钟...")

        result = await agent.generate_image(
            prompt="一只坐着的橙色猫，表情开心，活泼可爱，真实准确。",
            negative_prompt="低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良、模糊、失真",
            width=1280,
            height=1280,
            max_wait_time=300,  # 5分钟
        )

        print("\n" + "=" * 60)
        print("图像生成结果")
        print("=" * 60)
        print(f"成功: {result.get('success', False)}")

        if result.get("success"):
            urls = result.get("result", [])
            print(f"生成的图片数量: {len(urls)}")
            for i, url in enumerate(urls, 1):
                print(f"\n图片 {i}:")
                print(f"  URL: {url}")
        else:
            print(f"错误: {result.get('error', 'N/A')}")
            if "task_id" in result:
                print(f"任务 ID: {result.get('task_id')}")

        return result.get("success", False)

    except Exception as e:
        print(f"\n❌ 图像生成失败: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        await agent.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="图像视频生成MCP Agent 测试")
    parser.add_argument(
        "--generate-image",
        action="store_true",
        help="直接测试图像生成功能（需要较长时间）",
    )
    args = parser.parse_args()

    if args.generate_image:
        success = asyncio.run(test_generate_image_direct())
    else:
        success = asyncio.run(test_agent_basic())

    sys.exit(0 if success else 1)


