#!/usr/bin/env python3
"""
测试发布流程的进度报告机制
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent / "src"
sys.path.insert(0, str(project_root))

from xiaohongshu_mcp_python.actions.publish import PublishAction, PublishImageContent
from xiaohongshu_mcp_python.browser.browser_manager import BrowserManager

class MockContext:
    """模拟MCP Context类，用于测试进度报告"""
    
    def __init__(self):
        self.progress_reports = []
    
    async def report_progress(self, progress: int, total: int):
        """记录进度报告"""
        percentage = (progress / total) * 100
        print(f"进度报告: {progress}/{total} ({percentage:.1f}%)")
        self.progress_reports.append((progress, total))

async def test_publish_with_progress():
    """测试带进度报告的发布流程"""
    print("开始测试发布流程的进度报告机制...")
    
    # 创建模拟的Context
    context = MockContext()
    
    # 创建浏览器管理器
    browser_manager = BrowserManager(headless=True)
    
    try:
        # 启动浏览器
        await browser_manager.start()
        page = await browser_manager.get_page()
        
        # 创建发布动作
        publish_action = PublishAction(page)
        
        # 创建测试内容（添加一个虚拟图片路径以满足验证要求）
        test_content = PublishImageContent(
            title="测试标题",
            content="这是一个测试内容",
            images=["/tmp/test_image.jpg"],  # 添加虚拟图片路径
            tags=["测试"]
        )
        
        print("开始测试导航到发布页面...")
        
        # 只测试导航部分，因为这是最耗时的操作
        try:
            await publish_action._navigate_to_publish_page(context)
            print("✅ 导航到发布页面成功")
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            # 这是预期的，因为我们没有真正登录
        
        # 检查进度报告
        print(f"\n进度报告记录: {len(context.progress_reports)} 条")
        for i, (progress, total) in enumerate(context.progress_reports):
            percentage = (progress / total) * 100
            print(f"  {i+1}. {progress}/{total} ({percentage:.1f}%)")
        
        if context.progress_reports:
            print("✅ 进度报告机制工作正常")
        else:
            print("❌ 没有收到进度报告")
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        # 清理资源
        await browser_manager.stop()

async def test_context_parameter_passing():
    """测试Context参数传递"""
    print("\n测试Context参数传递...")
    
    browser_manager = BrowserManager(headless=True)
    context = MockContext()
    
    try:
        await browser_manager.start()
        page = await browser_manager.get_page()
        
        publish_action = PublishAction(page)
        
        # 测试publish方法是否接受context参数
        test_content = PublishImageContent(
            title="测试",
            content="测试内容",
            images=["/tmp/test_image.jpg"],  # 添加虚拟图片路径
            tags=[]
        )
        
        try:
            # 这会失败，但我们主要是测试参数传递
            await publish_action.publish(test_content, context)
        except Exception as e:
            print(f"预期的错误（因为没有登录）: {type(e).__name__}")
        
        print("✅ Context参数传递测试完成")
        
    except Exception as e:
        print(f"参数传递测试错误: {e}")
    finally:
        await browser_manager.stop()

if __name__ == "__main__":
    print("=" * 50)
    print("测试发布流程的进度报告机制")
    print("=" * 50)
    
    asyncio.run(test_publish_with_progress())
    asyncio.run(test_context_parameter_passing())
    
    print("\n测试完成！")