"""状态模型定义"""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Agent 状态模型（LangGraph 节点之间传递的共享状态）"""

    # 基础标识
    workflow_id: str
    workflow_name: str
    user_id: str
    status: str
    current_step: Optional[str]
    error: Optional[str]
    failed_step: Optional[str]

    # 输入与上下文
    request: str
    context: Dict[str, Any]
    messages: List[Dict[str, Any]]

    # 中间产物
    understanding: Dict[str, Any]
    strategy: Dict[str, Any]
    materials: Dict[str, Any]
    content_result: Dict[str, Any]
    publish_result: Dict[str, Any]

    # 追踪记录
    logs: List[Dict[str, Any]]

