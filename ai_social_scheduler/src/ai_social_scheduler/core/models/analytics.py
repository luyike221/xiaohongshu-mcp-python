"""分析模型"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AnalyticsMetrics(BaseModel):
    """分析指标模型"""

    content_id: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    collected: int = 0
    engagement_rate: float = 0.0
    date: Optional[datetime] = None


class AnalyticsReport(BaseModel):
    """分析报告模型"""

    period_start: datetime
    period_end: datetime
    metrics: Dict[str, AnalyticsMetrics]
    trends: List[Dict[str, Any]] = []
    insights: List[str] = []
    recommendations: List[str] = []

