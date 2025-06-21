"""
Message document models for Cosmos DB.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MessageType(str, Enum):
    """Message types for different communication contexts."""

    CHAT = "chat"  # Regular chat message
    SYSTEM = "system"  # System notification or alert
    STATUS_UPDATE = "status"  # Trip status update
    LOCATION = "location"  # Location sharing update
    POLL = "poll"  # Group poll/vote
    RESERVATION = "reservation"  # Reservation update
    FILE = "file"  # File sharing
    ITINERARY = "itinerary"  # Itinerary update


class MessageStatus(str, Enum):
    """Message delivery and read status."""

    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class MessageDocument(BaseModel):
    """Message document model for Cosmos DB."""

    id: str
    trip_id: str  # This is the partition key
    sender_id: str
    sender_name: str
    sender_avatar: Optional[str] = None

    # Message content
    type: MessageType
    text: Optional[str] = None
    html: Optional[str] = None

    # For polls
    poll_options: Optional[List[Dict[str, Any]]] = None
    poll_responses: Optional[Dict[str, str]] = None
    poll_expires_at: Optional[datetime] = None

    # For file sharing
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # For location sharing
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None

    # Message metadata
    status: MessageStatus
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    # Reply threading
    reply_to_id: Optional[str] = None

    # Room/channel information
    room_id: Optional[str] = None
    room_name: Optional[str] = None

    # Read receipts
    read_by: Dict[str, datetime] = {}

    # Message visibility
    visible_to: Optional[List[str]] = None  # If not set, visible to all

    # Timestamps
    created_at: datetime

    # Custom data payload for specialized messages
    data: Optional[Dict[str, Any]] = None

    # Document metadata
    _resource_id: Optional[str] = None
    _etag: Optional[str] = None
    _ts: Optional[int] = None
