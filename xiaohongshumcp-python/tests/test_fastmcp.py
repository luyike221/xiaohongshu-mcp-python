#!/usr/bin/env python3
"""
测试 FastMCP 实现的小红书 MCP 服务器
"""

import asyncio
from fastmcp import Client

async def test_mcp_server():
    """测试FastMCP服务器"""
    # 创建客户端，直接使用脚本路径，FastMCP会自动推断传输方式
    client = Client("src/xiaohongshu_mcp_python/main.py")
    
    try:
        async with client:
            print("✅ 成功连接到FastMCP服务器")
            
            # 列出可用的工具
            tools = await client.list_tools()
            print(f"📋 可用工具: {[tool.name for tool in tools]}")
            
            # 测试登录状态检查工具
            result = await client.call_tool("xiaohongshu_check_login_status", {})
            print(f"🔍 登录状态检查结果: {result}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())