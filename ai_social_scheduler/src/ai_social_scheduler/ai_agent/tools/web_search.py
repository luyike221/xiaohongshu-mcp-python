"""网络搜索工具"""

from typing import Optional
from langchain.tools import BaseTool


class WebSearchTool(BaseTool):
    """网络搜索工具"""

    name: str = "web_search"
    description: str = "搜索网络信息"

    def _run(self, query: str) -> str:
        """同步执行"""
        # TODO: 实现网络搜索逻辑
        return ""

    async def _arun(self, query: str) -> str:
        """异步执行"""
        # TODO: 实现异步网络搜索逻辑
        return ""

