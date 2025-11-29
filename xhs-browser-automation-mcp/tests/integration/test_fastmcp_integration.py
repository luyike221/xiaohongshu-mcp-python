"""
FastMCP集成测试

测试完整的MCP服务器功能，包括工具调用和客户端连接
"""
import pytest
import asyncio
from pathlib import Path
from fastmcp import Client


class TestFastMCPIntegration:
    """FastMCP集成测试"""

    @pytest.fixture
    def mcp_server_path(self):
        """MCP服务器脚本路径"""
        return "src/xiaohongshu_mcp_python/main.py"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_startup_and_tools_list(self, mcp_server_path):
        """测试服务器启动和工具列表"""
        async with Client(mcp_server_path) as client:
            # 获取工具列表
            tools = await client.list_tools()
            
            # 验证所有预期工具都存在
            expected_tools = [
                "xiaohongshu_check_login_status",
                "xiaohongshu_get_qrcode", 
                "xiaohongshu_wait_for_login",
                "xiaohongshu_login",
                "xiaohongshu_logout"
            ]
            
            tool_names = [tool.name for tool in tools.tools]
            
            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"工具 {expected_tool} 未找到"
            
            assert len(tools.tools) == len(expected_tools)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_login_status_tool(self, mcp_server_path):
        """测试检查登录状态工具"""
        async with Client(mcp_server_path) as client:
            # 调用检查登录状态工具
            result = await client.call_tool("xiaohongshu_check_login_status")
            
            # 验证返回结果结构
            assert hasattr(result, 'content')
            assert len(result.content) > 0
            
            # 解析结果内容
            content = result.content[0]
            assert hasattr(content, 'text')
            
            # 验证返回的JSON结构包含必要字段
            import json
            data = json.loads(content.text)
            
            assert 'is_logged_in' in data
            assert 'status' in data
            assert 'message' in data
            assert isinstance(data['is_logged_in'], bool)
            assert isinstance(data['status'], str)
            assert isinstance(data['message'], str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_qrcode_tool(self, mcp_server_path):
        """测试获取二维码工具"""
        async with Client(mcp_server_path) as client:
            # 调用获取二维码工具
            result = await client.call_tool("xiaohongshu_get_qrcode")
            
            # 验证返回结果结构
            assert hasattr(result, 'content')
            assert len(result.content) > 0
            
            content = result.content[0]
            assert hasattr(content, 'text')
            
            # 解析结果内容
            import json
            data = json.loads(content.text)
            
            assert 'success' in data
            assert 'qr_code' in data
            assert 'message' in data
            assert isinstance(data['success'], bool)
            assert isinstance(data['message'], str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logout_tool(self, mcp_server_path):
        """测试登出工具"""
        async with Client(mcp_server_path) as client:
            # 调用登出工具
            result = await client.call_tool("xiaohongshu_logout")
            
            # 验证返回结果结构
            assert hasattr(result, 'content')
            assert len(result.content) > 0
            
            content = result.content[0]
            assert hasattr(content, 'text')
            
            # 解析结果内容
            import json
            data = json.loads(content.text)
            
            assert 'success' in data
            assert 'message' in data
            assert isinstance(data['success'], bool)
            assert isinstance(data['message'], str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_tool_with_params(self, mcp_server_path):
        """测试带参数的登录工具"""
        async with Client(mcp_server_path) as client:
            # 调用登录工具（使用测试参数）
            result = await client.call_tool(
                "xiaohongshu_login",
                arguments={
                    "username": "test_user",
                    "password": "test_password"
                }
            )
            
            # 验证返回结果结构
            assert hasattr(result, 'content')
            assert len(result.content) > 0
            
            content = result.content[0]
            assert hasattr(content, 'text')
            
            # 解析结果内容
            import json
            data = json.loads(content.text)
            
            assert 'success' in data
            assert 'status' in data
            assert 'message' in data
            assert isinstance(data['success'], bool)
            assert isinstance(data['status'], str)
            assert isinstance(data['message'], str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_wait_for_login_tool_with_timeout(self, mcp_server_path):
        """测试带超时参数的等待登录工具"""
        async with Client(mcp_server_path) as client:
            # 调用等待登录工具（使用短超时时间）
            result = await client.call_tool(
                "xiaohongshu_wait_for_login",
                arguments={"timeout": 5}
            )
            
            # 验证返回结果结构
            assert hasattr(result, 'content')
            assert len(result.content) > 0
            
            content = result.content[0]
            assert hasattr(content, 'text')
            
            # 解析结果内容
            import json
            data = json.loads(content.text)
            
            assert 'success' in data
            assert 'status' in data
            assert 'message' in data
            assert isinstance(data['success'], bool)
            assert isinstance(data['status'], str)
            assert isinstance(data['message'], str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_tool_calls_sequence(self, mcp_server_path):
        """测试多个工具调用序列"""
        async with Client(mcp_server_path) as client:
            # 1. 检查登录状态
            status_result = await client.call_tool("xiaohongshu_check_login_status")
            assert hasattr(status_result, 'content')
            
            # 2. 登出（确保清理状态）
            logout_result = await client.call_tool("xiaohongshu_logout")
            assert hasattr(logout_result, 'content')
            
            # 3. 再次检查登录状态
            status_result2 = await client.call_tool("xiaohongshu_check_login_status")
            assert hasattr(status_result2, 'content')
            
            # 验证状态一致性
            import json
            status_data = json.loads(status_result2.content[0].text)
            assert status_data['is_logged_in'] is False

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mcp_server_path):
        """测试并发工具调用"""
        async with Client(mcp_server_path) as client:
            # 并发调用多个工具
            tasks = [
                client.call_tool("xiaohongshu_check_login_status"),
                client.call_tool("xiaohongshu_logout"),
                client.call_tool("xiaohongshu_check_login_status")
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证所有调用都成功完成
            for result in results:
                assert not isinstance(result, Exception)
                assert hasattr(result, 'content')
                assert len(result.content) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_server_stability_long_running(self, mcp_server_path):
        """测试服务器长时间运行稳定性"""
        async with Client(mcp_server_path) as client:
            # 连续调用工具多次
            for i in range(10):
                result = await client.call_tool("xiaohongshu_check_login_status")
                assert hasattr(result, 'content')
                
                # 短暂延迟
                await asyncio.sleep(0.1)
            
            # 验证服务器仍然响应
            final_result = await client.call_tool("xiaohongshu_logout")
            assert hasattr(final_result, 'content')