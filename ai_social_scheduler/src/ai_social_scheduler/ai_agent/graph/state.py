"""状态模型定义"""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Agent 状态模型"""

    # 工作流状态
    workflow_id: str
    current_agent: Optional[str]
    status: str

    # 消息和上下文
    messages: List[Dict[str, Any]]
    context: Dict[str, Any]

    # 内容相关
    content: Optional[Dict[str, Any]]
    content_history: List[Dict[str, Any]]

    # 互动相关
    interactions: List[Dict[str, Any]]

    # 分析结果
    analytics: Optional[Dict[str, Any]]

    # 错误信息
    error: Optional[str]

