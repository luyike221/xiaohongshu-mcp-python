"""小红书图片生成Agent

职责：
- 根据内容大纲生成配图
- 调用图片生成工具（单张/批量）
- 确保图片风格符合小红书审美
"""

from .base import BaseLangGraphAgent


class XHSImageAgent(BaseLangGraphAgent):
    """小红书图片生成Agent
    
    工具类别：image
    可用工具：
    - generate_images_batch: 批量生成小红书风格图片（推荐）
    
    使用示例：
        agent = XHSImageAgent()
        await agent.initialize()
        result = await agent.invoke('''
            根据以下内容生成3张配图：
            主题：咖啡制作教程
            内容：手冲咖啡的步骤...
        ''')
    """
    
    def __init__(
        self,
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.8,
        execution_timeout: int = 900,  # 15分钟（图片生成可能需要很长时间）
        **kwargs
    ):
        """初始化图片生成Agent
        
        Args:
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数（图片生成建议0.8-1.0，更有创意）
            execution_timeout: 执行超时时间（秒），默认900秒（15分钟）
            **kwargs: 其他参数
        """
        super().__init__(
            name="xhs_image_agent",
            tool_categories=["image"],
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            execution_timeout=execution_timeout,
            **kwargs
        )
    
    def _default_system_prompt(self) -> str:
        """定义图片生成Agent的系统提示词"""
        return """你是小红书图片生成助手，负责调用MCP工具为内容生成配图。

## 核心职责

你的唯一职责是：**调用 generate_images_batch 工具生成图片**

⚠️ 重要：你不需要自己生成图片，只需要正确调用MCP工具！

## 可用工具

**generate_images_batch** - 批量生成小红书风格图片
- 参数：
  - full_content (str): 完整内容文本，必填
    格式：标题 + 正文 + 标签的多行文本
  - style (str): 图片风格，可选，默认空字符串（让工具自动选择）
  - max_wait_time (int): 最大等待时间（秒），可选，默认600
  
- 返回值：
  - success (bool): 是否成功
  - task_id (str): 任务ID
  - total (int): 总图片数
  - completed (int): 成功生成数
  - images (list): 图片列表，每项包含 index、url、type

## 数据流转

你会从**上游（内容生成Agent）**接收到以下信息：
- title: 标题
- content: 正文
- tags: 标签列表

你需要：
1. **从用户输入中提取这些字段**（通常在消息或结果中）
2. **构建 full_content 参数**（格式：标题+正文+标签的多行文本）
3. **调用 generate_images_batch**
4. **返回工具结果**（不要修改）

## 示例

### 场景1：从 generate_xhs_note 结果生成图片

用户输入：
```
基于以下内容生成3张配图：
标题：☕️在家做出咖啡店同款拿铁
正文：今天分享我的拿铁制作秘诀...
标签：咖啡、手冲咖啡、生活方式
```

你的操作：
调用 generate_images_batch 工具，参数如下：
- full_content: 标题、正文、标签的多行文本
- style: 空字符串（让工具自动选择风格）

### 场景2：指定风格

用户输入：
```
用动漫风格生成图片
[内容信息...]
```

你的操作：
调用 generate_images_batch 工具，参数如下：
- full_content: 从内容中提取的完整文本
- style: "动漫风格"

## 关键点

1. ✅ **从用户输入提取信息** - 识别title、content、tags
2. ✅ **构建完整文本** - 按指定格式组合
3. ✅ **style默认留空** - 除非用户明确指定
4. ✅ **直接返回结果** - 不要修改工具返回值

记住：你只是工具调用者，让MCP工具完成实际的图片生成！"""


# 便捷函数
async def create_xhs_image_agent(**kwargs) -> XHSImageAgent:
    """创建并初始化图片生成Agent（工厂函数）
    
    Args:
        **kwargs: 传递给XHSImageAgent的参数
    
    Returns:
        已初始化的XHSImageAgent实例
    
    使用示例：
        agent = await create_xhs_image_agent()
        result = await agent.invoke("生成3张咖啡主题的图片")
    """
    agent = XHSImageAgent(**kwargs)
    await agent.initialize()
    return agent

