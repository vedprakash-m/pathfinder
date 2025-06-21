"""
Notification models for the Pathfinder application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from app.core.database import GUID, Base
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


class NotificationType(str, Enum):
    """Notification types."""

    TRIP_INVITATION = "trip_invitation"
    TRIP_UPDATE = "trip_update"
    ITINERARY_READY = "itinerary_ready"
    ITINERARY_UPDATE = "itinerary_update"
    FAMILY_INVITATION = "family_invitation"
    RESERVATION_CONFIRMED = "reservation_confirmed"
    RESERVATION_CANCELLED = "reservation_cancelled"
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    CHAT_MESSAGE = "chat_message"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model."""

    __tablename__ = "notifications"

    id = Column(GUID(), primary_key=True, default=uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Reference to related entities
    trip_id = Column(GUID(), ForeignKey("trips.id"), nullable=True)
    family_id = Column(GUID(), ForeignKey("families.id"), nullable=True)

    # Status and timestamps
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Additional data as JSON string
    data = Column(Text, nullable=True)  # JSON string for additional notification data

    # Relationships
    user = relationship("User", back_populates="notifications")
    trip = relationship("Trip", back_populates="notifications")
    family = relationship("Family", back_populates="notifications")


# Pydantic models for API serialization
class NotificationBase(BaseModel):
    """Base notification model."""

    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., max_length=200)
    message: str
    trip_id: Optional[UUID] = None
    family_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    data: Optional[str] = None  # JSON string


class NotificationCreate(NotificationBase):
    """Notification creation model."""

    user_id: UUID


class NotificationUpdate(BaseModel):
    """Notification update model."""

    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationResponse(NotificationBase):
    """Notification response model."""

    id: UUID
    user_id: UUID
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""

    notifications: list[NotificationResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class NotificationStats(BaseModel):
    """Notification statistics."""

    total: int
    unread: int
    by_type: dict[str, int]
    by_priority: dict[str, int]


class BulkNotificationCreate(BaseModel):
    """Bulk notification creation model."""

    user_ids: list[UUID]
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = Field(..., max_length=200)
    message: str
    trip_id: Optional[UUID] = None
    family_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None
    data: Optional[str] = None


class NotificationFilters(BaseModel):
    """Notification filtering options."""

    type: Optional[NotificationType] = None
    priority: Optional[NotificationPriority] = None
    is_read: Optional[bool] = None
    trip_id: Optional[UUID] = None
    family_id: Optional[UUID] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class NotificationMarkRead(BaseModel):
    """Mark notifications as read."""

    notification_ids: list[UUID]


class NotificationSettings(BaseModel):
    """User notification preferences."""

    email_notifications: bool = True
    push_notifications: bool = True
    trip_invitations: bool = True
    trip_updates: bool = True
    itinerary_updates: bool = True
    family_invitations: bool = True
    reservation_updates: bool = True
    system_announcements: bool = True
    chat_messages: bool = True
