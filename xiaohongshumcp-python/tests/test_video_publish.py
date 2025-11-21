#!/usr/bin/env python3
"""
视频发布功能测试脚本
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from xiaohongshu_mcp_python.main import xiaohongshu_publish_video


async def test_video_publish():
    """测试视频发布功能"""
    
    # 测试参数
    test_title = "测试视频发布"
    test_content = "这是一个测试视频内容，用于验证MCP视频发布接口的功能。"
    test_video_path = "/path/to/test/video.mp4"  # 请替换为实际的视频文件路径
    test_tags = ["测试", "视频", "MCP"]
    test_username = "test_user"
    
    print("开始测试视频发布功能...")
    print(f"标题: {test_title}")
    print(f"内容: {test_content}")
    print(f"视频路径: {test_video_path}")
    print(f"标签: {test_tags}")
    print(f"用户名: {test_username}")
    print("-" * 50)
    
    try:
        # 调用视频发布接口
        result = await xiaohongshu_publish_video(
            title=test_title,
            content=test_content,
            video=test_video_path,
            tags=test_tags,
            username=test_username
        )
        
        print("发布结果:")
        print(f"成功: {result.get('success', False)}")
        print(f"消息: {result.get('message', 'N/A')}")
        
        if result.get('success'):
            print("✅ 视频发布测试成功!")
            if 'result' in result:
                print(f"发布详情: {result['result']}")
        else:
            print("❌ 视频发布测试失败!")
            if 'error' in result:
                print(f"错误信息: {result['error']}")
                
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


def test_video_publish_parameters():
    """测试视频发布参数验证"""
    
    print("\n" + "=" * 50)
    print("测试参数验证...")
    
    # 测试用例
    test_cases = [
        {
            "name": "正常参数",
            "params": {
                "title": "正常标题",
                "content": "正常内容",
                "video": "/path/to/video.mp4",
                "tags": ["标签1", "标签2"]
            },
            "expected": "应该通过参数验证"
        },
        {
            "name": "空标题",
            "params": {
                "title": "",
                "content": "正常内容",
                "video": "/path/to/video.mp4",
                "tags": ["标签1"]
            },
            "expected": "应该失败 - 标题为空"
        },
        {
            "name": "标题过长",
            "params": {
                "title": "这是一个非常长的标题" * 10,
                "content": "正常内容",
                "video": "/path/to/video.mp4",
                "tags": ["标签1"]
            },
            "expected": "应该失败 - 标题过长"
        },
        {
            "name": "视频路径为空",
            "params": {
                "title": "正常标题",
                "content": "正常内容",
                "video": "",
                "tags": ["标签1"]
            },
            "expected": "应该失败 - 视频路径为空"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['name']}")
        print(f"参数: {case['params']}")
        print(f"预期: {case['expected']}")
        
        # 这里可以添加实际的参数验证逻辑
        # 由于需要实际的浏览器环境，这里只是展示测试结构
        print("✓ 参数验证测试结构正确")


if __name__ == "__main__":
    print("小红书视频发布MCP接口测试")
    print("=" * 50)
    
    # 检查是否在正确的环境中运行
    if not os.path.exists("src/xiaohongshu_mcp_python"):
        print("❌ 请在项目根目录下运行此测试脚本")
        sys.exit(1)
    
    # 运行参数验证测试
    test_video_publish_parameters()
    
    print("\n" + "=" * 50)
    print("注意事项:")
    print("1. 实际测试需要配置有效的视频文件路径")
    print("2. 需要先登录小红书账号")
    print("3. 需要启动浏览器环境")
    print("4. 建议在开发环境中进行测试")
    
    # 如果需要运行实际的异步测试，取消下面的注释
    # print("\n运行实际视频发布测试...")
    # asyncio.run(test_video_publish())