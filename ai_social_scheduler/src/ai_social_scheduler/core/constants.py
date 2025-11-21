"""常量定义"""

# Agent 类型
class AgentType:
    """Agent 类型常量"""

    CONTENT = "content"
    INTERACTION = "interaction"
    ANALYSIS = "analysis"


# 工作流状态
class WorkflowState:
    """工作流状态常量"""

    INIT = "init"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


# 内容状态
class ContentStatus:
    """内容状态常量"""

    DRAFT = "draft"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


# 互动类型
class InteractionType:
    """互动类型常量"""

    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"
    FOLLOW = "follow"


# LLM 提供商
class LLMProvider:
    """LLM 提供商常量"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"

