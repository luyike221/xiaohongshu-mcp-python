"""图视频生成智能体"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from ...client import QwenClient
from ...tools.logging import get_logger
from ..base import BaseAgent

logger = get_logger(__name__)
langchain_logger = logging.getLogger("langchain")


class MaterialGeneratorAgent(BaseAgent):
    """图视频生成智能体
    
    职责：
    - 根据内容策略生成图片素材
    - 根据内容策略生成视频素材
    - 处理图片和视频
    - 生成符合要求的素材
    """
    
    def __init__(
        self,
        name: str = "material_generator",
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
    ):
        """初始化图视频生成智能体
        
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
            self.logger.info("Initializing Material Generator Agent")
            
            # 初始化LLM客户端
            self._llm_client = QwenClient(
                model=self.llm_model,
                temperature=self.llm_temperature,
                api_key=self.llm_api_key
            )
            
            # 创建Agent（使用简单的工具）
            # 这里可以添加图片生成工具、视频生成工具等
            tools = []  # TODO: 添加图片/视频生成工具
            
            self._agent = create_agent(
                model=self._llm_client.client,
                tools=tools,
                system_prompt="你是一个专业的图视频生成助手，可以根据内容策略生成高质量的图片和视频素材。"
            )
            
            self._initialized = True
            self.logger.info("Material Generator Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Material Generator Agent",
                error=str(e)
            )
            raise
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行图视频生成逻辑
        
        Args:
            state: 状态字典，包含：
                - strategy: 内容策略
                - content_type: 内容类型（image/video）
                - requirements: 生成要求
                - 其他相关参数
        
        Returns:
            执行结果，包含：
                - images: 生成的图片列表
                - videos: 生成的视频列表
                - success: 是否成功
        """
        await self._initialize()
        
        try:
            # 从state中提取信息
            strategy = state.get("strategy", {})
            content_type = state.get("content_type", "image")
            requirements = state.get("requirements", {})
            
            self.logger.info(
                "Executing Material Generator Agent",
                content_type=content_type,
                strategy=strategy
            )
            
            # 构建生成提示
            prompt = f"""
            根据以下内容策略生成{content_type}素材：
            
            策略：{strategy}
            要求：{requirements}
            
            请生成符合要求的素材。
            """
            
            # 如果使用Agent，可以调用Agent
            if self._agent:
                messages = [HumanMessage(content=prompt)]
                result = await asyncio.wait_for(
                    self._agent.ainvoke({"messages": messages}),
                    timeout=120
                )
            else:
                # 直接使用LLM生成
                messages = [HumanMessage(content=prompt)]
                response = await self._llm_client.client.ainvoke(messages)
                result = {"response": response}
            
            # 生成素材（这里简化处理，实际应该调用图片/视频生成服务）
            if content_type == "image":
                images = await self._generate_images(strategy, requirements)
                return {
                    "agent": self.name,
                    "images": images,
                    "videos": [],
                    "success": True,
                    "result": result
                }
            elif content_type == "video":
                videos = await self._generate_videos(strategy, requirements)
                return {
                    "agent": self.name,
                    "images": [],
                    "videos": videos,
                    "success": True,
                    "result": result
                }
            else:
                # 同时生成图片和视频
                images = await self._generate_images(strategy, requirements)
                videos = await self._generate_videos(strategy, requirements)
                return {
                    "agent": self.name,
                    "images": images,
                    "videos": videos,
                    "success": True,
                    "result": result
                }
            
        except Exception as e:
            self.logger.error(
                "Material Generator Agent execution failed",
                error=str(e)
            )
            return {
                "agent": self.name,
                "images": [],
                "videos": [],
                "success": False,
                "error": str(e)
            }
    
    async def _generate_images(
        self,
        strategy: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[str]:
        """生成图片素材
        
        Args:
            strategy: 内容策略
            requirements: 生成要求
        
        Returns:
            图片路径列表
        """
        # TODO: 实现图片生成逻辑
        # 这里可以调用图片生成API（如DALL-E、Midjourney等）
        self.logger.info("Generating images", strategy=strategy)
        
        # 模拟生成图片
        # 实际应该调用图片生成服务
        return []
    
    async def _generate_videos(
        self,
        strategy: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> List[str]:
        """生成视频素材
        
        Args:
            strategy: 内容策略
            requirements: 生成要求
        
        Returns:
            视频路径列表
        """
        # TODO: 实现视频生成逻辑
        # 这里可以调用视频生成API
        self.logger.info("Generating videos", strategy=strategy)
        
        # 模拟生成视频
        # 实际应该调用视频生成服务
        return []
    
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

