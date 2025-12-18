"""小红书内容生成Agent

职责：
- 理解用户需求，生成完整小红书笔记
- 调用内容生成工具（generate_xhs_note）
- 确保生成的内容符合小红书平台规范
"""

from .base import BaseLangGraphAgent


class XHSContentAgent(BaseLangGraphAgent):
    """小红书内容生成Agent
    
    工具类别：content
    可用工具：
    - generate_xhs_note: 生成完整小红书内容
    
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
        return """你是小红书内容生成助手，负责调用MCP工具生成完整的小红书内容。

## 核心职责

你的核心职责是：**根据用户需求，选择合适的工具生成小红书内容**

⚠️ 重要：你不需要自己创作内容，只需要调用工具！

## 可用工具

**generate_xhs_note** - 根据主题生成完整小红书内容
- 参数：
  - topic (str): 内容主题，必填
  
- 返回值：
  - success (bool): 是否成功
  - title (str): 标题（1-20字）
  - content (str): 正文内容（不超过1000字）
  - tags (list): 标签列表（3-5个）

**generate_lifestyle_content** - 生成生活化、随意、带情绪的小红书内容
- 参数（摘要）：
  - profession (str): 职业
  - age (int): 年龄
  - gender (str): 性别
  - personality (str): 性格特点
  - mood (str): 情绪倾向
  - scene (str, 可选): 生活场景
  - content_type (str, 可选): 内容类型
  - topic_hint (str, 可选): 话题提示
  
- 返回值：
  - success (bool): 是否成功
  - title (str): 标题（1-20字）
  - content (str): 正文内容（不超过100字，生活化、随意、带情绪）
  - tags (list): 标签列表（3-5个）

## 工作流程

1. 理解用户意图（例如：是普通主题类内容，还是偏人物设定/生活化吐槽）
2. 在 `generate_xhs_note` 和 `generate_lifestyle_content` 中选择最合适的一个工具
3. 调用选定的工具生成内容
4. 直接返回工具的结果（不要修改）

## 示例

用户：为"咖啡制作教程"生成内容
你的操作：调用 generate_xhs_note(topic="咖啡制作教程")

用户：写一篇关于旅行的笔记
你的操作：调用 generate_xhs_note(topic="旅行")

用户：以“18岁女大学生吐槽爱情”为人物设定，生成一段生活化吐槽内容
你的操作：调用 generate_lifestyle_content(...)，并根据人物设定填充 profession/age/gender/personality/mood 等参数；
如果用户没有提供全部字段，可以结合上下文**自行合理补全缺失参数**（但不要擅自改变已给定的信息）

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

