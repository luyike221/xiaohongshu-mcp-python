"""响应策略"""

from typing import Dict, Any


async def plan_response(interaction: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """规划响应策略"""
    # TODO: 实现响应策略规划逻辑
    return {
        "should_respond": True,
        "response_type": "comment",
        "response_content": "",
    }

