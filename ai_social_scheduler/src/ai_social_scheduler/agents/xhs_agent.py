"""小红书 Agent - 基于新架构实现

重构核心：继承 BaseNode，集成到新架构
"""

from typing import Any

from langchain_core.messages import AIMessage

from ..core.task import Task, TaskType
from ..nodes import BaseNode, NodeRegistry
from ..tools.logging import get_logger
from ..workflows import generate_xhs_content_workflow

logger = get_logger(__name__)


# ============================================================================
# 小红书 Agent
# ============================================================================

@NodeRegistry.register_node("xhs_agent")
class XHSAgent(BaseNode):
    """小红书内容生成 Agent
    
    功能：
    1. 生成小红书笔记内容（标题、正文）
    2. 生成配图
    3. 发布到小红书平台
    
    特点：
    - 基于 BaseNode，支持生命周期钩子
    - 支持中间件（日志、重试等）
    - 统一错误处理
    """
    
    async def execute(self, task: Task, state: dict[str, Any]) -> dict[str, Any]:
        """执行小红书内容生成
        
        Args:
            task: 任务对象
            state: 图状态
        
        Returns:
            更新的状态
        """
        logger.info("XHSAgent executing", task_id=task.task_id)
        
        # 1. 提取参数
        description = self._extract_description(task)
        image_count = self._extract_image_count(task)
        publish = self._should_publish(task)
        
        logger.info(
            "XHS content generation started",
            description=description[:50],
            image_count=image_count,
            publish=publish
        )
        
        # 2. 调用工作流生成内容
        try:
            result = await generate_xhs_content_workflow(
                description=description,
                image_count=image_count,
                publish=publish,
            )
            
            # 3. 处理结果
            if result.get("success"):
                return self._handle_success(task, result)
            else:
                return self._handle_failure(task, result)
        
        except Exception as e:
            logger.error(f"XHS workflow failed: {e}", exc_info=True)
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
        """处理成功结果"""
        content = result.get("content", {})
        images = result.get("images", [])
        publish_result = result.get("publish", {})
        
        # 构建输出数据
        output_data = {
            "success": True,
            "title": content.get("title", ""),
            "content": content.get("content", ""),
            "images_count": len(images),
            "images": images,
        }
        
        # 发布信息
        if publish_result:
            output_data["published"] = publish_result.get("success", False)
            output_data["note_id"] = publish_result.get("note_id")
        
        # 标记任务完成
        task.mark_completed(output_data)
        
        # 生成用户友好的消息
        message = self._format_success_message(output_data)
        
        logger.info(
            "XHS content generated successfully",
            task_id=task.task_id,
            title=output_data["title"][:30]
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
        """格式化成功消息"""
        lines = ["✅ 小红书内容已生成"]
        
        title = output_data.get("title", "")
        if title:
            lines.append(f"标题：{title}")
        
        images_count = output_data.get("images_count", 0)
        if images_count > 0:
            lines.append(f"图片：{images_count}张")
        
        if output_data.get("published"):
            lines.append("状态：已发布")
            note_id = output_data.get("note_id")
            if note_id:
                lines.append(f"笔记ID：{note_id}")
        else:
            lines.append("状态：未发布")
        
        return "\n".join(lines)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "XHSAgent",
]

