"""文本处理工具"""

import re
from typing import List


def clean_text(text: str) -> str:
    """清理文本"""
    # 移除多余空白
    text = re.sub(r"\s+", " ", text)
    # 移除首尾空白
    text = text.strip()
    return text


def extract_tags(text: str) -> List[str]:
    """提取标签"""
    # 提取 #标签# 格式
    tags = re.findall(r"#([^#]+)#", text)
    return tags


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

