"""小红书内容生成MCP服务测试脚本

这是一个简单的测试脚本，可以直接运行来测试 XHSContentGeneratorService。

使用方法:
    python test_xhs_content_generator_service.py

前置条件:
    1. 配置 ALIBABA_BAILIAN_API_KEY 环境变量或在 .env 文件中设置
    2. 确保 xhs-content-generator-mcp 服务正在运行（默认地址：http://127.0.0.1:8004/mcp）
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_social_scheduler.ai_agent.agents.mcp.xhs import (
    XHSContentGeneratorService,
    create_xhs_content_generator_service,
)
from ai_social_scheduler.config import model_config


def get_api_key():
    """从配置获取 API Key"""
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


async def test_service_basic():
    """测试服务基本功能"""
    print("=" * 60)
    print("小红书内容生成MCP服务基本功能测试")
    print("=" * 60)

    print(f"✓ 开始测试\n")

    # 测试1: 创建服务
    print("[测试1] 创建服务...")
    try:
        service = XHSContentGeneratorService()
        print(f"✓ 服务创建成功")
        print(f"  - MCP URL: {service.mcp_url}")
        print(f"  - MCP Transport: {service.mcp_transport}")
    except Exception as e:
        print(f"❌ 服务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试2: 初始化服务
    print("\n[测试2] 初始化服务（连接MCP服务器）...")
    try:
        await service._initialize()
        print(f"✓ 服务初始化成功")
        print(f"  - 初始化状态: {service._initialized}")
        if service._generate_outline_tool:
            print(f"  - 找到工具: {service._generate_outline_tool.name}")
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        print(f"  提示: 请确保 xhs-content-generator-mcp 服务正在运行")
        print(f"  默认地址: http://127.0.0.1:8004/mcp")
        import traceback
        traceback.print_exc()
        return False

    # 测试3: 生成简单大纲
    print("\n[测试3] 生成简单大纲（默认配置）...")
    print("  主题: 如何在家做拿铁")
    try:
        result = await service.generate_outline(
            topic="如何在家做拿铁",
            provider_type="alibaba_bailian",
            temperature=0.3,
        )
        
        print(f"✓ 大纲生成完成")
        print(f"  - 成功: {result.get('success', False)}")
        
        if result.get('success'):
            outline = result.get('outline', '')
            pages = result.get('pages', [])
            print(f"  - 大纲长度: {len(outline)} 字符")
            print(f"  - 页面数量: {len(pages)}")
            print(f"  - 使用图片: {result.get('has_images', False)}")
            print(f"  - 使用VL分析: {result.get('image_analysis_used', False)}")
            
            # 显示大纲预览
            if outline:
                preview = outline[:200] + "..." if len(outline) > 200 else outline
                print(f"\n  大纲预览:")
                print(f"  {preview}")
            
            # 显示页面结构
            if pages:
                print(f"\n  页面结构:")
                for page in pages[:3]:  # 只显示前3页
                    page_type = page.get('type', 'unknown')
                    content_preview = page.get('content', '')[:50]
                    print(f"    - 页面 {page.get('index', '?')} ({page_type}): {content_preview}...")
        else:
            error = result.get('error', 'Unknown error')
            print(f"  - 错误: {error}")
            
    except Exception as e:
        print(f"❌ 大纲生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试4: 生成带自定义参数的大纲
    print("\n[测试4] 生成带自定义参数的大纲...")
    print("  主题: 秋季显白美甲")
    print("  参数: provider_type=alibaba_bailian, temperature=0.5")
    try:
        result = await service.generate_outline(
            topic="秋季显白美甲",
            provider_type="alibaba_bailian",
            temperature=0.5,
            max_output_tokens=8000,
        )
        
        print(f"✓ 大纲生成完成")
        print(f"  - 成功: {result.get('success', False)}")
        if result.get('success'):
            pages = result.get('pages', [])
            print(f"  - 页面数量: {len(pages)}")
        else:
            print(f"  - 错误: {result.get('error', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 大纲生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试5: 使用工厂函数创建服务
    print("\n[测试5] 使用工厂函数创建服务...")
    try:
        service2 = await create_xhs_content_generator_service()
        print(f"✓ 工厂函数创建成功")
        print(f"  - 初始化状态: {service2._initialized}")
        await service2.close()
        print(f"✓ 服务已关闭")
    except Exception as e:
        print(f"❌ 工厂函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试6: 使用异步上下文管理器
    print("\n[测试6] 使用异步上下文管理器...")
    try:
        async with XHSContentGeneratorService() as service3:
            result = await service3.generate_outline(
                topic="产品宣传",
                provider_type="alibaba_bailian",
            )
            print(f"✓ 上下文管理器测试成功")
            print(f"  - 生成结果: {result.get('success', False)}")
        print(f"✓ 上下文管理器自动关闭成功")
    except Exception as e:
        print(f"❌ 上下文管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 清理
    print("\n[清理] 关闭服务...")
    try:
        await service.close()
        print("✓ 服务已关闭")
    except Exception as e:
        print(f"⚠️  关闭服务时出错: {e}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    return True


async def test_generate_outline_detailed():
    """详细测试大纲生成功能"""
    print("=" * 60)
    print("大纲生成功能详细测试")
    print("=" * 60)

    # 测试用例
    test_cases = [
        {
            "name": "美食教程",
            "topic": "如何在家做拿铁",
            "provider_type": "alibaba_bailian",
            "temperature": 0.3,
        },
        {
            "name": "美妆分享",
            "topic": "秋季显白美甲",
            "provider_type": "alibaba_bailian",
            "temperature": 0.5,
        },
        {
            "name": "产品宣传",
            "topic": "新款智能手表功能介绍",
            "provider_type": "alibaba_bailian",
            "temperature": 0.3,
        },
    ]

    async with XHSContentGeneratorService() as service:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"测试用例 {i}: {test_case['name']}")
            print(f"{'='*60}")
            print(f"主题: {test_case['topic']}")
            print(f"参数: provider_type={test_case['provider_type']}, temperature={test_case['temperature']}")
            print(f"\n开始生成...")

            try:
                result = await service.generate_outline(**test_case)

                print(f"\n生成结果:")
                print(f"  - 成功: {result.get('success', False)}")

                if result.get('success'):
                    outline = result.get('outline', '')
                    pages = result.get('pages', [])
                    print(f"  - 大纲长度: {len(outline)} 字符")
                    print(f"  - 页面数量: {len(pages)}")
                    
                    # 显示完整大纲
                    print(f"\n完整大纲:")
                    print(f"{outline}")
                    
                    # 显示页面详情
                    if pages:
                        print(f"\n页面详情:")
                        for page in pages:
                            print(f"\n  页面 {page.get('index', '?')} ({page.get('type', 'unknown')}):")
                            print(f"  {page.get('content', '')}")
                else:
                    print(f"  - 错误: {result.get('error', 'N/A')}")

            except Exception as e:
                print(f"❌ 生成失败: {e}")
                import traceback
                traceback.print_exc()

            # 等待一下再执行下一个测试
            if i < len(test_cases):
                print(f"\n等待2秒后执行下一个测试...")
                await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("详细测试完成!")
    print("=" * 60)


async def test_error_handling():
    """测试错误处理"""
    print("=" * 60)
    print("错误处理测试")
    print("=" * 60)

    async with XHSContentGeneratorService() as service:
        # 测试1: 空主题
        print("\n[测试1] 空主题...")
        result = await service.generate_outline(topic="")
        print(f"  结果: success={result.get('success', False)}")
        if not result.get('success'):
            print(f"  错误: {result.get('error', 'N/A')}")

        # 测试2: 无效的 provider_type
        print("\n[测试2] 无效的 provider_type...")
        result = await service.generate_outline(
            topic="测试主题",
            provider_type="invalid_provider",
        )
        print(f"  结果: success={result.get('success', False)}")
        if not result.get('success'):
            print(f"  错误: {result.get('error', 'N/A')}")

    print("\n" + "=" * 60)
    print("错误处理测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="小红书内容生成MCP服务测试")
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="详细测试大纲生成功能",
    )
    parser.add_argument(
        "--error",
        action="store_true",
        help="测试错误处理",
    )
    args = parser.parse_args()

    if args.detailed:
        success = asyncio.run(test_generate_outline_detailed())
    elif args.error:
        success = asyncio.run(test_error_handling())
    else:
        success = asyncio.run(test_service_basic())

    sys.exit(0 if success else 1)

