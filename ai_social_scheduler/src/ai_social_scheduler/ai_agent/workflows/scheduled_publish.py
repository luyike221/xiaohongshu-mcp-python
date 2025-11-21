"""流程3：定时内容发布"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class ScheduledPublishWorkflow(BaseWorkflow):
    """定时内容发布工作流
    
    流程步骤：
    1. 定时任务事件触发
    2. AI决策引擎生成内容计划
    3. 策略管理器选择话题和模板
    4. 调用图视频生成服务生成素材
    5. 调用小红书MCP服务发布
    6. 数据分析服务收集数据
    7. 策略管理器优化后续策略
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="scheduled_publish",
            description="定时内容发布"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "trigger_scheduled_task",
            "generate_content_plan",
            "select_topic_template",
            "generate_material",
            "publish_content",
            "collect_data",
            "optimize_strategy",
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        try:
            result = await self.supervisor.execute_workflow(
                workflow_name=self.name,
                input_data=input_data,
            )
            
            return {
                "success": True,
                "workflow": self.name,
                "result": result,
            }
            
        except Exception as e:
            return await self.handle_error(e, "execute")

