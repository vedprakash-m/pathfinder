"""Notification-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    user_id: str
    type: str
    priority: str
    title: str
    message: str
    trip_id: Optional[str] = None
    family_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    data: Optional[dict] = None

class NotificationUpdate(BaseModel):
    """Schema for updating notification."""
    is_read: Optional[bool] = None

class NotificationCreate(BaseModel):
    """Schema for creating notification."""
    user_id: str
    type: str
    priority: str = "normal"
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    trip_id: Optional[str] = None
    family_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    data: Optional[dict] = None
