"""流程8：内容表现分析与优化"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class PerformanceAnalysisWorkflow(BaseWorkflow):
    """内容表现分析与优化工作流
    
    流程步骤：
    1. 定时任务触发数据分析
    2. 调用小红书MCP服务获取内容数据
    3. 数据分析服务分析内容表现
    4. AI决策引擎识别高/低表现内容特征
    5. 策略管理器提取成功模式
    6. 更新内容模板和策略库
    7. 生成内容优化建议
    8. 状态管理器记录分析结果
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="performance_analysis",
            description="内容表现分析与优化"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "trigger_analysis",
            "get_content_data",
            "analyze_performance",
            "identify_features",
            "extract_patterns",
            "update_templates",
            "generate_suggestions",
            "record_result",
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

