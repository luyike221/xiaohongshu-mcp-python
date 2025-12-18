"""小红书工作流子图 - 完整的内容生成到发布流程

流程：内容生成 → 图片生成 → 发布（可选）

特点：
- 使用LangGraph StateGraph管理状态
- 每个步骤由独立的Agent执行
- 支持条件路由（是否发布）
- 完全由LLM驱动决策
- 支持流式输出
"""

from typing import TypedDict, List, Any, Literal, Optional, Dict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from .base import BaseSubgraph
from ..agents import XHSContentAgent, XHSImageAgent, XHSPublishAgent
from ..core.task import Task
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 状态定义
# ============================================================================

class XHSWorkflowState(TypedDict, total=False):
    """小红书工作流状态（扩展 GraphState 以支持直接集成）
    
    状态字段说明：
    
    从 GraphState 继承的字段：
        messages: 消息历史（LangChain格式）
        task: 当前任务
        thread_id: 会话 ID
        user_id: 用户 ID
        iteration_count: 迭代计数
        metadata: 元数据
    
    工作流专有字段：
        description: 用户描述的主题或需求
        image_count: 需要生成的图片数量
        should_publish: 是否发布到小红书
    
    中间状态：
        content_result: 内容生成Agent的结果
        image_result: 图片生成Agent的结果
        publish_result: 发布Agent的结果
    
    输出字段：
        success: 整个流程是否成功
        error: 错误信息（如果失败）
        final_output: 最终输出（整合所有结果）
    """
    # 从 GraphState 继承的字段（使子图状态与主图兼容）
    messages: List[BaseMessage]
    task: Optional[Task]
    thread_id: str
    user_id: str
    iteration_count: int
    metadata: Dict[str, Any]
    
    # 工作流输入
    description: str
    image_count: int
    should_publish: bool
    
    # 中间状态
    content_result: dict
    image_result: dict
    publish_result: dict
    
    # 输出
    success: bool
    error: str
    final_output: dict


# ============================================================================
# 工作流子图
# ============================================================================

class XHSWorkflowSubgraph(BaseSubgraph):
    """小红书工作流子图
    
    完整流程：
    1. 内容生成节点：调用XHSContentAgent生成标题、正文、标签
    2. 图片生成节点：调用XHSImageAgent生成配图
    3. 发布节点（可选）：调用XHSPublishAgent发布到小红书
    
    使用示例：
        workflow = XHSWorkflowSubgraph()
        await workflow.initialize()
        
        result = await workflow.invoke({
            "description": "咖啡制作教程",
            "image_count": 3,
            "should_publish": True,
        })
        
        # 或流式输出
        async for state in workflow.stream({...}):
            print(f"当前步骤: {state}")
    """
    
    def __init__(self):
        """初始化工作流子图"""
        super().__init__(name="xhs_workflow")
        
        # 初始化Agents
        self.content_agent = XHSContentAgent()
        self.image_agent = XHSImageAgent()
        self.publish_agent = XHSPublishAgent()
    
    def _define_state_schema(self) -> type:
        """定义状态Schema"""
        return XHSWorkflowState
    
    async def _build_graph(self) -> StateGraph:
        """构建工作流图
        
        图结构：
            START
              ↓
        [内容生成节点]
              ↓
        [图片生成节点]
              ↓
          {条件路由}
           ↙    ↘
      [发布节点]  END
           ↓
          END
        """
        # 创建StateGraph
        workflow = StateGraph(XHSWorkflowState)
        
        # 添加节点
        workflow.add_node("generate_content", self._generate_content_node)
        workflow.add_node("generate_images", self._generate_images_node)
        workflow.add_node("publish", self._publish_node)
        
        # 定义边
        workflow.set_entry_point("generate_content")
        workflow.add_edge("generate_content", "generate_images")
        
        # 条件路由：是否发布
        workflow.add_conditional_edges(
            "generate_images",
            self._should_publish_router,
            {
                "publish": "publish",
                "end": END,
            }
        )
        
        workflow.add_edge("publish", END)
        
        return workflow
    
    # ========================================================================
    # 节点函数
    # ========================================================================
    
    async def _generate_content_node(self, state: XHSWorkflowState) -> XHSWorkflowState:
        """内容生成节点
        
        调用XHSContentAgent生成小红书内容大纲
        """
        # 如果 description 未设置，从 task 中提取（支持从主图集成）
        if not state.get("description"):
            task = state.get("task")
            if task:
                self.logger.info("Extracting parameters from task")
                extracted_params = task.input_data.get("extracted_params", {})
                route_decision = task.metadata.get("route_decision", {})
                route_params = route_decision.get("extracted_params", {})
                
                # 提取描述
                state["description"] = (
                    extracted_params.get("description") 
                    or route_params.get("description")
                    or task.input_data.get("user_input", "")
                )
                
                # 提取图片数量
                state["image_count"] = int(
                    extracted_params.get("image_count")
                    or route_params.get("image_count")
                    or 3
                )
                
                # 提取是否发布
                state["should_publish"] = bool(task.input_data.get("publish", True))
        
        description = state.get("description", "")
        if not description:
            self.logger.error("No description provided")
            state["success"] = False
            state["error"] = "未提供内容描述"
            return state
        
        self.logger.info(
            "Step 1: Generating content",
            description=description[:50]
        )
        
        try:
            # 确保Agent已初始化
            await self.content_agent.initialize()
            
            # 构建清晰的提示 - 说明需求与可用工具，让 Agent 自主选择
            prompt = f"""你是小红书内容生成助手，现在有一个创作需求：

主题：{description}

请你根据用户意图，在可用工具（generate_xhs_note / generate_lifestyle_content）中选择**最合适的一个**来完成创作：
- 如果是普通主题类、小红书图文笔记，优先考虑使用 generate_xhs_note(topic=...)
- 如果更偏向人物设定、生活化吐槽、带强烈情绪的内容，优先考虑使用 generate_lifestyle_content(...)

要求：
1. 必须通过工具完成内容生成，不要自己写正文
2. 工具返回什么，就原样作为最终结果返回给用户，不要修改"""
            
            # 调用内容生成Agent
            result = await self.content_agent.invoke(prompt)
            
            # 更新状态
            state["content_result"] = result
            state["messages"] = result.get("messages", [])
            
            self.logger.info("Content generation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}", exc_info=True)
            state["success"] = False
            state["error"] = f"内容生成失败: {str(e)}"
        
        return state
    
    async def _generate_images_node(self, state: XHSWorkflowState) -> XHSWorkflowState:
        """图片生成节点
        
        调用XHSImageAgent生成配图
        """
        # 如果上一步失败，跳过
        if state.get("error"):
            return state
        
        self.logger.info(
            "Step 2: Generating images",
            count=state.get("image_count", 3)
        )
        
        try:
            # 确保Agent已初始化
            await self.image_agent.initialize()
            
            # 从内容结果中提取信息
            content_result = state.get("content_result", {})
            messages = content_result.get("messages", [])
            
            # 尝试从消息中提取 generate_xhs_note 工具调用的结果
            outline_result = self._extract_outline_result(messages)
            
            # 构建提示 - 明确传递数据给Agent
            if outline_result and isinstance(outline_result, dict):
                title = outline_result.get("title", "")
                content_text = outline_result.get("content", "")
                tags = outline_result.get("tags", [])
                tags_str = " ".join([f"#{tag}" for tag in tags]) if tags else ""
                
                # 构建 full_content
                full_content = f"""标题：{title}

正文：{content_text}

标签：{tags_str}"""
                
                prompt = f"""请调用 generate_images_batch 工具生成图片。

从上游内容生成Agent接收到的数据：
- 标题：{title}
- 正文：{content_text[:100]}...
- 标签：{tags_str}

操作：
调用 generate_images_batch(
    full_content=\"\"\"{full_content}\"\"\",
    style="",  # 留空，让工具自动选择
)"""
            else:
                # 使用通用提示，让Agent自己提取
                prompt = f"""请从以下内容结果中提取title、content、tags，然后调用 generate_images_batch 工具生成图片。

内容结果：
{content_result}

操作步骤：
1. 从上述结果中提取 title、content、tags
2. 构建 full_content 参数（格式：标题+正文+标签的多行文本）
3. 调用 generate_images_batch(full_content=..., style="")"""
            
            # 调用图片生成Agent
            result = await self.image_agent.invoke(prompt)
            
            # 更新状态
            state["image_result"] = result
            
            # 如果不需要发布，这是最后一步，标记为成功
            if not state.get("should_publish"):
                state["success"] = True
                state["final_output"] = {
                    "content": state.get("content_result"),
                    "images": result,
                }
                
                # 如果有 task，更新 task 状态
                task = state.get("task")
                if task:
                    task.mark_completed(state["final_output"])
                    self.logger.info(f"Task marked as completed: {task.task_id}")
            
            self.logger.info("Image generation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}", exc_info=True)
            state["success"] = False
            state["error"] = f"图片生成失败: {str(e)}"
            
            # 更新 task 状态为失败
            task = state.get("task")
            if task:
                task.mark_failed(str(e))
        
        return state
    
    def _extract_outline_result(self, messages: list) -> dict:
        """从消息列表中提取 generate_xhs_note 的结果
        
        Args:
            messages: LangChain消息列表
        
        Returns:
            outline结果字典，如果未找到则返回None
        """
        if not messages:
            return None
        
        import json
        
        # 查找工具调用的结果（ToolMessage）
        for msg in reversed(messages):
            # 检查是否是工具消息
            if hasattr(msg, "name") and msg.name == "generate_xhs_note":
                if hasattr(msg, "content"):
                    content = msg.content
                    # 尝试解析为字典
                    if isinstance(content, str):
                        try:
                            return json.loads(content)
                        except:
                            pass
                    elif isinstance(content, dict):
                        return content
            # 或者检查最后一条消息是否包含结果
            elif msg == messages[-1] and hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, dict) and "title" in content:
                    return content
        
        return None
    
    async def _publish_node(self, state: XHSWorkflowState) -> XHSWorkflowState:
        """发布节点
        
        调用XHSPublishAgent发布到小红书
        """
        # 如果前面步骤失败，跳过
        if state.get("error"):
            return state
        
        self.logger.info("Step 3: Publishing to Xiaohongshu")
        
        try:
            # 确保Agent已初始化
            await self.publish_agent.initialize()
            
            # 从state提取数据
            content_result = state.get("content_result", {})
            image_result = state.get("image_result", {})
            
            # 提取内容信息
            outline_result = self._extract_outline_result(content_result.get("messages", []))
            
            # 提取图片URLs
            images = image_result.get("messages", [])
            image_urls = self._extract_image_urls(images)
            
            # 构建清晰的提示 - 明确传递数据给Agent
            if outline_result:
                title = outline_result.get("title", "")
                content_text = outline_result.get("content", "")
                tags = outline_result.get("tags", [])
                
                prompt = f"""请按以下步骤发布内容到小红书：

从上游Agent接收到的数据：

【内容信息】
- 标题：{title}
- 正文：{content_text[:200]}...
- 标签：{tags}

【图片信息】  
- 图片URLs：{image_urls}

操作步骤：
1. 调用 xiaohongshu_check_login_session() 检查登录状态
2. 如果未登录，提示用户需要登录
3. 如果已登录，调用 xiaohongshu_publish_content(
    title="{title}",
    content="{content_text}",  # 确保移除所有#标签
    images={image_urls},
    tags={tags}  # 确保移除#号前缀
)"""
            else:
                # 使用通用提示
                prompt = f"""请从以下结果中提取数据并发布到小红书：

内容结果：{content_result}
图片结果：{image_result}

操作步骤：
1. 检查登录状态
2. 从内容结果提取：title、content、tags
3. 从图片结果提取：图片URL列表
4. 清洗数据（移除#号等）
5. 调用 xiaohongshu_publish_content 发布"""
            
            # 调用发布Agent
            result = await self.publish_agent.invoke(prompt)
            
            # 更新状态
            state["publish_result"] = result
            state["success"] = True
            state["final_output"] = {
                "content": state.get("content_result"),
                "images": state.get("image_result"),
                "publish": result,
            }
            
            # 更新 task 状态为完成
            task = state.get("task")
            if task:
                task.mark_completed(state["final_output"])
                self.logger.info(f"Task marked as completed: {task.task_id}")
            
            self.logger.info("Publishing completed successfully")
            
        except Exception as e:
            self.logger.error(f"Publishing failed: {e}", exc_info=True)
            state["success"] = False
            state["error"] = f"发布失败: {str(e)}"
            
            # 更新 task 状态为失败
            task = state.get("task")
            if task:
                task.mark_failed(str(e))
        
        return state
    
    def _extract_image_urls(self, messages: list) -> list:
        """从图片生成结果中提取图片URLs
        
        Args:
            messages: LangChain消息列表
        
        Returns:
            图片URL列表
        """
        if not messages:
            return []
        
        import json
        
        # 查找工具调用的结果
        for msg in reversed(messages):
            if hasattr(msg, "name") and msg.name == "generate_images_batch":
                if hasattr(msg, "content"):
                    content = msg.content
                    # 尝试解析为字典
                    if isinstance(content, str):
                        try:
                            result = json.loads(content)
                            if "images" in result:
                                return [img.get("url") for img in result["images"] if "url" in img]
                        except:
                            pass
                    elif isinstance(content, dict):
                        if "images" in content:
                            return [img.get("url") for img in content["images"] if "url" in img]
        
        return []
    
    # ========================================================================
    # 路由函数
    # ========================================================================
    
    def _should_publish_router(self, state: XHSWorkflowState) -> Literal["publish", "end"]:
        """判断是否需要发布
        
        条件：
        1. should_publish为True
        2. 前面步骤没有错误
        
        Args:
            state: 当前状态
        
        Returns:
            "publish": 进入发布节点
            "end": 结束流程
        """
        should_publish = state.get("should_publish", False)
        has_error = bool(state.get("error"))
        
        if should_publish and not has_error:
            self.logger.info("Routing to publish node")
            return "publish"
        else:
            if has_error:
                self.logger.info("Skipping publish due to error")
            else:
                self.logger.info("Skipping publish (should_publish=False)")
            return "end"
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def format_result(self, state: XHSWorkflowState) -> Dict[str, Any]:
        """格式化最终结果
        
        Args:
            state: 最终状态
        
        Returns:
            格式化后的结果字典
        """
        result = {
            "success": state.get("success", False),
            "error": state.get("error"),
        }
        
        # 提取内容信息
        if "content_result" in state:
            result["content"] = state["content_result"]
        
        # 提取图片信息
        if "image_result" in state:
            result["images"] = state["image_result"]
        
        # 提取发布信息
        if "publish_result" in state:
            result["publish"] = state["publish_result"]
        
        return result


# ============================================================================
# 便捷函数
# ============================================================================

async def create_xhs_workflow_subgraph() -> XHSWorkflowSubgraph:
    """创建并初始化小红书工作流子图（工厂函数）
    
    Returns:
        已初始化的XHSWorkflowSubgraph实例
    
    使用示例:
        workflow = await create_xhs_workflow_subgraph()
        result = await workflow.invoke({
            "description": "咖啡制作教程",
            "image_count": 3,
            "should_publish": True,
        })
    """
    workflow = XHSWorkflowSubgraph()
    await workflow.initialize()
    return workflow

