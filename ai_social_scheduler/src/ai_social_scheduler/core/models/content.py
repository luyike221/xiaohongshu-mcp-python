"""内容模型"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Content(BaseModel):
    """内容模型"""

    id: Optional[str] = None
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    status: str = "draft"
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    post_id: Optional[str] = None
    url: Optional[str] = None


class ContentCreate(BaseModel):
    """创建内容请求模型"""

    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)

