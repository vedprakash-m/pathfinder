"""
Enum definitions for Cosmos models.
These replace the enums that were in the removed SQL models.
"""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class TripStatus(str, Enum):
    """Trip status enumeration."""

    DRAFT = "draft"
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ActivityType(str, Enum):
    """Activity type enumeration."""

    ACCOMMODATION = "accommodation"
    TRANSPORTATION = "transportation"
    DINING = "dining"
    ATTRACTION = "attraction"
    ACTIVITY = "activity"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class DifficultyLevel(str, Enum):
    """Activity difficulty level."""

    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


class ItineraryStatus(str, Enum):
    """Itinerary status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipationStatus(str, Enum):
    """Participation status enumeration."""

    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    PENDING = "pending"
