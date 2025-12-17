"""图构建器 - 动态构建 LangGraph

重构核心：基于配置动态构建执行图
"""

from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from ..core.task import Task
from ..nodes import NodeFactory, NodeRegistry
from ..orchestrator import Orchestrator
from ..router import RouterSystem
from ..tools.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# 图状态定义
# ============================================================================

class GraphState(TypedDict, total=False):
    """图状态定义
    
    LangGraph 需要一个 TypedDict 来定义状态
    """
    # 消息历史
    messages: list[BaseMessage]
    
    # 当前任务
    task: Optional[Task]
    
    # 会话 ID
    thread_id: str
    
    # 用户 ID
    user_id: str
    
    # 迭代计数
    iteration_count: int
    
    # 元数据
    metadata: dict[str, Any]


# ============================================================================
# 图构建器
# ============================================================================

class GraphBuilder:
    """图构建器 - 动态构建 LangGraph
    
    核心职责：
    1. 基于节点配置构建图
    2. 添加节点和边
    3. 编译图
    4. 集成路由和调度
    
    设计理念：
    - 动态构建：基于配置自动生成图结构
    - 灵活路由：集成路由系统
    - 统一接口：屏蔽底层复杂性
    """
    
    def __init__(
        self,
        orchestrator: Orchestrator,
        node_registry: Optional[NodeRegistry] = None,
        node_factory: Optional[NodeFactory] = None,
        checkpointer: Optional[MemorySaver] = None,
    ):
        """初始化图构建器
        
        Args:
            orchestrator: 调度器
            node_registry: 节点注册表
            node_factory: 节点工厂
            checkpointer: 检查点存储器
        """
        self.orchestrator = orchestrator
        self.node_registry = node_registry or NodeRegistry()
        self.node_factory = node_factory or NodeFactory(registry=self.node_registry)
        self.checkpointer = checkpointer or MemorySaver()
        
        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None
        
        logger.info("GraphBuilder initialized")
    
    # ========================================================================
    # 图构建
    # ========================================================================
    
    async def build(self) -> StateGraph:
        """构建状态图（现在是异步的，因为需要初始化子图）
        
        Returns:
            构建好的 StateGraph（未编译）
        """
        logger.info("Building graph with subgraphs as nodes...")
        
        # 创建状态图
        workflow = StateGraph(GraphState)
        
        # 1. 添加路由节点（入口）
        workflow.add_node("router", self._create_router_node())
        
        # 2. 添加子图作为节点（新架构：直接使用子图）
        successfully_added_nodes = []
        
        # 添加小红书工作流子图
        try:
            from ..subgraphs import XHSWorkflowSubgraph
            xhs_subgraph = XHSWorkflowSubgraph()
            
            # 初始化子图
            await xhs_subgraph.initialize()
            
            # 关键：直接添加编译后的子图，让 LangGraph 自动处理流式输出
            workflow.add_node("xhs_workflow", xhs_subgraph.graph)
            successfully_added_nodes.append("xhs_workflow")
            logger.info("Subgraph added to graph: xhs_workflow")
        except Exception as e:
            logger.error(f"Failed to add xhs_workflow subgraph: {e}")
        
        # 3. 添加等待节点
        workflow.add_node("wait", self._create_wait_node())
        
        # 4. 添加边
        # START -> router
        workflow.add_edge(START, "router")
        
        # router -> 条件路由
        route_map = {node_id: node_id for node_id in successfully_added_nodes}
        route_map.update({"wait": "wait", "end": END})
        
        workflow.add_conditional_edges(
            "router",
            self._route_from_router,
            route_map
        )
        
        # 所有节点 -> router（完成后回到路由）
        for node_id in successfully_added_nodes:
            workflow.add_edge(node_id, "router")
        
        # wait -> router
        workflow.add_edge("wait", "router")
        
        self._graph = workflow
        logger.info("Graph built successfully with subgraphs")
        
        return workflow
    
    async def compile(self, interrupt_before: Optional[list[str]] = None):
        """编译图（现在是异步的）
        
        Args:
            interrupt_before: 在哪些节点前中断
        
        Returns:
            编译后的可执行图
        """
        if self._graph is None:
            await self.build()
        
        # 默认在 wait 前中断
        interrupt_before = interrupt_before or ["wait"]
        
        logger.info(
            "Compiling graph",
            checkpointer=True,
            interrupt_before=interrupt_before
        )
        
        self._compiled_graph = self._graph.compile(
            checkpointer=self.checkpointer,
            interrupt_before=interrupt_before,
        )
        
        logger.info("Graph compiled successfully")
        return self._compiled_graph
    
    async def get_graph(self):
        """获取编译后的图（异步版本）"""
        if self._compiled_graph is None:
            await self.compile()
        return self._compiled_graph
    
    # ========================================================================
    # 节点创建
    # ========================================================================
    
    def _create_router_node(self):
        """创建路由节点"""
        async def router_node(state: GraphState) -> dict[str, Any]:
            """路由节点：分析意图并决定下一步"""
            messages = state.get("messages", [])
            current_task = state.get("task")
            
            # 获取最后的用户消息
            user_input = None
            last_message_index = -1
            for i, msg in enumerate(reversed(messages)):
                if hasattr(msg, "type") and msg.type == "human":
                    user_input = msg.content
                    last_message_index = len(messages) - 1 - i
                    break
            
            # 检查是否是新的用户输入（在当前任务之后）
            is_new_input = False
            if current_task and user_input:
                # 检查任务创建时的消息数量
                task_message_count = current_task.metadata.get("message_count", 0)
                is_new_input = len(messages) > task_message_count
            elif user_input:
                is_new_input = True
            
            # 如果已有任务且未完成，并且没有新输入，继续执行
            if current_task and not current_task.is_terminal() and not is_new_input:
                logger.info(f"Continuing task: {current_task.task_id}")
                return {"task": current_task}
            
            if not user_input:
                logger.warning("No user input found")
                return {
                    "task": None,
                    "messages": [AIMessage(content="请输入您的需求")],
                }
            
            # 提交任务到调度器（新输入或新任务）
            logger.info(
                "Submitting new task",
                user_input=user_input[:50],
                is_new_input=is_new_input,
                has_current_task=current_task is not None
            )
            
            task = await self.orchestrator.submit(
                user_input=user_input,
                context={
                    "thread_id": state.get("thread_id", ""),
                    "user_id": state.get("user_id", ""),
                },
                messages=messages,
            )
            
            # 记录消息数量，用于判断是否有新输入
            task.metadata["message_count"] = len(messages)
            
            # 添加响应消息
            response = task.metadata.get("response", "")
            if response:
                messages.append(AIMessage(content=response))
            
            return {
                "task": task,
                "messages": messages,
                "iteration_count": state.get("iteration_count", 0) + 1,
            }
        
        return router_node
    
    def _create_wait_node(self):
        """创建等待节点"""
        async def wait_node(state: GraphState) -> dict[str, Any]:
            """等待节点：暂停等待用户输入"""
            logger.info("Wait node reached - pausing for user input")
            return {}
        
        return wait_node
    
    def _wrap_node(self, node):
        """包装节点，使其适配 LangGraph 接口"""
        async def wrapped_node(state: GraphState) -> dict[str, Any]:
            """包装后的节点"""
            task = state.get("task")
            
            if task is None:
                logger.warning(f"No task for node: {node.node_id}")
                return {}
            
            # 执行节点
            result = await node(task, state)
            
            # 更新任务
            updated_task = result.get("task", task)
            
            # 合并消息
            new_messages = result.get("messages", [])
            messages = state.get("messages", [])
            messages.extend(new_messages)
            
            return {
                "task": updated_task,
                "messages": messages,
            }
        
        return wrapped_node
    
    
    # ========================================================================
    # 路由函数
    # ========================================================================
    
    def _route_from_router(self, state: GraphState) -> str:
        """从 router 路由到下一个节点
        
        新架构：直接路由到子图节点而不是 agent 节点
        """
        task = state.get("task")
        iteration_count = state.get("iteration_count", 0)
        
        # 检查迭代次数
        MAX_ITERATIONS = 20
        if iteration_count >= MAX_ITERATIONS:
            logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached")
            return "end"
        
        # 没有任务，等待
        if task is None:
            logger.info("No task, waiting")
            return "wait"
        
        # 任务已完成，等待
        if task.is_terminal():
            logger.info(f"Task completed: {task.task_id}")
            return "wait"
        
        # 没有目标节点，等待
        if not task.target_nodes:
            logger.info("No target nodes, waiting")
            return "wait"
        
        # 路由到第一个目标节点
        target = task.target_nodes[0]
        
        # 映射旧的 agent 节点名到新的子图节点名
        node_mapping = {
            "xhs_agent": "xhs_workflow",
            "xhs_content_agent": "xhs_workflow",
        }
        
        next_node = node_mapping.get(target, target)
        
        # wait 是特殊节点
        if next_node == "wait":
            logger.info("Routing to wait node")
            return "wait"
        
        logger.info(
            f"Routing to subgraph",
            next_node=next_node,
            original_target=target,
            task_id=task.task_id,
            iteration=iteration_count
        )
        
        return next_node


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "GraphBuilder",
    "GraphState",
]

