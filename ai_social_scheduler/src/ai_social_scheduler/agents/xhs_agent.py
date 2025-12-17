"""小红书 Agent - 基于LangGraph子图重构

新架构：
- 不再使用命令式workflow
- 使用XHSWorkflowSubgraph（LangGraph子图）
- 完全由LLM驱动决策
- 更高的灵活性和可扩展性
"""

from typing import Any

from langchain_core.messages import AIMessage

from ..core.task import Task, TaskType
from ..nodes import BaseNode, NodeRegistry
from ..tools.logging import get_logger
from ..subgraphs import XHSWorkflowSubgraph

logger = get_logger(__name__)


# ============================================================================
# 小红书 Agent
# ============================================================================

@NodeRegistry.register_node("xhs_agent")
class XHSAgent(BaseNode):
    """小红书内容生成 Agent（基于LangGraph子图）
    
    功能：
    1. 生成小红书笔记内容（标题、正文）
    2. 生成配图
    3. 发布到小红书平台
    
    新架构特点：
    - 使用LangGraph子图进行流程编排
    - 每个步骤由独立的Agent执行
    - LLM自主决策工具调用
    - 支持流式输出
    - 灵活的条件路由
    """
    
    def __init__(self, *args, **kwargs):
        """初始化节点"""
        super().__init__(*args, **kwargs)
        # 初始化工作流子图
        self.workflow_subgraph = XHSWorkflowSubgraph()
    
    async def execute(self, task: Task, state: dict[str, Any]) -> dict[str, Any]:
        """执行小红书内容生成
        
        Args:
            task: 任务对象
            state: 图状态
        
        Returns:
            更新的状态
        """
        logger.info("XHSAgent executing (using LangGraph subgraph)", task_id=task.task_id)
        
        # 1. 提取参数
        description = self._extract_description(task)
        image_count = self._extract_image_count(task)
        should_publish = self._should_publish(task)
        
        logger.info(
            "XHS content generation started",
            description=description[:50],
            image_count=image_count,
            should_publish=should_publish
        )
        
        # 2. 调用LangGraph子图
        try:
            result = await self.workflow_subgraph.invoke({
                "description": description,
                "image_count": image_count,
                "should_publish": should_publish,
                "messages": [],
            })
            
            # 3. 处理结果
            if result.get("success"):
                return self._handle_success(task, result)
            else:
                return self._handle_failure(task, result)
        
        except Exception as e:
            logger.error(f"XHS workflow subgraph failed: {e}", exc_info=True)
            return self._handle_error(task, e)
    
    # ========================================================================
    # 参数提取
    # ========================================================================
    
    def _extract_description(self, task: Task) -> str:
        """提取内容描述"""
        # 优先从提取的参数获取
        description = task.input_data.get("extracted_params", {}).get("description")
        
        if description:
            return description
        
        # 其次从路由决策获取
        route_decision = task.metadata.get("route_decision", {})
        description = route_decision.get("extracted_params", {}).get("description")
        
        if description:
            return description
        
        # 最后从用户输入获取
        user_input = task.input_data.get("user_input", "")
        return user_input
    
    def _extract_image_count(self, task: Task) -> int:
        """提取图片数量"""
        # 从提取的参数获取
        count = task.input_data.get("extracted_params", {}).get("image_count")
        
        if count is not None:
            return int(count)
        
        # 从路由决策获取
        route_decision = task.metadata.get("route_decision", {})
        count = route_decision.get("extracted_params", {}).get("image_count")
        
        if count is not None:
            return int(count)
        
        # 默认值
        return self.get_config_value("max_images", 3)
    
    def _should_publish(self, task: Task) -> bool:
        """是否应该发布"""
        # 从任务参数获取
        publish = task.input_data.get("publish")
        
        if publish is not None:
            return bool(publish)
        
        # 从配置获取
        return self.get_config_value("auto_publish", True)
    
    # ========================================================================
    # 结果处理
    # ========================================================================
    
    def _handle_success(self, task: Task, result: dict) -> dict[str, Any]:
        """处理成功结果
        
        新架构：从LangGraph子图结果中提取信息
        """
        # 提取各个步骤的结果
        content_result = result.get("content_result", {})
        image_result = result.get("image_result", {})
        publish_result = result.get("publish_result", {})
        
        # 构建输出数据
        output_data = {
            "success": True,
            "content_result": content_result,
            "image_result": image_result,
            "publish_result": publish_result if publish_result else None,
        }
        
        # 标记任务完成
        task.mark_completed(output_data)
        
        # 生成用户友好的消息
        message = self._format_success_message(output_data)
        
        logger.info(
            "XHS content generated successfully (via subgraph)",
            task_id=task.task_id
        )
        
        return {
            "task": task,
            "messages": [AIMessage(content=message)],
        }
    
    def _handle_failure(self, task: Task, result: dict) -> dict[str, Any]:
        """处理失败结果"""
        error_msg = result.get("error", "未知错误")
        
        # 标记任务失败
        task.mark_failed(error_msg)
        
        message = f"❌ 小红书内容生成失败\n错误：{error_msg}"
        
        logger.error(
            "XHS content generation failed",
            task_id=task.task_id,
            error=error_msg
        )
        
        return {
            "task": task,
            "messages": [AIMessage(content=message)],
        }
    
    def _handle_error(self, task: Task, error: Exception) -> dict[str, Any]:
        """处理异常"""
        error_msg = str(error)
        
        # 标记任务失败
        task.mark_failed(error_msg)
        
        message = f"❌ 小红书内容生成出错\n错误：{error_msg}"
        
        return {
            "task": task,
            "messages": [AIMessage(content=message)],
        }
    
    def _format_success_message(self, output_data: dict) -> str:
        """格式化成功消息
        
        新架构：从子图结果中提取消息
        """
        lines = ["✅ 小红书内容已生成（使用LangGraph子图）"]
        
        # 内容信息
        content_result = output_data.get("content_result", {})
        if content_result:
            lines.append("✓ 内容生成完成")
        
        # 图片信息
        image_result = output_data.get("image_result", {})
        if image_result:
            lines.append("✓ 图片生成完成")
        
        # 发布信息
        publish_result = output_data.get("publish_result")
        if publish_result:
            lines.append("✓ 发布完成")
        else:
            lines.append("○ 未发布")
        
        return "\n".join(lines)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "XHSAgent",
]

