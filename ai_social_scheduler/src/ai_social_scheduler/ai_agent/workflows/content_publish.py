"""流程1：用户请求内容发布"""

from typing import Any, Dict, List

from .base import BaseWorkflow
from ..supervisor import Supervisor


class ContentPublishWorkflow(BaseWorkflow):
    """用户请求内容发布工作流
    
    流程步骤：
    1. API服务层接收
    2. AI决策引擎理解需求
    3. 策略管理器生成内容策略
    4. 调用图视频生成服务生成素材
    5. 调用小红书MCP服务发布内容
    6. 状态管理器记录执行结果
    7. 返回结果给用户
    """

    def __init__(self, supervisor: Supervisor):
        """初始化工作流"""
        super().__init__(
            name="content_publish",
            description="用户请求内容发布"
        )
        self.supervisor = supervisor

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "receive_request",
            "understand_request",
            "generate_strategy",
            "generate_material",
            "publish_content",
            "record_result",
            "return_result",
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input data"}

        try:
            # 执行 Supervisor 工作流
            result = await self.supervisor.execute_workflow(
                workflow_name=self.name,
                input_data=input_data,
                config={
                    "configurable": {
                        "workflow": self.name,
                        "thread_id": input_data.get("user_id", "unknown"),
                    }
                }
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
        required_fields = ["user_request"]
        return all(field in input_data for field in required_fields)

