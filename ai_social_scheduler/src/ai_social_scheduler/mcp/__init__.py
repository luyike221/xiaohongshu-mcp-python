"""MCP模块 - Model Context Protocol工具注册

新架构：
- MCP服务注册为LangChain Tools
- 统一的工具注册中心
- 分类管理和查询
- 供Agent使用

核心组件：
- MCPToolRegistry: 工具注册中心
- mcp_registry: 全局注册表实例
"""

from .registry import MCPToolRegistry, mcp_registry

__all__ = [
    "MCPToolRegistry",
    "mcp_registry",
]
