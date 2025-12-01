"""小红书MCP服务智能体"""

import asyncio
import logging
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

from ...client import QwenClient
from ...config import mcp_config
from ...tools.logging import get_logger

logger = get_logger(__name__)

# 启用 LangChain 调试日志（可选，用于追踪工具调用）
langchain_logger = logging.getLogger("langchain")
langchain_agent_logger = logging.getLogger("langchain.agents")


async def create_xiaohongshu_mcp_agent(
    name: str = "xiaohongshu_mcp",
    mcp_url: Optional[str] = None,
    mcp_transport: Optional[str] = None,
    llm_model: str = "qwen-plus",
    llm_temperature: float = 0.7,
    llm_api_key: Optional[str] = None,
) -> "XiaohongshuMCPAgent":
    """创建并初始化小红书MCP服务智能体（工厂函数）
    
    Args:
        name: Agent名称
        mcp_url: MCP服务地址
        mcp_transport: MCP传输方式
        llm_model: LLM模型名称
        llm_temperature: LLM温度参数
        llm_api_key: LLM API Key（可选，如果不提供则从环境变量读取）
    
    Returns:
        已初始化的XiaohongshuMCPAgent实例
    """
    agent = XiaohongshuMCPAgent(
        name=name,
        mcp_url=mcp_url,
        mcp_transport=mcp_transport,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    await agent._initialize()
    return agent


class XiaohongshuMCPAgent:
    """小红书MCP服务智能体
    
    职责：
    - 连接小红书MCP服务
    - 提供内容发布功能（图文/视频）
    - 提供内容浏览功能（列表/搜索/详情）
    - 提供用户信息查询功能
    - 提供互动操作功能（点赞/收藏/评论）
    - 提供登录状态检查功能
    """

    def __init__(
        self,
        name: str = "xiaohongshu_mcp",
        mcp_url: Optional[str] = None,
        mcp_transport: Optional[str] = None,
        llm_model: str = "qwen-plus",
        llm_temperature: float = 0.7,
        llm_api_key: Optional[str] = None,
    ):
        """初始化小红书MCP服务智能体
        
        Args:
            name: Agent名称
            mcp_url: MCP服务地址，默认从配置读取
            mcp_transport: MCP传输方式，默认从配置读取
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数
            llm_api_key: LLM API Key（可选，如果不提供则从环境变量读取）
        """
        self.name = name
        self.mcp_url = mcp_url or mcp_config.xiaohongshu_mcp_url
        self.mcp_transport = mcp_transport or mcp_config.xiaohongshu_mcp_transport
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.llm_api_key = llm_api_key
        self.logger = logger
        
        # 延迟初始化的组件
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._tools = None
        self._agent = None
        self._llm_client: Optional[QwenClient] = None
        self._initialized = False

    async def _initialize(self):
        """初始化MCP客户端和Agent（懒加载）"""
        if self._initialized:
            return
        
        try:
            self.logger.info(
                "Initializing Xiaohongshu MCP Agent",
                mcp_url=self.mcp_url,
                transport=self.mcp_transport
            )
            
            # 初始化LLM客户端
            self._llm_client = QwenClient(
                model=self.llm_model,
                temperature=self.llm_temperature,
                api_key=self.llm_api_key
            )
            
            # 初始化MCP客户端
            self._mcp_client = MultiServerMCPClient({
                "xiaohongshu": {
                    "url": self.mcp_url,
                    "transport": self.mcp_transport,
                }
            })
            
            # 获取MCP工具
            self.logger.info("Fetching MCP tools...")
            self._tools = await self._mcp_client.get_tools()
            self.logger.info(
                "MCP tools fetched",
                tool_count=len(self._tools),
                tool_names=[tool.name for tool in self._tools]
            )
            
            # 创建Agent（使用新的LangChain 1.0+ API）
            self.logger.info("Creating Agent with LangChain 1.0+ API...")
            # 直接传递模型对象，因为Qwen使用自定义端点
            self._agent = create_agent(
                model=self._llm_client.client,  # 传递模型对象
                tools=self._tools,
                system_prompt="你是一个专业的小红书内容运营助手，可以帮助用户发布内容、查看数据、进行互动等操作。"
            )
            
            self._initialized = True
            self.logger.info("Xiaohongshu MCP Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(
                "Failed to initialize Xiaohongshu MCP Agent",
                error=str(e),
                mcp_url=self.mcp_url
            )
            raise

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent逻辑
        
        Args:
            state: 状态字典，包含：
                - messages: 消息列表（可选）
                - content: 任务描述（可选）
                - 其他任务相关参数
        
        Returns:
            执行结果
        """
        # 确保已初始化
        await self._initialize()
        
        try:
            # 构建消息
            if "messages" in state:
                messages = state["messages"]
            elif "content" in state:
                messages = [HumanMessage(content=str(state["content"]))]
            else:
                # 从state中提取任务描述
                task_description = state.get("task", state.get("request", "处理小红书相关任务"))
                messages = [HumanMessage(content=str(task_description))]
            
            self.logger.info(
                "Executing Xiaohongshu MCP Agent",
                agent=self.name,
                message_count=len(messages),
                message_content=str(messages[0].content) if messages else "N/A"
            )
            
            # 执行Agent
            self.logger.info(
                "Invoking agent with LLM",
                agent=self.name,
                llm_model=self.llm_model,
                tool_count=len(self._tools) if self._tools else 0,
                available_tools=[tool.name for tool in self._tools] if self._tools else []
            )
            
            # 临时启用 LangChain 调试日志（如果日志级别是 DEBUG）
            original_level = langchain_logger.level
            std_logger = logging.getLogger(__name__)
            if std_logger.isEnabledFor(logging.DEBUG):
                langchain_logger.setLevel(logging.DEBUG)
                langchain_agent_logger.setLevel(logging.DEBUG)
            
            try:
                # 使用 asyncio.wait_for 添加超时保护
                timeout = self._llm_client.timeout if self._llm_client else 120
                self.logger.debug(f"Setting agent execution timeout to {timeout} seconds")
                
                result = await asyncio.wait_for(
                    self._agent.ainvoke({
                        "messages": messages
                    }),
                    timeout=timeout * 2  # Agent 执行可能需要更长时间（包含工具调用）
                )
                
                self.logger.info(
                    "Agent LLM invocation completed",
                    agent=self.name,
                    result_type=type(result).__name__,
                    has_messages="messages" in result if isinstance(result, dict) else False
                )
                
                # 记录返回的消息内容（用于调试）
                if isinstance(result, dict) and "messages" in result:
                    messages_list = result["messages"]
                    self.logger.debug(
                        "Agent returned messages",
                        message_count=len(messages_list),
                        last_message_type=type(messages_list[-1]).__name__ if messages_list else None
                    )
                    
            except asyncio.TimeoutError:
                self.logger.error(
                    "Agent execution timeout",
                    agent=self.name,
                    timeout_seconds=timeout * 2
                )
                raise TimeoutError(f"Agent execution exceeded {timeout * 2} seconds")
            except Exception as e:
                self.logger.error(
                    "Agent LLM invocation failed",
                    agent=self.name,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
            finally:
                # 恢复原始日志级别
                langchain_logger.setLevel(original_level)
                langchain_agent_logger.setLevel(original_level)
            
            self.logger.info(
                "Xiaohongshu MCP Agent execution completed",
                agent=self.name,
                has_result=result is not None
            )
            
            return {
                "agent": self.name,
                "result": result,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(
                "Xiaohongshu MCP Agent execution failed",
                agent=self.name,
                error=str(e)
            )
            return {
                "agent": self.name,
                "result": {"error": str(e)},
                "success": False
            }

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """运行Agent（包含错误处理）"""
        try:
            return await self.execute(state)
        except Exception as e:
            self.logger.error(
                "Xiaohongshu MCP Agent run failed",
                agent=self.name,
                error=str(e)
            )
            raise

    @property
    def agent(self):
        """获取编译后的Agent图（用于langgraph_supervisor）
        
        注意：此属性要求agent已初始化。如果未初始化，请使用create_xiaohongshu_mcp_agent工厂函数。
        """
        if not self._initialized:
            raise RuntimeError(
                f"Agent '{self.name}' not initialized. "
                "Please use create_xiaohongshu_mcp_agent() factory function "
                "or call _initialize() first."
            )
        return self._agent
    
    def __getattr__(self, name: str) -> Any:
        """代理方法到compiled graph（用于langgraph_supervisor）
        
        这样可以让agent直接作为compiled graph使用，同时保留name属性
        """
        if not self._initialized:
            raise RuntimeError(
                f"Agent '{self.name}' not initialized. "
                "Please use create_xiaohongshu_mcp_agent() factory function."
            )
        # 代理所有未定义的属性到compiled graph
        return getattr(self._agent, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """使agent可调用（用于langgraph_supervisor）
        
        注意：这需要agent已初始化
        """
        if not self._initialized:
            raise RuntimeError(
                f"Agent '{self.name}' not initialized. "
                "Please use create_xiaohongshu_mcp_agent() factory function."
            )
        # 直接调用compiled graph
        return self._agent(*args, **kwargs)

    async def check_login_status(self) -> Dict[str, Any]:
        """检查登录状态（便捷方法）"""
        await self._initialize()
        
        login_tool = next(
            (tool for tool in self._tools if "login" in tool.name.lower() and "status" in tool.name.lower()),
            None
        )
        
        if not login_tool:
            # 尝试查找其他可能的登录状态工具
            login_tool = next(
                (tool for tool in self._tools if "check_login" in tool.name.lower()),
                None
            )
        
        if login_tool:
            result = await login_tool.ainvoke({})
            return {"logged_in": True, "status": result}
        else:
            return {"logged_in": False, "error": "Login status tool not found"}

    async def publish_content(
        self,
        title: str,
        content: str,
        images: Optional[list] = None,
        tags: Optional[list] = None,
    ) -> Dict[str, Any]:
        """发布图文内容（便捷方法）
        
        Args:
            title: 标题
            content: 正文
            images: 图片列表（路径或URL）
            tags: 标签列表
        """
        await self._initialize()
        
        publish_tool = next(
            (tool for tool in self._tools if "publish_content" in tool.name.lower()),
            None
        )
        
        if not publish_tool:
            raise ValueError("publish_content tool not found in MCP tools")
        
        params = {
            "title": title,
            "content": content,
        }
        
        if images:
            params["images"] = images
        if tags:
            params["tags"] = tags
        
        result = await publish_tool.ainvoke(params)
        return result

    async def publish_with_video(
        self,
        title: str,
        content: str,
        video_path: str,
        tags: Optional[list] = None,
    ) -> Dict[str, Any]:
        """发布视频内容（便捷方法）
        
        Args:
            title: 标题
            content: 正文
            video_path: 视频文件路径
            tags: 标签列表
        """
        await self._initialize()
        
        video_tool = next(
            (tool for tool in self._tools if "publish_with_video" in tool.name.lower() or "video" in tool.name.lower()),
            None
        )
        
        if not video_tool:
            raise ValueError("publish_with_video tool not found in MCP tools")
        
        params = {
            "title": title,
            "content": content,
            "video_path": video_path,
        }
        
        if tags:
            params["tags"] = tags
        
        result = await video_tool.ainvoke(params)
        return result

    async def close(self):
        """关闭MCP客户端连接"""
        if self._mcp_client:
            # MultiServerMCPClient 可能需要清理资源
            # 根据实际API调整
            self._mcp_client = None
            self._initialized = False
            self.logger.info("Xiaohongshu MCP Agent closed")

