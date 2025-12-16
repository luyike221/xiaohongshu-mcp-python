"""节点基类 - 所有节点的抽象基类

重构核心：统一节点接口，支持中间件和生命周期管理
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.messages import AIMessage

from ..core.node import NodeConfig
from ..core.task import Task, TaskStatus
from ..tools.logging import get_logger


# ============================================================================
# 节点基类
# ============================================================================

class BaseNode(ABC):
    """节点基类 - 所有节点的抽象基类
    
    核心职责：
    1. 定义节点接口
    2. 提供生命周期钩子
    3. 支持中间件机制
    4. 统一错误处理
    
    设计理念：
    - 简单：核心接口只有 execute
    - 可扩展：支持钩子和中间件
    - 可观测：内置日志和监控
    - 可控制：超时、重试等由外部控制
    
    生命周期：
    1. before_execute (钩子)
    2. execute (核心方法)
    3. after_execute (钩子)
    4. on_error (错误处理)
    """
    
    def __init__(
        self,
        config: NodeConfig,
        middlewares: Optional[list] = None,
    ):
        """初始化节点
        
        Args:
            config: 节点配置
            middlewares: 中间件列表
        """
        self.config = config
        self.node_id = config.node_id
        self.name = config.name
        self.middlewares = middlewares or []
        
        self.logger = get_logger(f"node.{self.node_id}")
        
        self.logger.info(
            f"Node initialized: {self.name}",
            node_id=self.node_id,
            node_type=config.node_type.value
        )
    
    # ========================================================================
    # 核心接口
    # ========================================================================
    
    async def __call__(self, task: Task, state: dict[str, Any]) -> dict[str, Any]:
        """节点调用入口（兼容 LangGraph）
        
        这是 LangGraph 调用节点的标准接口
        
        Args:
            task: 任务对象
            state: 图状态
        
        Returns:
            更新的状态
        """
        try:
            # 执行前钩子
            await self.before_execute(task, state)
            
            # 执行核心逻辑
            result = await self.execute(task, state)
            
            # 执行后钩子
            await self.after_execute(task, state, result)
            
            return result
            
        except Exception as e:
            # 错误处理
            return await self.on_error(task, state, e)
    
    @abstractmethod
    async def execute(self, task: Task, state: dict[str, Any]) -> dict[str, Any]:
        """执行节点逻辑（子类必须实现）
        
        Args:
            task: 任务对象
            state: 图状态
        
        Returns:
            更新的状态字典
        """
        pass
    
    # ========================================================================
    # 生命周期钩子
    # ========================================================================
    
    async def before_execute(self, task: Task, state: dict[str, Any]):
        """执行前钩子
        
        可以在这里做：
        - 参数验证
        - 资源准备
        - 日志记录
        """
        self.logger.info(
            "Node execution starting",
            task_id=task.task_id,
            task_type=task.task_type.value
        )
        
        # 标记任务为运行中
        task.mark_running(self.node_id)
    
    async def after_execute(
        self,
        task: Task,
        state: dict[str, Any],
        result: dict[str, Any]
    ):
        """执行后钩子
        
        可以在这里做：
        - 结果验证
        - 资源清理
        - 日志记录
        """
        self.logger.info(
            "Node execution completed",
            task_id=task.task_id,
            node_id=self.node_id
        )
    
    async def on_error(
        self,
        task: Task,
        state: dict[str, Any],
        error: Exception
    ) -> dict[str, Any]:
        """错误处理钩子
        
        Args:
            task: 任务对象
            state: 图状态
            error: 错误对象
        
        Returns:
            更新的状态
        """
        import traceback
        
        error_stack = traceback.format_exc()
        
        self.logger.error(
            f"Node execution failed: {error}",
            task_id=task.task_id,
            node_id=self.node_id,
            exc_info=True
        )
        
        # 标记任务失败
        task.mark_failed(str(error), error_stack)
        
        # 返回错误状态
        return {
            "task": task,
            "messages": [AIMessage(content=f"执行失败: {error}")],
            "error": str(error),
        }
    
    # ========================================================================
    # 辅助方法
    # ========================================================================
    
    def validate_input(self, task: Task) -> bool:
        """验证输入参数
        
        子类可以重写此方法进行自定义验证
        """
        return True
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.config.get(key, default)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.node_id}, name={self.name})>"


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "BaseNode",
]

