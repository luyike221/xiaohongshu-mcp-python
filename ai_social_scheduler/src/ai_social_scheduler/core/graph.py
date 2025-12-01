"""LangGraph 图定义

定义了主工作流图的结构：

START
  │
  ▼
Router (LLM 决策)
  │
  ├─ 📥 接收消息
  ├─ 🤔 LLM 分析意图
  ├─ 🎯 做出决策
  └─ 💬 生成回复
      │
  decision.next_agent
      │
  ├──→ "xhs_agent" ──→ XHS Agent ──→ 回到 Router
  │
  ├──→ "wait" ──→ 中断等待用户输入 ──→ Router
  │
  └──→ "end" ──→ END

设计原则：
1. 可扩展 - 新增 Agent 只需注册并添加路由
2. 可中断 - 支持 wait 状态暂停等待用户输入
3. 可恢复 - 使用 checkpointer 支持会话持久化
4. 防循环 - 通过 iteration_count 限制最大迭代次数
"""

from typing import Literal, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ..agents.router import RouterAgent, create_router_agent
from ..agents.xhs.xhs_agent import XHSAgentNode, create_xhs_agent_node
from ..tools.logging import get_logger
from .models import GraphConfig, NextAgent
from .state import AgentState, should_continue

logger = get_logger(__name__)


# ============================================================================
# 常量定义
# ============================================================================

# 节点名称
NODE_ROUTER = "router"
NODE_XHS_AGENT = "xhs_agent"
NODE_WAIT = "wait"

# 最大迭代次数（防止无限循环）
MAX_ITERATIONS = 20


# ============================================================================
# 路由函数
# ============================================================================

def route_from_router(state: AgentState) -> Literal["xhs_agent", "wait", "end"]:
    """根据 Router 决策进行路由
    
    这是条件边的路由函数，根据 decision.next_agent 决定下一个节点
    
    重要：如果任务已完成，强制路由到 wait，避免重复执行
    
    Args:
        state: 当前图状态
    
    Returns:
        下一个节点名称或 END
    """
    decision = state.get("decision")
    iteration_count = state.get("iteration_count", 0)
    task_context = state.get("task_context")
    
    # 检查是否超过最大迭代次数
    if not should_continue(state, MAX_ITERATIONS):
        logger.warning(
            f"Max iterations ({MAX_ITERATIONS}) reached, ending conversation"
        )
        return "end"
    
    # 🔥 关键修复：如果任务已完成，强制路由到 wait，避免重复执行
    if task_context:
        from .models import TaskStatus
        if task_context.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            logger.info(
                f"Task already completed (status={task_context.status.value}), routing to wait"
            )
            return "wait"
    
    if decision is None:
        logger.warning("No decision found, defaulting to wait")
        return "wait"
    
    next_agent = decision.next_agent
    
    logger.info(
        f"Routing from router",
        next_agent=next_agent.value if hasattr(next_agent, 'value') else next_agent,
        iteration=iteration_count
    )
    
    # 路由映射
    if next_agent == NextAgent.XHS_AGENT:
        # 再次检查：如果任务已完成，不应该再次执行
        if task_context and task_context.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            logger.info("Task completed, preventing re-execution, routing to wait")
            return "wait"
        return "xhs_agent"
    elif next_agent == NextAgent.END:
        return "end"
    else:
        # wait 或其他情况
        return "wait"


def route_from_agent(state: AgentState) -> Literal["router"]:
    """Agent 执行完成后路由回 Router
    
    所有专业 Agent 执行完成后都返回 Router 进行下一轮决策
    
    Args:
        state: 当前图状态
    
    Returns:
        始终返回 "router"
    """
    logger.info("Agent completed, routing back to router")
    return "router"


# ============================================================================
# 等待节点（中断点）
# ============================================================================

async def wait_node(state: AgentState) -> dict:
    """等待节点 - 作为中断点
    
    这是一个特殊节点，用于标记需要等待用户输入的位置。
    配合 interrupt_before=["wait"] 使用时，图会在此节点前暂停。
    
    实际上这个节点不做任何处理，只是作为流程控制点。
    """
    logger.info("Wait node reached - conversation paused for user input")
    
    # 不修改状态，只是标记位置
    return {}


# ============================================================================
# 图构建器
# ============================================================================

class SocialSchedulerGraph:
    """社交内容调度器图
    
    封装了 LangGraph 图的构建和管理逻辑
    
    使用方式：
    ```python
    # 创建图
    graph = SocialSchedulerGraph()
    app = graph.compile()
    
    # 运行图
    result = await app.ainvoke(
        {"messages": [HumanMessage(content="帮我写一篇小红书")]},
        config={"configurable": {"thread_id": "user_123"}}
    )
    ```
    """
    
    def __init__(
        self,
        config: Optional[GraphConfig] = None,
        router: Optional[RouterAgent] = None,
        xhs_agent: Optional[XHSAgentNode] = None,
    ):
        """初始化图构建器
        
        Args:
            config: 图配置
            router: 自定义 Router Agent
            xhs_agent: 自定义 XHS Agent
        """
        self.config = config or GraphConfig()
        
        # 初始化 Agents
        self.router = router or create_router_agent()
        self.xhs_agent = xhs_agent or create_xhs_agent_node()
        
        # 图相关
        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None
        self._checkpointer = None
        
        logger.info(
            "SocialSchedulerGraph initialized",
            checkpointer_enabled=self.config.checkpointer_enabled,
            recursion_limit=self.config.recursion_limit
        )
    
    def build(self) -> StateGraph:
        """构建状态图
        
        Returns:
            构建好的 StateGraph（未编译）
        """
        logger.info("Building graph...")
        
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # ====================================================================
        # 添加节点
        # ====================================================================
        
        # Router 节点 - 入口点，负责意图分析和路由决策
        workflow.add_node(NODE_ROUTER, self.router)
        
        # XHS Agent 节点 - 小红书内容生成
        workflow.add_node(NODE_XHS_AGENT, self.xhs_agent)
        
        # Wait 节点 - 等待用户输入的中断点
        workflow.add_node(NODE_WAIT, wait_node)
        
        # ====================================================================
        # 添加边
        # ====================================================================
        
        # START -> Router
        workflow.add_edge(START, NODE_ROUTER)
        
        # Router -> 条件路由
        workflow.add_conditional_edges(
            NODE_ROUTER,
            route_from_router,
            {
                "xhs_agent": NODE_XHS_AGENT,
                "wait": NODE_WAIT,
                "end": END,
            }
        )
        
        # XHS Agent -> Router（完成任务后回到 Router）
        workflow.add_edge(NODE_XHS_AGENT, NODE_ROUTER)
        
        # Wait -> Router（用户输入新消息后继续）
        # 注意：这条边只在用户提供新输入后才会被触发
        workflow.add_edge(NODE_WAIT, NODE_ROUTER)
        
        self._graph = workflow
        logger.info("Graph built successfully")
        
        return workflow
    
    def compile(
        self,
        checkpointer: Optional[MemorySaver] = None,
        interrupt_before: Optional[list[str]] = None,
        interrupt_after: Optional[list[str]] = None,
    ):
        """编译图
        
        Args:
            checkpointer: 状态检查点器（用于持久化）
            interrupt_before: 在哪些节点前中断
            interrupt_after: 在哪些节点后中断
        
        Returns:
            编译后的可执行图
        """
        if self._graph is None:
            self.build()
        
        # 配置 checkpointer
        if self.config.checkpointer_enabled:
            self._checkpointer = checkpointer or MemorySaver()
        
        # 配置中断点
        # wait 节点前中断，允许添加新消息
        interrupt_before = interrupt_before or self.config.interrupt_before
        if NODE_WAIT not in interrupt_before:
            interrupt_before = [NODE_WAIT] + interrupt_before
        
        interrupt_after = interrupt_after or self.config.interrupt_after
        
        logger.info(
            "Compiling graph",
            checkpointer=self._checkpointer is not None,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after
        )
        
        # 编译
        self._compiled_graph = self._graph.compile(
            checkpointer=self._checkpointer,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
        )
        
        logger.info("Graph compiled successfully")
        return self._compiled_graph
    
    @property
    def graph(self):
        """获取编译后的图"""
        if self._compiled_graph is None:
            self.compile()
        return self._compiled_graph
    
    def get_state_schema(self):
        """获取状态 Schema"""
        return AgentState
    
    def visualize(self) -> str:
        """生成图的 Mermaid 可视化代码
        
        Returns:
            Mermaid 格式的图定义
        """
        if self._graph is None:
            self.build()
        
        try:
            return self._compiled_graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.warning(f"Could not generate visualization: {e}")
            return ""


# ============================================================================
# 便捷创建函数
# ============================================================================

def create_graph(
    config: Optional[GraphConfig] = None,
    checkpointer: Optional[MemorySaver] = None,
) -> SocialSchedulerGraph:
    """创建社交调度器图
    
    Args:
        config: 图配置
        checkpointer: 状态检查点器
    
    Returns:
        配置好的图实例
    
    Example:
        >>> graph = create_graph()
        >>> app = graph.compile()
        >>> result = await app.ainvoke({"messages": [...]})
    """
    graph = SocialSchedulerGraph(config=config)
    return graph


def get_compiled_graph(
    config: Optional[GraphConfig] = None,
    checkpointer: Optional[MemorySaver] = None,
):
    """获取编译好的图（便捷方法）
    
    Args:
        config: 图配置
        checkpointer: 状态检查点器
    
    Returns:
        编译后的可执行图
    
    Example:
        >>> app = get_compiled_graph()
        >>> result = await app.ainvoke(
        ...     {"messages": [HumanMessage(content="你好")]},
        ...     config={"configurable": {"thread_id": "123"}}
        ... )
    """
    graph = create_graph(config=config)
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# 对话运行器（高级封装）
# ============================================================================

class ConversationRunner:
    """对话运行器 - 简化多轮对话管理
    
    封装了会话状态管理和消息处理逻辑
    
    使用方式：
    ```python
    runner = ConversationRunner()
    
    # 发送消息
    response = await runner.send("帮我写一篇小红书")
    print(response)
    
    # 继续对话
    response = await runner.send("主题是秋天穿搭")
    ```
    """
    
    def __init__(
        self,
        thread_id: Optional[str] = None,
        config: Optional[GraphConfig] = None,
    ):
        """初始化对话运行器
        
        Args:
            thread_id: 会话 ID（用于持久化）
            config: 图配置
        """
        import uuid
        
        self.thread_id = thread_id or str(uuid.uuid4())
        self._graph = create_graph(config=config)
        self._app = self._graph.compile()
        
        logger.info(f"ConversationRunner initialized", thread_id=self.thread_id)
    
    async def send(self, message: str) -> str:
        """发送消息并获取响应
        
        Args:
            message: 用户消息
        
        Returns:
            AI 响应内容
        """
        from langchain_core.messages import HumanMessage, AIMessage
        
        logger.info(f"Sending message", thread_id=self.thread_id, message=message[:50])
        
        # 配置
        run_config = {
            "configurable": {
                "thread_id": self.thread_id,
            }
        }
        
        # 获取当前状态
        current_state = await self._app.aget_state(run_config)
        
        if current_state.values:
            # 继续现有对话 - 添加新消息并继续执行
            # 使用 update_state 添加新消息
            await self._app.aupdate_state(
                run_config,
                {"messages": [HumanMessage(content=message)]},
            )
            # 从中断点继续执行
            result = await self._app.ainvoke(None, run_config)
        else:
            # 新对话
            result = await self._app.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                run_config
            )
        
        # 提取最后的 AI 消息
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "无响应"
    
    async def get_history(self) -> list:
        """获取对话历史"""
        run_config = {"configurable": {"thread_id": self.thread_id}}
        state = await self._app.aget_state(run_config)
        return state.values.get("messages", []) if state.values else []
    
    def reset(self):
        """重置对话（生成新的 thread_id）"""
        import uuid
        self.thread_id = str(uuid.uuid4())
        logger.info(f"Conversation reset", new_thread_id=self.thread_id)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 常量
    "NODE_ROUTER",
    "NODE_XHS_AGENT", 
    "NODE_WAIT",
    "MAX_ITERATIONS",
    # 路由函数
    "route_from_router",
    "route_from_agent",
    # 图类
    "SocialSchedulerGraph",
    # 便捷函数
    "create_graph",
    "get_compiled_graph",
    # 对话运行器
    "ConversationRunner",
]
