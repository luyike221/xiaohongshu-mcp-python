"""图片生成工具"""

from typing import Optional
from langchain.tools import BaseTool


class ImageGenTool(BaseTool):
    """图片生成工具"""

    name: str = "image_gen"
    description: str = "生成图片"

    def _run(self, prompt: str) -> str:
        """同步执行"""
        # TODO: 实现图片生成逻辑
        return ""

    async def _arun(self, prompt: str) -> str:
        """异步执行"""
        # TODO: 实现异步图片生成逻辑
        return ""

