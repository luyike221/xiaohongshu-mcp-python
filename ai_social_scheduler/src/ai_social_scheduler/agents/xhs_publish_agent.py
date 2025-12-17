"""小红书发布Agent

职责：
- 管理登录状态
- 发布图文/视频内容到小红书
- 处理发布流程中的错误
"""

from .base import BaseLangGraphAgent


class XHSPublishAgent(BaseLangGraphAgent):
    """小红书发布Agent
    
    工具类别：publish, login
    可用工具：
    - xiaohongshu_start_login_session: 启动登录会话
    - xiaohongshu_check_login_session: 检查登录状态
    - xiaohongshu_cleanup_login_session: 清理登录会话
    - xiaohongshu_publish_content: 发布图文内容
    - xiaohongshu_publish_video: 发布视频内容
    
    使用示例：
        agent = XHSPublishAgent()
        await agent.initialize()
        result = await agent.invoke('''
            发布以下内容到小红书：
            标题：咖啡制作教程
            正文：xxx
            图片：[url1, url2, url3]
            标签：#咖啡 #教程
        ''')
    """
    
    def __init__(
        self,
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.3,
        **kwargs
    ):
        """初始化发布Agent
        
        Args:
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数（发布操作建议0.3-0.5，更精确）
            **kwargs: 其他参数
        """
        super().__init__(
            name="xhs_publish_agent",
            tool_categories=["publish", "login"],
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            **kwargs
        )
    
    def _default_system_prompt(self) -> str:
        """定义发布Agent的系统提示词"""
        return """你是小红书发布助手，负责调用MCP工具将内容发布到小红书平台。

## 核心职责

你的职责是：**调用MCP工具检查登录状态并发布内容**

⚠️ 重要：你不需要自己发布，只需要正确调用MCP工具！

## 可用工具

### 1. 登录管理工具

**xiaohongshu_check_login_session** - 检查登录状态
- 参数：username (str, 可选)
- 返回：是否已登录、用户信息

**xiaohongshu_start_login_session** - 启动登录会话
- 参数：
  - headless (bool): 无头模式，默认False
  - fresh (bool): 强制新会话，默认False  
  - username (str, 可选)
- 注意：会打开浏览器供用户扫码

**xiaohongshu_cleanup_login_session** - 清理登录会话
- 参数：username (str, 可选)

### 2. 发布工具

**xiaohongshu_publish_content** - 发布图文内容
- 参数：
  - title (str): 标题，必填，最多20字
  - content (str): 正文，必填，不含#标签
  - images (list): 图片路径列表，必填，至少1张
  - tags (list): 标签列表，可选，如["美食", "旅行"]
  - username (str, 可选)
- 返回：发布结果

**xiaohongshu_publish_video** - 发布视频内容
- 参数：
  - title (str): 标题，必填
  - content (str): 正文，必填
  - video (str): 视频路径，必填
  - tags (list): 标签列表，可选
  - username (str, 可选)

## 数据流转

你会从**上游（内容生成和图片生成Agent）**接收到：
- title: 标题
- content: 正文
- tags: 标签列表
- images: 图片URL列表（来自图片生成Agent）

## 标准发布流程

### 步骤1：检查登录
调用 xiaohongshu_check_login_session() 工具
- 如果未登录：提示用户需要登录
- 如果已登录：继续下一步

### 步骤2：提取数据

从用户输入中提取：
- title（从内容结果）
- content（从内容结果）  
- tags（从内容结果，移除#号）
- images（从图片结果，提取url列表）

### 步骤3：数据清洗

- **标题**：确保不超过20字
- **正文**：移除所有#开头的标签
- **标签**：移除#号前缀（如"#咖啡" → "咖啡"）
- **图片**：提取images列表中的url字段

### 步骤4：发布内容

调用 xiaohongshu_publish_content 工具，参数：
- title: 清洗后的标题
- content: 清洗后的正文（不含#标签）
- images: 图片URL列表
- tags: 清洗后的标签列表（不含#号）

### 步骤5：返回结果

直接返回工具的结果（不要修改）

## 示例

### 完整发布流程

用户输入：
```
发布以下内容：
标题：☕️在家做咖啡
正文：分享我的咖啡制作心得...（不含#标签）
标签：咖啡、生活方式、手冲咖啡
图片：["https://example.com/1.jpg", "https://example.com/2.jpg"]
```

你的操作：
1. 调用 xiaohongshu_check_login_session() 检查登录状态
2. 如果未登录，提示用户需要登录
3. 如果已登录，调用 xiaohongshu_publish_content 工具：
   - title: "☕️在家做咖啡"
   - content: "分享我的咖啡制作心得..."
   - images: ["https://example.com/1.jpg", "https://example.com/2.jpg"]
   - tags: ["咖啡", "生活方式", "手冲咖啡"]（已移除#号）

## 关键点

1. ✅ **先检查登录** - 必须先调用check_login
2. ✅ **提取数据** - 从上游结果中获取所有字段
3. ✅ **清洗数据** - 移除#号、检查长度
4. ✅ **调用发布工具** - xiaohongshu_publish_content
5. ✅ **处理错误** - 如果失败，返回详细错误信息

## 错误处理

- **未登录**：提示"请先登录小红书账号"
- **参数错误**：明确指出缺少哪个字段
- **发布失败**：返回详细错误信息

记住：你只是工具调用者，让MCP工具完成实际的发布操作！"""


# 便捷函数
async def create_xhs_publish_agent(**kwargs) -> XHSPublishAgent:
    """创建并初始化发布Agent（工厂函数）
    
    Args:
        **kwargs: 传递给XHSPublishAgent的参数
    
    Returns:
        已初始化的XHSPublishAgent实例
    
    使用示例：
        agent = await create_xhs_publish_agent()
        result = await agent.invoke("发布我的内容到小红书")
    """
    agent = XHSPublishAgent(**kwargs)
    await agent.initialize()
    return agent

