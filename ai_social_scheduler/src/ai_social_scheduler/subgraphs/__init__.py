"""LangGraph Subgraphs - 业务流程编排层

新架构：
- Subgraph = 多个Agent的组合
- 使用LangGraph StateGraph管理状态流转
- 支持条件路由和循环
- 支持流式输出

已实现的Subgraphs：
- XHSWorkflowSubgraph: 小红书完整工作流（内容生成→图片生成→发布）
"""

from .base import BaseSubgraph
from .xhs_workflow_subgraph import XHSWorkflowSubgraph, XHSWorkflowState, create_xhs_workflow_subgraph

__all__ = [
    # 基类
    "BaseSubgraph",
    
    # 小红书工作流
    "XHSWorkflowSubgraph",
    "XHSWorkflowState",
    "create_xhs_workflow_subgraph",
]

