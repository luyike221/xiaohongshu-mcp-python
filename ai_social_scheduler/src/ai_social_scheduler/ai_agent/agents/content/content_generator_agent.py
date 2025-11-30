"""内容生成智能体"""

import asyncio
import logging
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from ...client import QwenClient
from ...tools.logging import get_logger
from ..base import BaseAgent
from ..mcp.xhs.xhs_content_generator_service import XHSContentGeneratorService

logger = get_logger(__name__)
langchain_logger = logging.getLogger("langchain")


class ContentGeneratorAgent(BaseAgent):
    """内容生成智能体
    
    职责：
    - 根据策略和模板生成内容
    - 确保内容符合平台规范
    - 优化内容的可读性和吸引力
    - 生成合适的标题和描述
    """
    
    def __init__(
        self,
        name: str = "content_generator",
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
    ):
        """初始化内容生成智能体
        
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
        self._content_generator_service: Optional[XHSContentGeneratorService] = None
        self._initialized = False
    
    async def _initialize(self):
        """初始化Agent（懒加载）"""
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing Content Generator Agent")
            
            # 初始化LLM客户端
            self._llm_client = QwenClient(
                model=self.llm_model,
                temperature=self.llm_temperature,
                api_key=self.llm_api_key
            )
            
            # 创建Agent
            tools = []  # TODO: 可以添加内容优化工具等
            
            self._agent = create_agent(
                model=self._llm_client.client,
                tools=tools,
                system_prompt="""你是一个专业的内容生成助手，专门负责生成高质量的内容。
                
你的职责：
- 根据策略和模板生成内容
- 确保内容符合平台规范
- 优化内容的可读性和吸引力
- 生成合适的标题和描述

重要提示：
- 内容要原创、有价值
- 符合小红书平台规范
- 使用合适的语气和风格
"""
            )
            
            self._initialized = True
            self.logger.info("Content Generator Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Content Generator Agent",
                error=str(e)
            )
            raise
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行内容生成逻辑
        
        Args:
            state: 状态字典，包含：
                - strategy: 内容策略
                - template: 内容模板
                - topic: 话题
                - keywords: 关键词
                - 其他相关参数
        
        Returns:
            执行结果，包含：
                - title: 标题
                - content: 正文
                - tags: 标签
                - success: 是否成功
        """
        await self._initialize()
        
        try:
            # 从state中提取信息
            strategy = state.get("strategy", {})
            template = state.get("template", "")
            topic = state.get("topic", "")
            keywords = state.get("keywords", [])
            
            self.logger.info(
                "Executing Content Generator Agent",
                topic=topic,
                strategy=strategy
            )
            
            # 构建生成提示
            prompt = f"""
            根据以下信息生成小红书内容：
            
            话题：{topic}
            策略：{strategy}
            模板：{template}
            关键词：{keywords}
            
            请生成：
            1. 标题（title）：吸引人的标题
            2. 正文（content）：高质量的内容正文
            3. 标签（tags）：相关标签列表
            
            要求：
            - 内容要原创、有价值
            - 符合小红书平台规范
            - 使用合适的语气和风格
            - 包含相关关键词
            
            返回JSON格式：
            {{
                "title": "标题",
                "content": "正文内容",
                "tags": ["标签1", "标签2"]
            }}
            """
            
            # 调用Agent或LLM生成内容
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
            
            # 从 LLM 结果中提取内容
            try:
                # 尝试从 result 中提取消息内容
                if isinstance(result, dict):
                    # 如果是 Agent 返回的结果
                    if "messages" in result:
                        last_message = result["messages"][-1]
                        if hasattr(last_message, "content"):
                            content_text = last_message.content
                        else:
                            content_text = str(last_message)
                    elif "response" in result:
                        # 如果是直接 LLM 调用的结果
                        response_obj = result["response"]
                        if hasattr(response_obj, "content"):
                            content_text = response_obj.content
                        else:
                            content_text = str(response_obj)
                    else:
                        content_text = str(result)
                else:
                    content_text = str(result)
                
                # 尝试解析 JSON（LLM 可能返回 JSON 格式）
                import json
                import re
                
                # 查找 JSON 块
                json_match = re.search(r'\{[^{}]*"title"[^{}]*\}', content_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed = json.loads(json_str)
                    generated_content = {
                        "title": parsed.get("title", strategy.get("topic", "默认标题")),
                        "content": parsed.get("content", f"这是关于{topic}的精彩内容"),
                        "tags": parsed.get("tags", keywords or ["标签1", "标签2"])
                    }
                else:
                    # 如果无法解析 JSON，使用文本内容
                    generated_content = {
                        "title": strategy.get("topic", "默认标题"),
                        "content": content_text[:500] if len(content_text) > 500 else content_text,
                        "tags": keywords or ["标签1", "标签2"]
                    }
                    
            except Exception as parse_error:
                self.logger.warning(
                    "Failed to parse LLM output, using fallback",
                    error=str(parse_error)
                )
                # 回退方案：使用策略信息生成基本内容
            generated_content = {
                "title": strategy.get("topic", "默认标题"),
                    "content": f"这是关于{topic}的精彩内容。{', '.join(keywords) if keywords else ''}",
                "tags": keywords or ["标签1", "标签2"]
            }
            
            return {
                "agent": self.name,
                "title": generated_content["title"],
                "content": generated_content["content"],
                "tags": generated_content["tags"],
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(
                "Content Generator Agent execution failed",
                error=str(e)
            )
            return {
                "agent": self.name,
                "title": "",
                "content": "",
                "tags": [],
                "success": False,
                "error": str(e)
            }
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """运行 Agent（LangGraph 兼容接口）
        
        Args:
            state: 工作流状态，包含：
                - strategy: 内容策略
                - materials: 素材信息
                - context: 上下文信息
                - request: 用户请求
        
        Returns:
            执行结果，包含：
                - title: 标题
                - content: 正文
                - tags: 标签
                - success: 是否成功
        """
        try:
            # 从 state 中提取策略和素材
            strategy = state.get("strategy", {})
            materials = state.get("materials", {})
            context = state.get("context", {})
            request = state.get("request", "")
            topic = strategy.get("topic", "")
            
            # 优先使用 generate_outline MCP 工具生成内容
            if topic:
                try:
                    # 初始化内容生成服务
                    if not self._content_generator_service:
                        self._content_generator_service = XHSContentGeneratorService()
                        await self._content_generator_service._initialize()
                    
                    self.logger.info(
                        "Using generate_outline MCP tool to generate content",
                        topic=topic
                    )
                    
                    # 调用 generate_outline 生成大纲
                    outline_result = await self._content_generator_service.generate_outline(
                        topic=topic,
                        provider_type=context.get("provider_type", "alibaba_bailian"),
                        temperature=context.get("temperature", 0.3),
                        max_output_tokens=context.get("max_output_tokens", 8000),
                    )
                    
                    if outline_result.get("success", False):
                        # 使用从大纲中提取的 title、content、tags
                        title = outline_result.get("title", topic)
                        content = outline_result.get("content", "")
                        tags = outline_result.get("tags", [])
                        
                        # 如果没有提取到标签，使用策略中的关键词作为标签
                        if not tags:
                            tags = strategy.get("keywords", [])
                        
                        self.logger.info(
                            "Content generated successfully via generate_outline",
                            title=title[:30] if title else "",
                            content_length=len(content),
                            tags_count=len(tags)
                        )
                        
                        return {
                            "agent": self.name,
                            "title": title,
                            "content": content,
                            "tags": tags,
                            "success": True,
                            "outline": outline_result.get("outline", ""),
                            "pages": outline_result.get("pages", [])
                        }
                    else:
                        self.logger.warning(
                            "generate_outline failed, falling back to LLM generation",
                            error=outline_result.get("error", "Unknown error")
                        )
                        # 如果 generate_outline 失败，回退到原来的 LLM 生成方式
                except Exception as e:
                    self.logger.warning(
                        "Failed to use generate_outline, falling back to LLM generation",
                        error=str(e)
                    )
                    # 如果调用失败，回退到原来的 LLM 生成方式
            
            # 回退方案：使用原来的 LLM 生成方式
            exec_params = {
                "strategy": strategy,
                "topic": topic,
                "keywords": strategy.get("keywords", []),
                "template": strategy.get("template", ""),
                "materials": materials,
                "context": context,
                "request": request,
            }
            
            # 调用执行方法
            result = await self.execute(exec_params)
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Content Generator Agent run failed",
                error=str(e)
            )
            return {
                "agent": self.name,
                "title": "",
                "content": "",
                "tags": [],
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

