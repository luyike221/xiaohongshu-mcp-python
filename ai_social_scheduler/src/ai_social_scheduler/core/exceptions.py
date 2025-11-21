"""自定义异常"""


class XiaohongshuAgentError(Exception):
    """基础异常类"""

    pass


class ConfigurationError(XiaohongshuAgentError):
    """配置错误"""

    pass


class LLMError(XiaohongshuAgentError):
    """LLM 调用错误"""

    pass


class StorageError(XiaohongshuAgentError):
    """存储错误"""

    pass


class WorkflowError(XiaohongshuAgentError):
    """工作流错误"""

    pass


class AgentError(XiaohongshuAgentError):
    """Agent 错误"""

    pass


class ValidationError(XiaohongshuAgentError):
    """验证错误"""

    pass

