"""流程4：热点内容追踪与发布"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class HotTopicTrackingWorkflow(BaseWorkflow):
    """热点内容追踪与发布工作流
    
    流程步骤：
    1. 定时任务触发热点监控
    2. 调用小红书MCP服务搜索热点话题
    3. AI决策引擎分析热点相关性
    4. 策略管理器匹配内容策略
    5. AI决策引擎生成热点内容方案
    6. 调用图视频生成服务生成素材
    7. 调用小红书MCP服务发布热点内容
    8. 状态管理器记录热点追踪数据
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="hot_topic_tracking",
            description="热点内容追踪与发布"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "trigger_monitoring",
            "search_hot_topics",
            "analyze_relevance",
            "match_strategy",
            "generate_content_plan",
            "generate_material",
            "publish_content",
            "record_tracking_data",
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

