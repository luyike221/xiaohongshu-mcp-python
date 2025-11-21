"""Supervisor 主类 - 中央协调者"""

from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langgraph_supervisor import create_supervisor

from .decision_engine import DecisionEngine
from .strategy_manager import StrategyManager
from .state_manager import StateManager
from ..prompts import SUPERVISOR_PROMPT
from ..tools.logging import get_logger

logger = get_logger(__name__)


class Supervisor:
    """Supervisor - 中央协调者
    
    职责：
    - 协调各个专业智能体
    - 控制工作流执行
    - 管理全局状态
    - 处理异常和分支
    """

    def __init__(
        self,
        agents: List[Any],
        model: Any,
        decision_engine: Optional[DecisionEngine] = None,
        strategy_manager: Optional[StrategyManager] = None,
        state_manager: Optional[StateManager] = None,
    ):
        """初始化 Supervisor
        
        Args:
            agents: 专业智能体列表
            model: LLM 模型
            decision_engine: AI决策引擎
            strategy_manager: 策略管理器
            state_manager: 状态管理器
        """
        self.agents = agents
        self.model = model
        self.decision_engine = decision_engine or DecisionEngine()
        self.strategy_manager = strategy_manager or StrategyManager()
        self.state_manager = state_manager or StateManager()
        self.logger = logger
        
        # Supervisor 图将在执行工作流时根据工作流名称动态创建
        self._supervisor_cache: Dict[str, Any] = {}

    def _create_supervisor(self, workflow_name: Optional[str] = None):
        """创建 Supervisor 图
        
        Args:
            workflow_name: 工作流名称，用于选择对应的提示词
        """
        from ..prompts.supervisor import (
            CONTENT_PUBLISH_SUPERVISOR_PROMPT,
            AUTO_REPLY_SUPERVISOR_PROMPT,
            SCHEDULED_PUBLISH_SUPERVISOR_PROMPT,
            HOT_TOPIC_TRACKING_SUPERVISOR_PROMPT,
            EXCEPTION_HANDLING_SUPERVISOR_PROMPT,
            COMPETITOR_ANALYSIS_SUPERVISOR_PROMPT,
            MESSAGE_HANDLING_SUPERVISOR_PROMPT,
            PERFORMANCE_ANALYSIS_SUPERVISOR_PROMPT,
        )
        
        # 根据工作流选择对应的提示词
        workflow_prompts = {
            "content_publish": CONTENT_PUBLISH_SUPERVISOR_PROMPT,
            "auto_reply": AUTO_REPLY_SUPERVISOR_PROMPT,
            "scheduled_publish": SCHEDULED_PUBLISH_SUPERVISOR_PROMPT,
            "hot_topic_tracking": HOT_TOPIC_TRACKING_SUPERVISOR_PROMPT,
            "exception_handling": EXCEPTION_HANDLING_SUPERVISOR_PROMPT,
            "competitor_analysis": COMPETITOR_ANALYSIS_SUPERVISOR_PROMPT,
            "message_handling": MESSAGE_HANDLING_SUPERVISOR_PROMPT,
            "performance_analysis": PERFORMANCE_ANALYSIS_SUPERVISOR_PROMPT,
        }
        
        # 选择提示词，如果没有匹配的则使用通用提示词
        base_prompt = workflow_prompts.get(workflow_name, SUPERVISOR_PROMPT)
        
        agent_list = "\n".join([f"- {agent.name}" for agent in self.agents])
        prompt = base_prompt.format(agent_list=agent_list)
        
        supervisor = create_supervisor(
            agents=self.agents,
            model=self.model,
            prompt=prompt,
        ).compile()
        
        return supervisor

    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            workflow_name: 工作流名称
            input_data: 输入数据
            config: 配置
        
        Returns:
            执行结果
        """
        self.logger.info(
            "Workflow execution started",
            workflow_name=workflow_name,
            input_data=input_data
        )
        
        # 记录工作流开始
        workflow_id = f"{workflow_name}_{input_data.get('user_id', 'unknown')}"
        await self.state_manager.record_execution_result(
            workflow_id=workflow_id,
            step="start",
            result={"workflow_name": workflow_name},
            status="running"
        )
        
        try:
            # 获取或创建对应工作流的 Supervisor
            if workflow_name not in self._supervisor_cache:
                self._supervisor_cache[workflow_name] = self._create_supervisor(workflow_name)
            
            supervisor = self._supervisor_cache[workflow_name]
            
            # 构建消息
            messages = [HumanMessage(content=str(input_data))]
            
            # 执行 Supervisor
            response = await supervisor.ainvoke(
                {"messages": messages},
                config=config or {}
            )
            
            # 记录成功
            await self.state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="complete",
                result=response,
                status="success"
            )
            
            self.logger.info(
                "Workflow execution completed",
                workflow_name=workflow_name,
                workflow_id=workflow_id
            )
            
            return response
            
        except Exception as e:
            # 记录失败
            await self.state_manager.record_execution_result(
                workflow_id=workflow_id,
                step="error",
                result={"error": str(e)},
                status="failed"
            )
            
            self.logger.error(
                "Workflow execution failed",
                workflow_name=workflow_name,
                workflow_id=workflow_id,
                error=str(e)
            )
            
            raise

    def get_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态
        
        Args:
            workflow_id: 工作流ID
        
        Returns:
            状态数据
        """
        return self.state_manager.get_state(workflow_id)

