"""小红书内容发布节点 - 作为 LangGraph 中的一个节点

这个节点可以被上层 Agent/Supervisor 调用
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from ...client import QwenClient
from ...tools.logging import get_logger
from ...tools.xhs.content_generator import _generate_content_workflow

logger = get_logger(__name__)


# ============================================================================
# 1. 定义工具
# ============================================================================

class ContentGenerationInput(BaseModel):
    """内容生成工具的输入参数"""
    description: str = Field(
        description="内容描述或主题"
    )
    image_count: int = Field(
        default=3,
        ge=1,
        le=9,
        description="图片数量，范围 1-9"
    )


async def generate_xhs_content_tool(
    description: str,
    image_count: int = 3,
) -> str:
    """生成并发布小红书内容"""
    try:
        logger.info(
            "XHS Node: Generating content",
            description=description[:50],
            image_count=image_count
        )
        
        result = await _generate_content_workflow(
            description=description,
            image_count=image_count,
            publish=True,
        )
        
        if result.get("success"):
            content = result.get("content", {})
            title = content.get("title", "")
            images_count = len(result.get("images", []))
            publish_result = result.get("publish", {})
            
            message = f"✅ 小红书内容已生成\n"
            message += f"标题：{title}\n"
            message += f"图片：{images_count}张\n"
            
            if publish_result and publish_result.get("success"):
                note_id = publish_result.get("note_id", "")
                message += f"状态：已发布\n"
                if note_id:
                    message += f"笔记ID：{note_id}"
            
            return message
        else:
            return f"❌ 生成失败：{result.get('error', '未知错误')}"
            
    except Exception as e:
        logger.error("XHS Node: Tool execution failed", error=str(e))
        return f"❌ 执行出错：{str(e)}"


def create_xhs_tool() -> StructuredTool:
    """创建小红书生成工具"""
    return StructuredTool.from_function(
        func=generate_xhs_content_tool,
        name="generate_xhs_content",
        description="生成并发布小红书内容。根据描述生成标题、正文和配图并发布。",
        args_schema=ContentGenerationInput,
        coroutine=generate_xhs_content_tool,
    )


# ============================================================================
# 2. 小红书 Agent 节点
# ============================================================================

class XHSAgentNode:
    """小红书内容发布 Agent 节点
    
    可以作为 LangGraph 中的一个节点被调用
    """
    
    def __init__(
        self,
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
    ):
        """初始化节点
        
        Args:
            llm_model: LLM 模型名称
            llm_temperature: 温度参数
        """
        self.logger = logger
        
        # 初始化 LLM
        llm_client = QwenClient(
            model=llm_model,
            temperature=llm_temperature
        )
        self.llm = llm_client.client
        
        # 创建工具
        self.tool = create_xhs_tool()
        self.tools = [self.tool]
        
        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 系统提示词
        self.system_prompt = SystemMessage(content="""你是小红书内容生成专家。

当收到生成小红书内容的请求时：
1. 分析用户的内容需求（主题、图片数量等）
2. 调用 generate_xhs_content 工具生成内容
3. 返回生成结果

重要：
- 默认生成 3 张图片
- 必须从用户消息中提取内容描述
- 如果信息不足，说明需要更多信息
""")
        
        self.logger.info(
            "XHS Agent Node initialized",
            model=llm_model,
        )
    
    async def __call__(self, state: dict) -> dict:
        """节点执行函数（作为 LangGraph 节点调用）
        
        Args:
            state: 图的状态，必须包含 'messages' 字段
        
        Returns:
            更新后的状态
        """
        messages = state["messages"]
        task_context = state.get("task_context")
        
        self.logger.info(
            "XHS Node: Processing request",
            message_count=len(messages)
        )
        
        # 更新任务状态为处理中
        if task_context:
            from ...core.models import TaskStatus
            task_context.mark_in_progress()
        
        # 添加系统提示词
        messages_with_system = [self.system_prompt] + list(messages)
        
        # 调用 LLM
        response = await self.llm_with_tools.ainvoke(messages_with_system)
        
        # 如果有工具调用，执行工具
        if hasattr(response, "tool_calls") and response.tool_calls:
            self.logger.info(
                "XHS Node: Executing tools",
                tool_count=len(response.tool_calls)
            )
            
            result_dict = {}
            task_success = True
            error_message = None
            tool_result = None
            
            try:
                # 执行工具
                tool_node = ToolNode(self.tools)
                tool_result = await tool_node.ainvoke({
                    "messages": messages_with_system + [response]
                })
                
                # 检查工具执行结果是否包含错误
                tool_messages = tool_result.get("messages", [])
                if tool_messages:
                    last_tool_msg = tool_messages[-1]
                    if hasattr(last_tool_msg, "content"):
                        tool_result_content = last_tool_msg.content
                        # 检查是否包含错误标识
                        if isinstance(tool_result_content, str):
                            # 检查各种错误标识
                            error_indicators = ["❌", "失败", "错误", "出错", "exception", "error", "failed"]
                            if any(indicator in tool_result_content.lower() for indicator in error_indicators):
                                task_success = False
                                error_message = tool_result_content
                                self.logger.warning(
                                    "XHS Node: Tool returned error result",
                                    error=error_message
                                )
                
                # 再次调用 LLM 生成最终响应
                final_messages = messages_with_system + [response] + tool_result["messages"]
                final_response = await self.llm.ainvoke(final_messages)
                
            except Exception as e:
                # 🔥 关键修复：捕获工具执行异常
                self.logger.error(
                    "XHS Node: Tool execution failed",
                    error=str(e),
                    exc_info=True
                )
                task_success = False
                error_message = str(e)
                
                # 生成错误响应消息
                from langchain_core.messages import AIMessage
                final_response = AIMessage(
                    content=f"抱歉，执行过程中遇到错误：{str(e)}"
                )
            
            # 更新任务状态
            if task_context:
                from ...core.models import TaskStatus
                if task_success and tool_result:
                    # 任务成功
                    tool_messages = tool_result.get("messages", [])
                    result_info = {}
                    if tool_messages:
                        last_tool_msg = tool_messages[-1]
                        if hasattr(last_tool_msg, "content"):
                            result_info["tool_result"] = last_tool_msg.content
                    
                    task_context.mark_completed(result_info)
                    self.logger.info(
                        "XHS Node: Task completed and marked as COMPLETED",
                        task_id=task_context.task_id
                    )
                else:
                    # 任务失败
                    task_context.mark_failed(error_message or "Unknown error")
                    self.logger.warning(
                        "XHS Node: Task failed and marked as FAILED",
                        task_id=task_context.task_id,
                        error=error_message
                    )
                
                result_dict["task_context"] = task_context
            
            self.logger.info(f"XHS Node: Task {'completed' if task_success else 'failed'}")
            return {
                "messages": [final_response],
                **result_dict
            }
        
        # 没有工具调用，直接返回响应
        # 如果没有工具调用，也标记为已完成（可能是简单查询）
        if task_context:
            from ...core.models import TaskStatus
            task_context.mark_completed({"message": "No tool execution needed"})
            self.logger.info("XHS Node: Responded without tool execution, task marked as completed")
            return {
                "messages": [response],
                "task_context": task_context
            }
        
        self.logger.info("XHS Node: Responded without tool execution")
        return {"messages": [response]}


# ============================================================================
# 3. 便捷创建函数
# ============================================================================

def create_xhs_agent_node(
    llm_model: str = "qwen-plus",
    llm_temperature: float = 0.7,
) -> XHSAgentNode:
    """创建小红书 Agent 节点
    
    Args:
        llm_model: LLM 模型
        llm_temperature: 温度参数
    
    Returns:
        可调用的节点实例
    
    Example:
        >>> xhs_node = create_xhs_agent_node()
        >>> # 在上层图中使用
        >>> workflow.add_node("xhs_agent", xhs_node)
    """
    return XHSAgentNode(
        llm_model=llm_model,
        llm_temperature=llm_temperature,
    )