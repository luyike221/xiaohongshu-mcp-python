"""数据分析智能体"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from ...client import QwenClient
from ...tools.logging import get_logger
from ..base import BaseAgent
from .collector import collect_analytics_data, collect_content_metrics

logger = get_logger(__name__)
langchain_logger = logging.getLogger("langchain")


class DataAnalysisAgent(BaseAgent):
    """数据分析智能体
    
    职责：
    - 收集内容数据
    - 分析内容表现
    - 识别高/低表现内容特征
    - 生成分析报告
    """
    
    def __init__(
        self,
        name: str = "data_analysis",
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
    ):
        """初始化数据分析智能体
        
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
            self.logger.info("Initializing Data Analysis Agent")
            
            # 初始化LLM客户端
            self._llm_client = QwenClient(
                model=self.llm_model,
                temperature=self.llm_temperature,
                api_key=self.llm_api_key
            )
            
            # 创建Agent
            tools = []  # TODO: 可以添加数据分析工具等
            
            self._agent = create_agent(
                model=self._llm_client.client,
                tools=tools,
                system_prompt="""你是一个专业的数据分析助手，专门负责分析内容数据。
                
你的职责：
- 收集内容数据
- 分析内容表现
- 识别高/低表现内容特征
- 生成分析报告

重要提示：
- 分析要准确、深入
- 提供有价值的洞察
- 支持数据驱动的决策
"""
            )
            
            self._initialized = True
            self.logger.info("Data Analysis Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Data Analysis Agent",
                error=str(e)
            )
            raise
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据分析逻辑
        
        Args:
            state: 状态字典，包含：
                - content_ids: 内容ID列表
                - analysis_type: 分析类型
                - date_range: 日期范围
                - 其他相关参数
        
        Returns:
            执行结果，包含：
                - metrics: 指标数据
                - insights: 洞察
                - recommendations: 建议
                - success: 是否成功
        """
        await self._initialize()
        
        try:
            # 从state中提取信息
            content_ids = state.get("content_ids", [])
            analysis_type = state.get("analysis_type", "performance")
            date_range = state.get("date_range", {})
            
            self.logger.info(
                "Executing Data Analysis Agent",
                analysis_type=analysis_type,
                content_count=len(content_ids)
            )
            
            # 收集数据
            if content_ids:
                metrics = await collect_content_metrics(content_ids)
            else:
                # 收集时间段数据
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)  # 默认7天
                metrics_data = await collect_analytics_data(start_date, end_date)
                metrics = {"data": metrics_data}
            
            # 分析数据
            prompt = f"""
            分析以下内容数据：
            
            分析类型：{analysis_type}
            指标数据：{metrics}
            
            请分析：
            1. 内容表现指标（点赞、评论、收藏、分享等）
            2. 高表现内容的特征
            3. 低表现内容的特征
            4. 改进建议
            
            返回JSON格式：
            {{
                "metrics": {{}},
                "insights": ["洞察1", "洞察2"],
                "recommendations": ["建议1", "建议2"]
            }}
            """
            
            # 调用Agent或LLM分析数据
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
                "metrics": metrics,
                "insights": ["高表现内容通常包含热门话题", "发布时间影响内容表现"],
                "recommendations": ["优化发布时间", "增加互动元素"]
            }
            
            return {
                "agent": self.name,
                "metrics": analysis_result["metrics"],
                "insights": analysis_result["insights"],
                "recommendations": analysis_result["recommendations"],
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(
                "Data Analysis Agent execution failed",
                error=str(e)
            )
            return {
                "agent": self.name,
                "metrics": {},
                "insights": [],
                "recommendations": [],
                "success": False,
                "error": str(e)
            }
    
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

