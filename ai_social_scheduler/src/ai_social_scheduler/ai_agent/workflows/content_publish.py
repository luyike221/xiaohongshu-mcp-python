"""流程1：用户请求内容发布（基于 LangGraph 的真正多 Agent 架构）"""

from typing import Any, Dict, List, Optional

from .base import BaseWorkflow


class ContentPublishWorkflow(BaseWorkflow):
    """用户请求内容发布工作流（LangGraph 多 Agent）
    
    架构说明：
    - 使用 LangGraph StateGraph 进行显式节点编排
    - 每个步骤都是独立的节点，通过共享状态传递数据
    - Agent 返回结构化结果而非自然语言
    - 按需加载 Agent，避免不必要的初始化开销
    
    流程步骤：
    1. entry: 初始化工作流
    2. understand_request: AI决策引擎理解用户需求
    3. generate_strategy: 策略管理器生成内容策略
    4. generate_material: 素材生成 Agent 生成图片/视频
    5. content_generation: 内容生成 Agent 创建文案和标题
    6. publish_content: 小红书 Agent 发布到平台
    7. record_result: 记录最终结果
    8. handle_error: 错误处理节点
    """

    def __init__(self, workflow_graph: Any):
        """初始化工作流
        
        Args:
            workflow_graph: 已编译的 LangGraph 工作流图
        """
        super().__init__(
            name="content_publish",
            description="用户请求内容发布（LangGraph 多 Agent）"
        )
        self.workflow_graph = workflow_graph

    def get_steps(self) -> List[str]:
        """获取工作流步骤"""
        return [
            "entry",
            "understand_request",
            "generate_strategy",
            "generate_material",
            "content_generation",
            "publish_content",
            "record_result",
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            input_data: 输入数据，包含：
                - user_id: 用户ID
                - request: 用户请求内容
                - context: 可选的上下文信息
        
        Returns:
            执行结果，包含：
                - success: 是否成功
                - workflow: 工作流名称
                - result: 完整的执行结果
                - error: 错误信息（如果失败）
        """
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input data"}

        try:
            # 准备 LangGraph 状态
            initial_state = {
                "user_id": input_data.get("user_id", "unknown"),
                "request": input_data.get("request", ""),
                "context": input_data.get("context", {}),
                "messages": [],
                "logs": [],
            }
            
            # 执行 LangGraph 工作流
            self.logger.info(
                "Executing LangGraph workflow",
                workflow=self.name,
                user_id=initial_state["user_id"]
            )
            
            final_state = await self.workflow_graph.ainvoke(initial_state)
            
            # 检查执行状态
            status = final_state.get("status", "unknown")
            if status == "failed":
                return {
                    "success": False,
                        "workflow": self.name,
                    "result": final_state.get("result", {}),
                    "error": final_state.get("error", "Unknown error"),
                    }
            
            return {
                "success": True,
                "workflow": self.name,
                "result": final_state.get("result", {}),
                "state": {
                    "workflow_id": final_state.get("workflow_id"),
                    "status": status,
                    "logs": final_state.get("logs", []),
                },
            }
            
        except Exception as e:
            self.logger.error(
                "Workflow execution failed",
                workflow=self.name,
                error=str(e)
            )
            return await self.handle_error(e, "execute")

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据
        
        必填字段：
        - request: 用户请求内容
        
        可选字段：
        - user_id: 用户ID（默认 "unknown"）
        - context: 上下文信息
        """
        return "request" in input_data and bool(input_data.get("request"))

