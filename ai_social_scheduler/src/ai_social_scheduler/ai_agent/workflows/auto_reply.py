"""流程2：自动回复评论"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class AutoReplyWorkflow(BaseWorkflow):
    """自动回复评论工作流
    
    流程步骤：
    1. 平台通知事件（新评论）
    2. API服务层接收
    3. AI决策引擎分析评论内容
    4. 生成回复内容
    5. 调用小红书MCP服务回复评论
    6. 状态管理器更新互动记录
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="auto_reply",
            description="自动回复评论"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "receive_notification",
            "analyze_comment",
            "generate_reply",
            "reply_comment",
            "update_interaction",
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
        required_fields = ["comment"]
        return all(field in input_data for field in required_fields)

