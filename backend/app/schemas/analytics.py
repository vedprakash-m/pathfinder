"""Analytics-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalyticsQuery(BaseModel):
    """Schema for analytics query."""
    metric: str = Field(..., pattern="^(trips|families|users|engagement|costs)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None

class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    metric: str
    period: str
    data: Dict[str, Any]
    generated_at: datetime

class UsageMetrics(BaseModel):
    """Schema for usage metrics."""
    total_users: int
    active_users: int
    total_families: int
    total_trips: int
    api_calls: int
    ai_requests: int
