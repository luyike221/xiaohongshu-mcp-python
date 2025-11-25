#!/usr/bin/env python3
"""直接测试内容发布工作流 - 图文内容场景（使用真正的 LangGraph 多 Agent）"""

import asyncio
import json
import sys
from typing import Dict, Any

from ai_social_scheduler.ai_agent.graph.factory import create_content_publish_graph
from ai_social_scheduler.ai_agent.workflows.content_publish import ContentPublishWorkflow


async def test_publish_image_content():
    """测试发布图文内容（使用真正的 LangGraph 多 Agent 架构）"""
    
    print("正在创建 LangGraph 工作流和所有 Agent...")
    try:
        # 创建 LangGraph 工作流图（按需加载 Agent）
        workflow_graph = await create_content_publish_graph(
            llm_model="qwen-plus",
            llm_temperature=0.7,
        )
        print("✅ LangGraph 工作流创建成功\n")
    except Exception as e:
        print(f"❌ 创建工作流失败: {str(e)}")
        print("请确保已配置必要的环境变量（如 ALIBABA_BAILIAN_API_KEY）")
        sys.exit(1)
    
    # 创建工作流实例
    workflow = ContentPublishWorkflow(workflow_graph)
    
    # 测试用例：图文内容
    test_cases = [
        {
            "name": "美食图文内容",
            "data": {
                "user_id": "test_user_001",
                "request": "我想发布一篇关于家常菜制作的图文笔记，主题是红烧肉的做法，需要配图展示制作步骤",
                "context": {
                    "topic": "美食",
                    "style": "教程",
                    "content_type": "image",  # 指定为图文内容
                    "image_count": 3,  # 需要3张图片
                    "keywords": ["红烧肉", "家常菜", "美食教程"]
                }
            }
        },
        {
            "name": "旅行图文内容",
            "data": {
                "user_id": "test_user_002",
                "request": "发布一篇关于云南旅行的图文笔记，分享大理古城的风景和美食",
                "context": {
                    "topic": "旅行",
                    "style": "分享",
                    "content_type": "image",
                    "image_count": 4,
                    "keywords": ["云南", "大理", "旅行", "古城"]
                }
            }
        },
        {
            "name": "穿搭图文内容",
            "data": {
                "user_id": "test_user_003",
                "request": "发布一篇春季穿搭的图文笔记，展示几套不同风格的搭配",
                "context": {
                    "topic": "穿搭",
                    "style": "分享",
                    "content_type": "image",
                    "image_count": 5,
                    "keywords": ["春季穿搭", "时尚", "搭配"]
                }
            }
        }
    ]
    
    # 执行测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"输入数据:")
        print(json.dumps(test_case['data'], indent=2, ensure_ascii=False))
        print(f"\n开始执行工作流...")
        print("提示: 工作流执行可能需要较长时间，特别是生成图片的步骤")
        print("正在执行中，请耐心等待...\n")
        
        try:
            # 直接执行工作流
            import time
            start_time = time.time()
            result = await workflow.execute(test_case['data'])
            elapsed_time = time.time() - start_time
            print(f"\n⏱️  执行耗时: {elapsed_time:.2f} 秒")
            
            print(f"\n工作流执行结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get("success"):
                print(f"\n✅ 测试通过: {test_case['name']}")
                workflow_id = f"content_publish_{test_case['data']['user_id']}"
                print(f"工作流ID: {workflow_id}")
            else:
                print(f"\n❌ 测试失败: {test_case['name']}")
                error_msg = result.get("error", "Unknown error")
                print(f"错误信息: {error_msg}")
                
        except asyncio.TimeoutError:
            print(f"\n⏱️  执行超时: {test_case['name']}")
            print("提示: 工作流执行可能需要较长时间，特别是生成图片的步骤")
        except Exception as e:
            print(f"\n❌ 执行异常: {test_case['name']}")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            import traceback
            print(f"\n详细错误:")
            traceback.print_exc()
        
        # 等待一下再执行下一个测试
        if i < len(test_cases):
            print(f"\n等待3秒后执行下一个测试...")
            await asyncio.sleep(3)


async def test_single_case():
    """测试单个用例（简化版）"""
    print("正在创建 LangGraph 工作流和所有 Agent...")
    try:
        workflow_graph = await create_content_publish_graph(
            llm_model="qwen-plus",
            llm_temperature=0.7,
        )
        print("✅ LangGraph 工作流创建成功\n")
    except Exception as e:
        print(f"❌ 创建工作流失败: {str(e)}")
        sys.exit(1)
    
    workflow = ContentPublishWorkflow(workflow_graph)
    
    # 单个测试用例
    input_data = {
        "user_id": "test_user_001",
        "request": "我想发布一篇关于家常菜制作的图文笔记，主题是红烧肉的做法，需要配图展示制作步骤",
        "context": {
            "topic": "美食",
            "style": "教程",
            "content_type": "image",
            "image_count": 3,
            "keywords": ["红烧肉", "家常菜", "美食教程"]
        }
    }
    
    print(f"输入数据:")
    print(json.dumps(input_data, indent=2, ensure_ascii=False))
    print(f"\n开始执行工作流...")
    
    try:
        result = await workflow.execute(input_data)
        print(f"\n执行结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("="*60)
    print("小红书内容发布工作流测试 - 真正的 LangGraph 多 Agent 架构")
    print("="*60)
    print("\n架构说明：")
    print("✨ 使用 LangGraph StateGraph 进行显式节点编排")
    print("✨ 每个步骤都是独立节点，通过共享状态传递数据")
    print("✨ Agent 返回结构化结果而非自然语言")
    print("✨ 按需加载 Agent，避免不必要的初始化")
    print("\n注意：")
    print("1. 确保已配置环境变量（ALIBABA_BAILIAN_API_KEY 等）")
    print("2. 确保图像视频生成MCP服务正在运行（默认：http://127.0.0.1:8003/mcp）")
    print("3. 确保小红书MCP服务正在运行（默认：http://127.0.0.1:8002/mcp）")
    print("="*60)
    
    # 选择测试模式
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # 单个用例测试
        await test_single_case()
    else:
        # 多个用例测试
        await test_publish_image_content()


if __name__ == "__main__":
    asyncio.run(main())

