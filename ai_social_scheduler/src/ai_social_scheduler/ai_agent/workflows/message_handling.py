"""流程7：私信自动处理"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class MessageHandlingWorkflow(BaseWorkflow):
    """私信自动处理工作流
    
    流程步骤：
    1. 平台通知事件（新私信）
    2. API服务层接收
    3. AI决策引擎分析私信内容
    4. 判断是否需要人工介入
    5. 生成自动回复内容（如可自动处理）
    6. 调用小红书MCP服务回复私信
    7. 状态管理器记录私信处理记录
    8. 标记需人工处理的私信（如需要）
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="message_handling",
            description="私信自动处理"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "receive_notification",
            "analyze_message",
            "judge_human_intervention",
            "generate_reply",
            "reply_message",
            "record_handling",
            "mark_for_human",
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
        required_fields = ["message"]
        return all(field in input_data for field in required_fields)

