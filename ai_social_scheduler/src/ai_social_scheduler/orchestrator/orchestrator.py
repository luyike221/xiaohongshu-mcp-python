"""调度器 - 任务调度和生命周期管理

重构核心：统一的任务调度和执行
"""

from typing import Any, Optional

from langchain_core.messages import HumanMessage

from ..core.task import Task, TaskStatus, TaskType
from ..router.router_system import RouterSystem
from ..tools.logging import get_logger
from .task_queue import TaskQueue

logger = get_logger(__name__)


# ============================================================================
# 调度器
# ============================================================================

class Orchestrator:
    """调度器 - 任务调度和生命周期管理
    
    核心职责：
    1. 接收用户请求，创建任务
    2. 路由决策
    3. 任务调度
    4. 生命周期管理
    
    设计理念：
    - 统一入口：所有请求通过 Orchestrator 处理
    - 解耦：路由、调度、执行分离
    - 可观测：完整的生命周期追踪
    """
    
    def __init__(
        self,
        router_system: RouterSystem,
        task_queue: Optional[TaskQueue] = None,
        max_queue_size: int = 1000,
    ):
        """初始化调度器
        
        Args:
            router_system: 路由系统
            task_queue: 任务队列
            max_queue_size: 最大队列大小
        """
        self.router_system = router_system
        self.task_queue = task_queue or TaskQueue(max_size=max_queue_size)
        
        logger.info("Orchestrator initialized")
    
    async def submit(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None,
        messages: Optional[list] = None,
        task_type: TaskType = TaskType.CONTENT_GENERATION,
    ) -> Task:
        """提交任务
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            messages: 历史消息
            task_type: 任务类型
        
        Returns:
            Task: 创建的任务对象
        """
        logger.info("Submitting task", input_length=len(user_input))
        
        # 1. 创建任务
        task = Task(
            task_type=task_type,
            name=f"Task for: {user_input[:50]}...",
            input_data={"user_input": user_input},
            context=context or {},
        )
        
        # 2. 路由决策
        logger.debug("Calling router system", user_input=user_input[:50])
        decision = await self.router_system.route(user_input, context, messages)
        
        logger.info(
            "Route decision made",
            task_id=task.task_id,
            target_nodes=decision.target_nodes,
            target_nodes_count=len(decision.target_nodes) if decision.target_nodes else 0,
            intent=decision.intent,
            should_wait=decision.should_wait,
            confidence=decision.confidence,
            reasoning=decision.reasoning[:100] if decision.reasoning else None
        )
        
        # 3. 更新任务信息
        task.target_nodes = decision.target_nodes
        task.metadata["route_decision"] = decision.model_dump()
        task.metadata["response"] = decision.response
        
        logger.debug(
            "Task updated with decision",
            task_id=task.task_id,
            task_target_nodes=task.target_nodes,
            task_target_nodes_count=len(task.target_nodes) if task.target_nodes else 0
        )
        
        # 4. 判断是否需要等待
        if decision.should_wait or not decision.target_nodes:
            logger.warning(
                "Task will be pending",
                task_id=task.task_id,
                should_wait=decision.should_wait,
                has_target_nodes=bool(decision.target_nodes),
                target_nodes=decision.target_nodes
            )
            task.transition_to(TaskStatus.PENDING)
            logger.info("Task pending, waiting for user input", task_id=task.task_id)
            return task
        
        # 5. 入队
        await self.task_queue.enqueue(task)
        task.transition_to(TaskStatus.QUEUED)
        
        logger.info("Task queued", task_id=task.task_id)
        
        return task
    
    async def process_next(self) -> Optional[Task]:
        """处理下一个任务
        
        Returns:
            处理的任务，如果队列为空则返回 None
        """
        # 出队
        task = await self.task_queue.dequeue()
        
        if task is None:
            return None
        
        logger.info("Processing task", task_id=task.task_id)
        
        # 标记为已调度
        task.transition_to(TaskStatus.SCHEDULED)
        
        return task
    
    def get_queue_stats(self) -> dict:
        """获取队列统计信息"""
        return self.task_queue.stats()


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "Orchestrator",
]

