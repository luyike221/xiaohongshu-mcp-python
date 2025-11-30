#!/usr/bin/env python3
"""测试小红书内容生成MCP服务

直接测试 XHSContentGeneratorService 的功能，并集成图片生成

使用方法:
    python test_xhs_content_generator.py              # 完整测试（包含图片生成和发布）
    python test_xhs_content_generator.py --no-images   # 仅测试内容生成，不生成图片
    python test_xhs_content_generator.py --no-publish  # 不发布内容到小红书
    python test_xhs_content_generator.py --single       # 单个用例测试
    python test_xhs_content_generator.py --factory      # 测试工厂函数

前置条件:
    1. 配置 ALIBABA_BAILIAN_API_KEY 环境变量或在 .env 文件中设置
    2. 确保 xhs-content-generator-mcp 服务正在运行（默认地址：http://127.0.0.1:8004/mcp）
    3. 确保 image-video-mcp 服务正在运行（默认地址：http://127.0.0.1:8003/mcp）
    4. 确保 xhs-browser-automation-mcp 服务正在运行（默认地址：http://127.0.0.1:8002/mcp）
    5. 确保已登录小红书账号（通过浏览器自动化服务）
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from ai_social_scheduler.ai_agent.agents.mcp.xhs import (
    XHSContentGeneratorService,
    create_xhs_content_generator_service,
    ImageVideoMCPService,
    create_image_video_mcp_service,
    XiaohongshuBrowserMCPService,
    create_xiaohongshu_browser_mcp_service,
)


async def test_basic(generate_images: bool = True, publish_content: bool = True):
    """基本功能测试（包含图片生成和发布）
    
    Args:
        generate_images: 是否生成图片，默认 True
        publish_content: 是否发布内容到小红书，默认 True
    """
    print("=" * 60)
    print("小红书内容生成MCP服务测试")
    if generate_images:
        print("（包含图片生成）")
    if publish_content:
        print("（包含内容发布）")
    print("=" * 60)
    print("\n架构说明：")
    print("✨ 使用 LangChain 官方 MCP 适配器")
    print("✨ 仅封装 MCP 调用，不创建 Agent")
    print("✨ 支持 HTTP 传输方式")
    if generate_images:
        print("✨ 集成图片生成功能")
    if publish_content:
        print("✨ 集成内容发布功能")
    print("\n注意：")
    print("1. 确保已配置环境变量（ALIBABA_BAILIAN_API_KEY 等）")
    print("2. 确保 xhs-content-generator-mcp 服务正在运行（默认：http://127.0.0.1:8004/mcp）")
    if generate_images:
        print("3. 确保 image-video-mcp 服务正在运行（默认：http://127.0.0.1:8003/mcp）")
    if publish_content:
        print("4. 确保 xhs-browser-automation-mcp 服务正在运行（默认：http://127.0.0.1:8002/mcp）")
        print("5. 确保已登录小红书账号（通过浏览器自动化服务）")
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
    ]

    # 执行测试用例
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"主题: {test_case['topic']}")
        print(f"参数: {json.dumps({k: v for k, v in test_case.items() if k != 'name'}, indent=2, ensure_ascii=False)}")
        print(f"\n开始生成大纲...")

        try:
            import time
            
            # 步骤1: 生成内容大纲
            async with XHSContentGeneratorService() as content_service:
                start_time = time.time()
                result = await content_service.generate_outline(**{k: v for k, v in test_case.items() if k != 'name'})
                elapsed_time = time.time() - start_time

                print(f"\n⏱️  内容生成耗时: {elapsed_time:.2f} 秒")
                print(f"\n内容生成结果:")
                print(json.dumps(result, indent=2, ensure_ascii=False))

                if result.get("success"):
                    print(f"\n✅ 内容生成成功: {test_case['name']}")
                    outline = result.get('outline', '')
                    pages = result.get('pages', [])
                    title = result.get('title', '')
                    content = result.get('content', '')
                    tags = result.get('tags', [])
                    
                    print(f"  - 大纲长度: {len(outline)} 字符")
                    print(f"  - 页面数量: {len(pages)}")
                    print(f"  - 标题: {title}")
                    print(f"  - 正文长度: {len(content)} 字符")
                    print(f"  - 标签数量: {len(tags)}")
                    if tags:
                        print(f"  - 标签: {', '.join(tags)}")
                    
                    # 显示大纲预览
                    if outline:
                        print(f"\n大纲预览（前500字符）:")
                        preview = outline[:500] + "..." if len(outline) > 500 else outline
                        print(f"{preview}")
                    
                    # 显示提取的标题和内容预览
                    if title:
                        print(f"\n提取的标题:")
                        print(f"  {title}")
                    if content:
                        print(f"\n提取的正文预览（前300字符）:")
                        preview = content[:300] + "..." if len(content) > 300 else content
                        print(f"  {preview}")
                    
                    # 步骤2: 生成图片（如果启用）
                    if generate_images and pages:
                        print(f"\n{'='*60}")
                        print(f"开始生成图片...")
                        print(f"{'='*60}")
                        
                        try:
                            async with ImageVideoMCPService() as image_service:
                                image_start_time = time.time()
                                
                                # 准备图片生成参数
                                image_pages = [
                                    {
                                        "index": page.get("index", i),
                                        "type": page.get("type", "content"),
                                        "content": page.get("content", "")
                                    }
                                    for i, page in enumerate(pages)
                                ]
                                
                                print(f"准备为 {len(image_pages)} 个页面生成图片...")
                                print(f"主题: {test_case['topic']}")
                                
                                # 调用批量图片生成接口
                                image_result = await image_service.generate_images_batch(
                                    pages=image_pages,
                                    full_outline=outline,
                                    user_topic=test_case['topic'],
                                    max_wait_time=600,  # 10分钟超时
                                )
                                
                                image_elapsed_time = time.time() - image_start_time
                                
                                print(f"\n⏱️  图片生成耗时: {image_elapsed_time:.2f} 秒")
                                print(f"\n图片生成结果:")
                                print(json.dumps(image_result, indent=2, ensure_ascii=False))
                                
                                if image_result.get("success"):
                                    print(f"\n✅ 图片生成成功")
                                    print(f"  - 任务ID: {image_result.get('task_id', 'N/A')}")
                                    print(f"  - 总页面数: {image_result.get('total', 0)}")
                                    print(f"  - 成功生成: {image_result.get('completed', 0)}")
                                    print(f"  - 失败数量: {image_result.get('failed', 0)}")
                                    
                                    # 显示生成的图片
                                    images = image_result.get('images', [])
                                    if images:
                                        print(f"\n生成的图片列表:")
                                        for img in images:
                                            print(f"  - 页面 {img.get('index', '?')} ({img.get('type', 'unknown')}):")
                                            print(f"    URL: {img.get('url', 'N/A')}")
                                    
                                    # 显示失败的页面
                                    failed_pages = image_result.get('failed_pages', [])
                                    if failed_pages:
                                        print(f"\n失败的页面:")
                                        for failed in failed_pages:
                                            print(f"  - 页面 {failed.get('index', '?')}: {failed.get('error', 'N/A')}")
                                    
                                    # 步骤3: 发布内容到小红书（如果启用）
                                    if publish_content and images:
                                        print(f"\n{'='*60}")
                                        print(f"开始发布内容到小红书...")
                                        print(f"{'='*60}")
                                        
                                        try:
                                            async with XiaohongshuBrowserMCPService() as publish_service:
                                                publish_start_time = time.time()
                                                
                                                # 使用从 generate_outline 中提取的标题、内容和标签
                                                # 这些数据已经清理过，不包含标题、副标题等元数据
                                                publish_title = result.get('title', '')
                                                publish_content = result.get('content', '')
                                                publish_tags = result.get('tags', [])
                                                
                                                # 如果标题为空，使用主题作为后备
                                                if not publish_title:
                                                    publish_title = test_case['topic']
                                                    if len(publish_title) > 20:
                                                        publish_title = publish_title[:20]
                                                
                                                # 如果内容为空，从大纲提取（作为后备方案）
                                                if not publish_content:
                                                    # 从大纲中提取，移除标记
                                                    import re
                                                    content_text = outline
                                                    # 移除页面类型标记
                                                    content_text = re.sub(r'^\[(封面|内容|总结)\]\s*', '', content_text, flags=re.MULTILINE)
                                                    # 移除标题、标签、视觉方案等行
                                                    lines = content_text.split('\n')
                                                    cleaned_lines = []
                                                    skip_keywords = ['标题：', '副标题：', '标签：', '视觉方案：', '视觉：', '方案：']
                                                    
                                                    for line in lines:
                                                        line = line.strip()
                                                        if not line:
                                                            continue
                                                        # 跳过包含关键词的行
                                                        if any(line.startswith(kw) for kw in skip_keywords):
                                                            continue
                                                        # 跳过太短的行
                                                        if len(line) < 3:
                                                            continue
                                                        cleaned_lines.append(line)
                                                    
                                                    publish_content = '\n'.join(cleaned_lines)
                                                    
                                                    # 如果还是为空，使用简化的主题描述
                                                    if not publish_content:
                                                        publish_content = f"分享{test_case['topic']}的详细步骤和心得。"
                                                
                                                # 如果标签为空，使用测试用例名称作为标签
                                                if not publish_tags:
                                                    publish_tags = [test_case['name']]
                                                
                                                # 限制内容长度，避免输入超时
                                                # 小红书正文建议1000-2000字，但为了安全，限制在1200字符以内
                                                MAX_CONTENT_LENGTH = 1200
                                                if len(publish_content) > MAX_CONTENT_LENGTH:
                                                    # 尝试智能截取：在句号、感叹号、问号处截断
                                                    truncated = publish_content[:MAX_CONTENT_LENGTH]
                                                    last_punct = max(
                                                        truncated.rfind('。'),
                                                        truncated.rfind('！'),
                                                        truncated.rfind('？'),
                                                        truncated.rfind('.'),
                                                        truncated.rfind('!'),
                                                        truncated.rfind('?')
                                                    )
                                                    if last_punct > MAX_CONTENT_LENGTH * 0.7:  # 如果标点在70%位置之后，使用该位置
                                                        publish_content = truncated[:last_punct + 1]
                                                    else:
                                                        publish_content = truncated + "..."
                                                    print(f"  ⚠️  内容过长，已截取至 {len(publish_content)} 字符")
                                                
                                                # 提取图片 URL 列表
                                                image_urls = [img.get('url') for img in images if img.get('url')]
                                                
                                                print(f"发布参数:")
                                                print(f"  - 标题: {publish_title}")
                                                print(f"  - 内容长度: {len(publish_content)} 字符")
                                                print(f"  - 图片数量: {len(image_urls)}")
                                                print(f"  - 标签: {', '.join(publish_tags) if publish_tags else '无'}")
                                                
                                                if not image_urls:
                                                    print(f"\n⚠️  没有可用的图片URL，跳过发布")
                                                else:
                                                    # 调用发布接口
                                                    publish_result = await publish_service.publish_content(
                                                        title=publish_title,
                                                        content=publish_content,
                                                        images=image_urls,
                                                        tags=publish_tags,
                                                    )
                                                    
                                                    publish_elapsed_time = time.time() - publish_start_time
                                                    
                                                    print(f"\n⏱️  发布耗时: {publish_elapsed_time:.2f} 秒")
                                                    print(f"\n发布结果:")
                                                    print(json.dumps(publish_result, indent=2, ensure_ascii=False))
                                                    
                                                    if publish_result.get("success"):
                                                        print(f"\n✅ 内容发布成功")
                                                        if publish_result.get("result"):
                                                            result_info = publish_result.get("result", {})
                                                            if isinstance(result_info, dict):
                                                                print(f"  - 发布状态: {result_info.get('status', 'N/A')}")
                                                                print(f"  - 消息: {result_info.get('message', 'N/A')}")
                                                    else:
                                                        print(f"\n❌ 内容发布失败")
                                                        error_msg = publish_result.get("error", "Unknown error")
                                                        print(f"错误信息: {error_msg}")
                                                        
                                        except Exception as publish_e:
                                            print(f"\n⚠️  内容发布异常: {test_case['name']}")
                                            print(f"错误类型: {type(publish_e).__name__}")
                                            print(f"错误信息: {str(publish_e)}")
                                            import traceback
                                            print(f"\n详细错误:")
                                            traceback.print_exc()
                                else:
                                    print(f"\n❌ 图片生成失败")
                                    error_msg = image_result.get("error", "Unknown error")
                                    print(f"错误信息: {error_msg}")
                                    
                        except Exception as img_e:
                            print(f"\n⚠️  图片生成异常: {test_case['name']}")
                            print(f"错误类型: {type(img_e).__name__}")
                            print(f"错误信息: {str(img_e)}")
                            import traceback
                            print(f"\n详细错误:")
                            traceback.print_exc()
                else:
                    print(f"\n❌ 内容生成失败: {test_case['name']}")
                    error_msg = result.get("error", "Unknown error")
                    print(f"错误信息: {error_msg}")
                    if not generate_images:
                        print(f"（跳过图片生成）")

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


async def test_single():
    """单个用例测试（简化版）"""
    print("=" * 60)
    print("小红书内容生成MCP服务测试 - 单个用例")
    print("=" * 60)

    # 单个测试用例
    input_data = {
        "topic": "如何在家做拿铁",
        "provider_type": "alibaba_bailian",
        "temperature": 0.3,
    }

    print(f"\n输入数据:")
    print(json.dumps(input_data, indent=2, ensure_ascii=False))
    print(f"\n开始生成大纲...")

    try:
        async with XHSContentGeneratorService() as service:
            result = await service.generate_outline(**input_data)
            print(f"\n执行结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if result.get("success"):
                print(f"\n✅ 测试通过")
                outline = result.get('outline', '')
                pages = result.get('pages', [])
                title = result.get('title', '')
                content = result.get('content', '')
                tags = result.get('tags', [])
                
                print(f"  - 大纲长度: {len(outline)} 字符")
                print(f"  - 页面数量: {len(pages)}")
                print(f"  - 标题: {title}")
                print(f"  - 正文长度: {len(content)} 字符")
                print(f"  - 标签数量: {len(tags)}")
                if tags:
                    print(f"  - 标签: {', '.join(tags)}")
            else:
                print(f"\n❌ 测试失败")
                print(f"错误: {result.get('error', 'N/A')}")
    except Exception as e:
        print(f"执行失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_factory():
    """测试工厂函数"""
    print("=" * 60)
    print("测试工厂函数创建服务")
    print("=" * 60)

    try:
        # 使用工厂函数创建服务
        service = await create_xhs_content_generator_service()
        print("✅ 服务创建成功")

        # 测试生成大纲
        result = await service.generate_outline(
            topic="产品宣传",
            provider_type="alibaba_bailian",
        )

        print(f"\n生成结果:")
        print(f"  - 成功: {result.get('success', False)}")
        if result.get('success'):
            print(f"  - 页面数量: {len(result.get('pages', []))}")

        # 关闭服务
        await service.close()
        print("✅ 服务已关闭")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    # 选择测试模式
    generate_images = True
    publish_content = True
    if len(sys.argv) > 1:
        if sys.argv[1] == "--single":
            await test_single()
            return
        elif sys.argv[1] == "--factory":
            await test_factory()
            return
        elif sys.argv[1] == "--no-images":
            generate_images = False
        elif sys.argv[1] == "--no-publish":
            publish_content = False
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("可用参数:")
            print("  --single      单个用例测试")
            print("  --factory     测试工厂函数")
            print("  --no-images   仅测试内容生成，不生成图片")
            print("  --no-publish  不发布内容到小红书")
            return
    
    # 处理多个参数
    for arg in sys.argv[1:]:
        if arg == "--no-images":
            generate_images = False
        elif arg == "--no-publish":
            publish_content = False
    
    await test_basic(generate_images=generate_images, publish_content=publish_content)


if __name__ == "__main__":
    asyncio.run(main())

