"""Pydantic 数据模型定义

定义了系统中使用的所有数据模型，包括：
- Router 决策模型
- Agent 任务上下文
- 消息类型枚举
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class NextAgent(str, Enum):
    """下一个 Agent 的选择枚举
    
    可扩展：新增 Agent 只需在此添加枚举值
    """
    XHS_AGENT = "xhs_agent"      # 小红书内容 Agent
    WAIT = "wait"                # 等待用户输入
    END = "end"                  # 结束对话
    
    # 预留扩展位置 - 未来可添加更多 Agent
    # ANALYSIS_AGENT = "analysis_agent"    # 数据分析 Agent
    # STRATEGY_AGENT = "strategy_agent"    # 策略 Agent


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 待处理
    IN_PROGRESS = "in_progress"  # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    WAITING = "waiting"          # 等待用户输入


class IntentType(str, Enum):
    """用户意图类型枚举"""
    CREATE_CONTENT = "create_content"      # 创建内容
    QUERY_STATUS = "query_status"          # 查询状态
    GET_HELP = "get_help"                  # 获取帮助
    CASUAL_CHAT = "casual_chat"            # 闲聊
    FEEDBACK = "feedback"                  # 反馈
    UNKNOWN = "unknown"                    # 未知


# ============================================================================
# Router 决策模型
# ============================================================================

class RouterDecision(BaseModel):
    """Router 的决策结果
    
    LLM 分析用户意图后生成的结构化决策
    """
    next_agent: NextAgent = Field(
        description="下一个要执行的 Agent"
    )
    intent: IntentType = Field(
        default=IntentType.UNKNOWN,
        description="识别出的用户意图"
    )
    reasoning: str = Field(
        default="",
        description="决策理由，用于调试和日志"
    )
    response: str = Field(
        default="",
        description="给用户的回复内容"
    )
    extracted_params: dict[str, Any] = Field(
        default_factory=dict,
        description="从用户消息中提取的参数"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="决策置信度"
    )


# ============================================================================
# 任务上下文模型
# ============================================================================

class TaskContext(BaseModel):
    """任务执行上下文
    
    在 Agent 之间传递的任务上下文信息
    """
    task_id: str = Field(
        default="",
        description="任务唯一标识"
    )
    task_type: str = Field(
        default="",
        description="任务类型"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="任务状态"
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="任务参数"
    )
    result: dict[str, Any] = Field(
        default_factory=dict,
        description="任务执行结果"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息（如果有）"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="更新时间"
    )
    
    def mark_in_progress(self) -> "TaskContext":
        """标记任务为处理中"""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()
        return self
    
    def mark_completed(self, result: dict[str, Any]) -> "TaskContext":
        """标记任务为已完成"""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.updated_at = datetime.now()
        return self
    
    def mark_failed(self, error: str) -> "TaskContext":
        """标记任务为失败"""
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = datetime.now()
        return self


# ============================================================================
# Agent 配置模型
# ============================================================================

class AgentConfig(BaseModel):
    """Agent 配置模型
    
    用于配置 Agent 的行为参数
    """
    name: str = Field(
        description="Agent 名称"
    )
    description: str = Field(
        default="",
        description="Agent 描述"
    )
    llm_model: str = Field(
        default="qwen-plus",
        description="使用的 LLM 模型"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM 温度参数"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        description="最大重试次数"
    )
    timeout: int = Field(
        default=60,
        ge=1,
        description="超时时间（秒）"
    )


# ============================================================================
# 图配置模型
# ============================================================================

class GraphConfig(BaseModel):
    """LangGraph 图配置"""
    
    checkpointer_enabled: bool = Field(
        default=True,
        description="是否启用状态检查点"
    )
    interrupt_before: list[str] = Field(
        default_factory=list,
        description="在哪些节点前中断"
    )
    interrupt_after: list[str] = Field(
        default_factory=list,
        description="在哪些节点后中断"
    )
    recursion_limit: int = Field(
        default=25,
        ge=1,
        description="递归限制"
    )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 枚举
    "NextAgent",
    "TaskStatus",
    "IntentType",
    # 模型
    "RouterDecision",
    "TaskContext",
    "AgentConfig",
    "GraphConfig",
]
