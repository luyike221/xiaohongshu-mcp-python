"""用户模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class User(BaseModel):
    """用户模型"""

    id: Optional[str] = None
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    created_at: Optional[datetime] = None

