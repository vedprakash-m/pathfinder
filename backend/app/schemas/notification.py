"""Notification-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Notification types."""

    TRIP_INVITATION = "trip_invitation"
    TRIP_UPDATE = "trip_update"
    FAMILY_INVITATION = "family_invitation"
    CONSENSUS_VOTE = "consensus_vote"
    POLL_CREATED = "poll_created"
    SYSTEM_MESSAGE = "system_message"


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


class Notification(BaseModel):
    """Full notification model."""

    id: str
    user_id: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    trip_id: Optional[str] = None
    family_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    data: Optional[dict] = None
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BulkNotificationCreate(BaseModel):
    """Schema for creating bulk notifications."""

    user_ids: List[str]
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    trip_id: Optional[str] = None
    family_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    data: Optional[dict] = None
