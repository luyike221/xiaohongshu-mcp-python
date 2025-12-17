"""小红书内容生成Agent

职责：
- 理解用户需求，生成小红书内容大纲
- 调用内容生成工具（generate_outline）
- 确保生成的内容符合小红书平台规范
"""

from .base import BaseLangGraphAgent


class XHSContentAgent(BaseLangGraphAgent):
    """小红书内容生成Agent
    
    工具类别：content
    可用工具：
    - generate_outline: 生成小红书内容大纲
    
    使用示例：
        agent = XHSContentAgent()
        await agent.initialize()
        result = await agent.invoke("帮我写一篇关于咖啡制作的小红书笔记")
    """
     
    def __init__(
        self,
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        execution_timeout: int = 240,
        **kwargs
    ):
        """初始化内容生成Agent
        
        Args:
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数（内容生成建议0.7-0.9）
            execution_timeout: Agent执行超时时间（秒），默认240秒
            **kwargs: 其他参数
        """
        super().__init__(
            name="xhs_content_agent",
            tool_categories=["content"],
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            execution_timeout=execution_timeout,
            **kwargs
        )
    
    def _default_system_prompt(self) -> str:
        """定义内容生成Agent的系统提示词"""
        return """你是小红书内容生成助手，负责调用MCP工具生成小红书内容大纲。

## 核心职责

你的唯一职责是：**调用 generate_outline 工具生成小红书内容**

⚠️ 重要：你不需要自己创作内容，只需要调用工具！

## 可用工具

**generate_outline** - 生成小红书内容大纲
- 参数：
  - topic (str): 内容主题，必填
  
- 返回值：
  - success (bool): 是否成功
  - title (str): 标题（1-20字）
  - content (str): 正文内容（不超过1000字）
  - tags (list): 标签列表（3-5个）

## 工作流程

1. 从用户输入中提取主题
2. 调用 generate_outline 工具
3. 直接返回工具的结果（不要修改）

## 示例

用户：为"咖啡制作教程"生成内容
你的操作：调用 generate_outline(topic="咖啡制作教程")

用户：写一篇关于旅行的笔记
你的操作：调用 generate_outline(topic="旅行")

记住：你只是工具调用者，让MCP工具完成实际的内容生成！"""


# 便捷函数
async def create_xhs_content_agent(**kwargs) -> XHSContentAgent:
    """创建并初始化内容生成Agent（工厂函数）
    
    Args:
        **kwargs: 传递给XHSContentAgent的参数
    
    Returns:
        已初始化的XHSContentAgent实例
    
    使用示例：
        agent = await create_xhs_content_agent()
        result = await agent.invoke("写一篇关于旅行的笔记")
    """
    agent = XHSContentAgent(**kwargs)
    await agent.initialize()
    return agent

