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
            # 1. 先进行意图识别（如果用户请求中有request字段）
            user_request = input_data.get("request") or input_data.get("content", "")
            context = input_data.get("context", {})
            understanding_result = None
            
            if user_request:
                self.logger.info("Step 1: Understanding user request")
                understanding_result = await self.decision_engine.understand_request(
                    user_request,
                    context
                )
                await self.state_manager.record_execution_result(
                    workflow_id=workflow_id,
                    step="understand_request",
                    result=understanding_result,
                    status="success"
                )
                
                # 如果意图识别推荐的工作流与传入的工作流不一致，使用推荐的工作流
                recommended_workflow = understanding_result.get("workflow")
                if recommended_workflow and recommended_workflow != workflow_name:
                    self.logger.info(
                        "Workflow changed based on intent understanding",
                        original=workflow_name,
                        recommended=recommended_workflow
                    )
                    workflow_name = recommended_workflow
                    # 更新workflow_id
                    workflow_id = f"{workflow_name}_{input_data.get('user_id', 'unknown')}"
            
            # 2. 根据工作流类型执行预处理
            if workflow_name == "content_publish" and understanding_result:
                # 生成内容策略
                self.logger.info("Step 2: Generating content strategy")
                strategy_result = await self.strategy_manager.generate_content_strategy(
                    user_request,
                    {**context, **understanding_result}
                )
                await self.state_manager.record_execution_result(
                    workflow_id=workflow_id,
                    step="generate_strategy",
                    result=strategy_result,
                    status="success"
                )
                
                # 将理解结果和策略添加到input_data中，传递给Supervisor
                input_data["understanding"] = understanding_result
                input_data["strategy"] = strategy_result
            elif understanding_result:
                # 其他工作流也保存理解结果
                input_data["understanding"] = understanding_result
            
            # 获取或创建对应工作流的 Supervisor
            if workflow_name not in self._supervisor_cache:
                self._supervisor_cache[workflow_name] = self._create_supervisor(workflow_name)
            
            supervisor = self._supervisor_cache[workflow_name]
            
            # 构建消息（包含完整的工作流上下文）
            # 将上下文信息格式化为更易读的文本
            context_text = f"""工作流：{workflow_name}
工作流ID：{workflow_id}
用户ID：{input_data.get('user_id', 'unknown')}
用户请求：{input_data.get('request', input_data.get('content', ''))}"""
            
            # 如果有理解结果和策略，添加到上下文中
            if understanding_result:
                context_text += f"\n\n意图理解结果：\n- 意图：{understanding_result.get('intent', '')}\n- 实体：{understanding_result.get('entities', {})}"
            
            if input_data.get('strategy'):
                strategy = input_data.get('strategy')
                context_text += f"\n\n内容策略：\n- 话题：{strategy.get('topic', '')}\n- 模板：{strategy.get('template', '')}\n- 风格：{strategy.get('style', '')}\n- 关键词：{strategy.get('keywords', [])}"
            
            # 创建新的消息列表，确保没有历史消息污染
            messages = [HumanMessage(content=context_text)]
            
            # 确保使用唯一的 thread_id，避免消息历史冲突
            # 使用 workflow_id 作为 thread_id，确保每次工作流执行都有独立的消息历史
            final_config = {
                "configurable": {
                    "thread_id": workflow_id,  # 使用 workflow_id 作为 thread_id，确保唯一性
                }
            }
            if config:
                final_config["configurable"].update(config.get("configurable", {}))
            
            # 执行 Supervisor
            self.logger.info(
                "Executing Supervisor graph",
                workflow_name=workflow_name,
                thread_id=workflow_id
            )
            response = await supervisor.ainvoke(
                {"messages": messages},
                config=final_config
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

