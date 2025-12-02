"""
Resource 资源模块

包含所有 MCP Resource 和 Resource Template 的定义
"""

from .resources import (
    register_resources,
    IMAGE_STYLES,
    NEGATIVE_PROMPTS,
    IMAGE_SIZES,
    VIDEO_STYLES,
    GENERATION_CONFIGS,
    PROMPT_TEMPLATES
)
from .templates import register_resource_templates

__all__ = [
    "register_resources",
    "register_resource_templates",
    "IMAGE_STYLES",
    "NEGATIVE_PROMPTS",
    "IMAGE_SIZES",
    "VIDEO_STYLES",
    "GENERATION_CONFIGS",
    "PROMPT_TEMPLATES"
]

