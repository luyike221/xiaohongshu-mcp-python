"""Supervisor 工厂函数 - 创建并初始化 Supervisor 和所有智能体"""

from typing import List, Optional

from .supervisor import Supervisor
from .decision_engine import DecisionEngine
from .strategy_manager import StrategyManager
from .state_manager import StateManager
from ..client import QwenClient
from ..agents.mcp.xhs.xiaohongshu_mcp_agent import create_xiaohongshu_mcp_agent
from ..agents.mcp.image_video.image_video_mcp_agent import create_image_video_mcp_agent
from ..agents.content.content_generator_agent import ContentGeneratorAgent
from ..agents.analysis.data_analysis_agent import DataAnalysisAgent
from ..agents.exception.exception_handling_agent import ExceptionHandlingAgent
from ..tools.logging import get_logger

logger = get_logger(__name__)


async def create_supervisor_with_agents(
    llm_model: str = "qwen-plus",
    llm_temperature: float = 0.7,
    llm_api_key: Optional[str] = None,
    mcp_url: Optional[str] = None,
    mcp_transport: Optional[str] = None,
    image_video_mcp_url: Optional[str] = None,
    image_video_mcp_transport: Optional[str] = None,
) -> Supervisor:
    """创建并初始化 Supervisor 和所有智能体
    
    Args:
        llm_model: LLM模型名称
        llm_temperature: LLM温度参数
        llm_api_key: LLM API Key（可选）
        mcp_url: 小红书MCP服务地址（可选）
        mcp_transport: MCP传输方式（可选）
        image_video_mcp_url: 图像视频生成MCP服务地址（可选）
        image_video_mcp_transport: 图像视频生成MCP传输方式（可选）
    
    Returns:
        已初始化的Supervisor实例
    """
    logger.info("Creating Supervisor with all agents")
    
    # 初始化LLM模型（用于Supervisor）
    model = QwenClient(
        model=llm_model,
        temperature=llm_temperature,
        api_key=llm_api_key
    )
    
    # 创建所有专业智能体
    agents: List = []
    
    # 1. 小红书MCP服务智能体
    logger.info("Creating Xiaohongshu MCP Agent")
    xhs_agent = await create_xiaohongshu_mcp_agent(
        name="xiaohongshu_mcp",
        mcp_url=mcp_url,
        mcp_transport=mcp_transport,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    agents.append(xhs_agent)
    
    # 2. 图视频生成智能体（使用ImageVideoMCPAgent）
    logger.info("Creating Image Video MCP Agent (Material Generator)")
    material_agent = await create_image_video_mcp_agent(
        name="material_generator",  # 保持名称一致以兼容现有提示词
        mcp_url=image_video_mcp_url,
        mcp_transport=image_video_mcp_transport,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    agents.append(material_agent)
    
    # 3. 内容生成智能体
    logger.info("Creating Content Generator Agent")
    content_agent = ContentGeneratorAgent(
        name="content_generator",
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    await content_agent._initialize()
    agents.append(content_agent)
    
    # 4. 数据分析智能体
    logger.info("Creating Data Analysis Agent")
    analysis_agent = DataAnalysisAgent(
        name="data_analysis",
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    await analysis_agent._initialize()
    agents.append(analysis_agent)
    
    # 5. 异常处理智能体
    logger.info("Creating Exception Handling Agent")
    exception_agent = ExceptionHandlingAgent(
        name="exception_handling",
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_api_key=llm_api_key,
    )
    await exception_agent._initialize()
    agents.append(exception_agent)
    
    # 创建决策引擎、策略管理器和状态管理器
    decision_engine = DecisionEngine(
        model=llm_model,
        temperature=llm_temperature
    )
    
    strategy_manager = StrategyManager(
        model=llm_model,
        temperature=llm_temperature
    )
    
    state_manager = StateManager()
    
    # 创建Supervisor
    supervisor = Supervisor(
        agents=agents,
        model=model.client,  # 传递LangChain模型对象
        decision_engine=decision_engine,
        strategy_manager=strategy_manager,
        state_manager=state_manager,
    )
    
    logger.info(
        "Supervisor created successfully",
        agent_count=len(agents),
        agent_names=[agent.name for agent in agents]
    )
    
    return supervisor

