"""异常处理智能体"""

import asyncio
import logging
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from ...client import QwenClient
from ...tools.logging import get_logger
from ..base import BaseAgent

logger = get_logger(__name__)
langchain_logger = logging.getLogger("langchain")


class ExceptionHandlingAgent(BaseAgent):
    """异常处理智能体
    
    职责：
    - 分析异常原因
    - 评估风险影响
    - 生成处理策略
    - 执行处理动作
    """
    
    def __init__(
        self,
        name: str = "exception_handling",
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
    ):
        """初始化异常处理智能体
        
        Args:
            name: Agent名称
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数
            llm_api_key: LLM API Key（可选）
        """
        super().__init__(name=name)
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_api_key = llm_api_key
        
        # 延迟初始化的组件
        self._llm_client: Optional[QwenClient] = None
        self._agent = None
        self._initialized = False
    
    async def _initialize(self):
        """初始化Agent（懒加载）"""
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing Exception Handling Agent")
            
            # 初始化LLM客户端
            self._llm_client = QwenClient(
                model=self.llm_model,
                temperature=self.llm_temperature,
                api_key=self.llm_api_key
            )
            
            # 创建Agent
            tools = []  # TODO: 可以添加异常处理工具等
            
            self._agent = create_agent(
                model=self._llm_client.client,
                tools=tools,
                system_prompt="""你是一个专业的异常处理助手，专门负责处理数据异常和系统异常。
                
你的职责：
- 分析异常原因
- 评估风险影响
- 生成处理策略
- 执行处理动作

重要提示：
- 快速响应异常
- 准确评估风险
- 采取合适的处理策略
- 记录处理结果
"""
            )
            
            self._initialized = True
            self.logger.info("Exception Handling Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Exception Handling Agent",
                error=str(e)
            )
            raise
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行异常处理逻辑
        
        Args:
            state: 状态字典，包含：
                - exception_data: 异常数据
                - exception_type: 异常类型
                - context: 上下文信息
                - 其他相关参数
        
        Returns:
            执行结果，包含：
                - cause: 异常原因
                - impact: 影响评估
                - action: 处理动作
                - success: 是否成功
        """
        await self._initialize()
        
        try:
            # 从state中提取信息
            exception_data = state.get("exception_data", {})
            exception_type = state.get("exception_type", "unknown")
            context = state.get("context", {})
            
            self.logger.info(
                "Executing Exception Handling Agent",
                exception_type=exception_type,
                exception_data=exception_data
            )
            
            # 分析异常
            prompt = f"""
            分析以下异常并生成处理策略：
            
            异常类型：{exception_type}
            异常数据：{exception_data}
            上下文：{context}
            
            请分析：
            1. 异常原因（cause）：为什么会发生
            2. 影响评估（impact）：对业务的影响（高/中/低）
            3. 风险等级（risk_level）：高/中/低
            4. 建议处理动作（action）：暂停/调整/继续/通知
            
            返回JSON格式：
            {{
                "cause": "异常原因",
                "impact": "影响评估",
                "risk_level": "风险等级",
                "action": "处理动作",
                "details": "详细说明"
            }}
            """
            
            # 调用Agent或LLM分析异常
            if self._agent:
                messages = [HumanMessage(content=prompt)]
                result = await asyncio.wait_for(
                    self._agent.ainvoke({"messages": messages}),
                    timeout=120
                )
            else:
                messages = [HumanMessage(content=prompt)]
                response = await self._llm_client.client.ainvoke(messages)
                result = {"response": response}
            
            # 解析分析结果（这里简化处理）
            # TODO: 实现JSON解析逻辑
            analysis_result = {
                "cause": "数据异常或系统错误",
                "impact": "medium",
                "risk_level": "medium",
                "action": "adjust",
                "details": "建议调整策略或重试"
            }
            
            # 执行处理动作
            action_result = await self._execute_action(
                analysis_result["action"],
                exception_data,
                context
            )
            
            return {
                "agent": self.name,
                "cause": analysis_result["cause"],
                "impact": analysis_result["impact"],
                "risk_level": analysis_result["risk_level"],
                "action": analysis_result["action"],
                "action_result": action_result,
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(
                "Exception Handling Agent execution failed",
                error=str(e)
            )
            return {
                "agent": self.name,
                "cause": "unknown",
                "impact": "unknown",
                "risk_level": "high",
                "action": "pause",
                "action_result": {"error": str(e)},
                "success": False,
                "error": str(e)
            }
    
    async def _execute_action(
        self,
        action: str,
        exception_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行处理动作
        
        Args:
            action: 处理动作（pause/adjust/continue/notify）
            exception_data: 异常数据
            context: 上下文信息
        
        Returns:
            执行结果
        """
        self.logger.info(
            "Executing action",
            action=action,
            exception_data=exception_data
        )
        
        # TODO: 实现具体的处理动作
        # - pause: 暂停相关操作
        # - adjust: 调整策略或参数
        # - continue: 继续执行（可能已恢复）
        # - notify: 通知相关人员
        
        if action == "pause":
            # 暂停相关操作
            return {"status": "paused", "message": "操作已暂停"}
        elif action == "adjust":
            # 调整策略或参数
            return {"status": "adjusted", "message": "策略已调整"}
        elif action == "continue":
            # 继续执行
            return {"status": "continued", "message": "继续执行"}
        elif action == "notify":
            # 通知相关人员
            return {"status": "notified", "message": "已通知相关人员"}
        else:
            return {"status": "unknown", "message": "未知动作"}
    
    @property
    def agent(self):
        """获取编译后的Agent图（用于langgraph_supervisor）"""
        if not self._initialized:
            raise RuntimeError(
                f"Agent '{self.name}' not initialized. "
                "Please call _initialize() first."
            )
        return self._agent
    
    def __getattr__(self, name: str) -> Any:
        """代理方法到compiled graph（用于langgraph_supervisor）"""
        if not self._initialized:
            raise RuntimeError(f"Agent '{self.name}' not initialized.")
        return getattr(self._agent, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """使agent可调用（用于langgraph_supervisor）"""
        if not self._initialized:
            raise RuntimeError(f"Agent '{self.name}' not initialized.")
        return self._agent(*args, **kwargs)

