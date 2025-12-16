"""小红书运营 AI Agent - 新架构

主要组件：
- SocialSchedulerApp: 应用主入口
- RouterSystem: 智能路由系统
- NodeRegistry: 节点注册表
- Orchestrator: 任务调度器

使用示例：
    from ai_social_scheduler import SocialSchedulerApp
    
    app = SocialSchedulerApp()
    await app.initialize()
    response = await app.chat("你好", thread_id="user_001")
"""

__version__ = "0.2.0"  # 新架构版本

# 导出新架构核心组件
from .app import SocialSchedulerApp
from .core import (
    IntentType,
    NextAgent,
    RouterDecision,
    TaskContext,
    TaskStatus,
)

__all__ = [
    # 版本
    "__version__",
    # 应用
    "SocialSchedulerApp",
    # 枚举
    "NextAgent",
    "TaskStatus",
    "IntentType",
    # 模型
    "RouterDecision",
    "TaskContext",
]
