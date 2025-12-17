"""工作流模块 - 已废弃

⚠️ 警告：此模块已废弃，请使用新的架构：

旧代码（已废弃）：
    from ..workflows import generate_xhs_content_workflow

新代码（推荐）：
    from ..subgraphs import XHSWorkflowSubgraph
    
    workflow = XHSWorkflowSubgraph()
    await workflow.initialize()
    result = await workflow.invoke({...})

详见：REFACTORING_GUIDE.md
"""

# 不再导出任何内容，保持向后兼容性（但会显示警告）
__all__ = []
