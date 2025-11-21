"""互动模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Interaction(BaseModel):
    """互动模型"""

    id: Optional[str] = None
    type: str  # comment, like, share, follow
    content_id: Optional[str] = None
    user_id: str
    content: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: Optional[datetime] = None


class InteractionResponse(BaseModel):
    """互动响应模型"""

    id: Optional[str] = None
    interaction_id: str
    response_content: str
    created_at: Optional[datetime] = None

