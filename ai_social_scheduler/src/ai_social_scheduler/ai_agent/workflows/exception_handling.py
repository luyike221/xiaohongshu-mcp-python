"""流程5：数据异常处理"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class ExceptionHandlingWorkflow(BaseWorkflow):
    """数据异常处理工作流
    
    流程步骤：
    1. 数据分析服务检测到数据异常
    2. API服务层接收异常事件
    3. AI决策引擎分析异常原因
    4. 风险评估异常影响
    5. 生成处理策略（暂停/调整/继续）
    6. 直接执行处理动作（暂停发布/调整策略等）
    7. 状态管理器记录异常和处理结果
    8. 通知用户（如需要）
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="exception_handling",
            description="数据异常处理"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "detect_exception",
            "receive_exception_event",
            "analyze_exception",
            "assess_risk",
            "generate_handling_strategy",
            "execute_action",
            "record_result",
            "notify_user",
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input data"}

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

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        required_fields = ["exception_data"]
        return all(field in input_data for field in required_fields)

