"""验证器"""

from typing import List
import re


def validate_url(url: str) -> bool:
    """验证 URL"""
    pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def validate_email(email: str) -> bool:
    """验证邮箱"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_tags(tags: List[str]) -> bool:
    """验证标签"""
    if not tags:
        return True
    # 标签长度限制
    for tag in tags:
        if len(tag) > 20 or len(tag) < 1:
            return False
    return True

