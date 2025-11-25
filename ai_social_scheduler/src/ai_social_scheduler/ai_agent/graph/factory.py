"""LangGraph 工作流工厂函数 - 按需创建 Agent 和工作流"""

from typing import Any, Dict, Optional

from .workflow import create_content_publish_workflow
from ..supervisor.decision_engine import DecisionEngine
from ..supervisor.strategy_manager import StrategyManager
from ..supervisor.state_manager import StateManager
from ..agents.mcp.xhs.xiaohongshu_mcp_agent import create_xiaohongshu_mcp_agent
from ..agents.mcp.image_video.image_video_mcp_agent import create_image_video_mcp_agent
from ..agents.content.content_generator_agent import ContentGeneratorAgent
from ..tools.logging import get_logger

logger = get_logger(__name__)


async def create_content_publish_graph(
    llm_model: str = "qwen-plus",
    llm_temperature: float = 0.7,
    llm_api_key: Optional[str] = None,
    xhs_mcp_url: Optional[str] = None,
    xhs_mcp_transport: Optional[str] = None,
    image_video_mcp_url: Optional[str] = None,
    image_video_mcp_transport: Optional[str] = None,
) -> Any:
    """创建内容发布工作流图（按需加载 Agent）
    
    Args:
        llm_model: LLM模型名称
        llm_temperature: LLM温度参数
        llm_api_key: LLM API Key（可选）
        xhs_mcp_url: 小红书MCP服务地址（可选）
        xhs_mcp_transport: 小红书MCP传输方式（可选）
        image_video_mcp_url: 图像视频生成MCP服务地址（可选）
        image_video_mcp_transport: 图像视频生成MCP传输方式（可选）
    
    Returns:
        已编译的 LangGraph 工作流
    """
    logger.info("Creating content publish workflow with LangGraph")
    
    # 1. 创建决策引擎和管理器（轻量级，无需 Agent）
    # 注意：DecisionEngine 和 StrategyManager 内部会创建 QwenClient，
    # QwenClient 会从环境变量读取 API key，所以不需要传递 api_key
    decision_engine = DecisionEngine(
        model=llm_model,
        temperature=llm_temperature
    )
    
    strategy_manager = StrategyManager(
        model=llm_model,
        temperature=llm_temperature
    )
    
    state_manager = StateManager()
    
    # 2. 按需创建专业 Agent（仅创建内容发布所需的）
    logger.info("Creating Material Generator Agent")
    material_agent = await create_image_video_mcp_agent(
        name="material_generator",
        mcp_url=image_video_mcp_url,
        mcp_transport=image_video_mcp_transport,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    
    logger.info("Creating Content Generator Agent")
    content_agent = ContentGeneratorAgent(
        name="content_generator",
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    await content_agent._initialize()
    
    logger.info("Creating Xiaohongshu Publisher Agent")
    publisher_agent = await create_xiaohongshu_mcp_agent(
        name="xiaohongshu_publisher",
        mcp_url=xhs_mcp_url,
        mcp_transport=xhs_mcp_transport,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    
    # 3. 创建并编译工作流图
    workflow_graph = create_content_publish_workflow(
        decision_engine=decision_engine,
        strategy_manager=strategy_manager,
        material_agent=material_agent,
        content_agent=content_agent,
        publisher_agent=publisher_agent,
        state_manager=state_manager,
    )
    
    logger.info("Content publish workflow created successfully")
    
    return workflow_graph


async def create_workflow_by_name(
    workflow_name: str,
    config: Optional[Dict[str, Any]] = None,
) -> Any:
    """根据工作流名称创建对应的工作流图
    
    Args:
        workflow_name: 工作流名称
        config: 配置参数
    
    Returns:
        已编译的工作流图
    """
    config = config or {}
    
    if workflow_name == "content_publish":
        return await create_content_publish_graph(**config)
    else:
        raise ValueError(f"Unknown workflow: {workflow_name}")

