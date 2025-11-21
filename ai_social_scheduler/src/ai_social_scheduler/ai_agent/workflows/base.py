"""工作流基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..tools.logging import get_logger

logger = get_logger(__name__)


class BaseWorkflow(ABC):
    """工作流基类
    
    所有工作流都应该继承这个基类，实现统一的接口。
    """

    def __init__(self, name: str, description: str):
        """初始化工作流
        
        Args:
            name: 工作流名称
            description: 工作流描述
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f"{__name__}.{name}")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流
        
        Args:
            input_data: 输入数据
        
        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def get_steps(self) -> List[str]:
        """获取工作流步骤列表
        
        Returns:
            步骤列表
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据
        
        Args:
            input_data: 输入数据
        
        Returns:
            是否有效
        """
        # 默认实现：总是返回 True
        # 子类可以重写此方法进行输入验证
        return True

    async def handle_error(self, error: Exception, step: str) -> Dict[str, Any]:
        """处理错误
        
        Args:
            error: 错误对象
            step: 出错的步骤
        
        Returns:
            错误处理结果
        """
        self.logger.error(
            "Workflow error",
            workflow=self.name,
            step=step,
            error=str(error)
        )
        
        return {
            "success": False,
            "error": str(error),
            "step": step,
        }

