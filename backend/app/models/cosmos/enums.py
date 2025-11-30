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


class FamilyRole(str, Enum):
    """Family member roles."""

    COORDINATOR = "coordinator"
    ADULT = "adult"
    CHILD = "child"


class InvitationStatus(str, Enum):
    """Family invitation status."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


class PollStatus(str, Enum):
    """Magic poll status enumeration."""

    ACTIVE = "active"
    CLOSED = "closed"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PollType(str, Enum):
    """Magic poll type enumeration."""

    DESTINATION_CHOICE = "destination_choice"
    ACTIVITY_PREFERENCE = "activity_preference"
    BUDGET_RANGE = "budget_range"
    DATE_SELECTION = "date_selection"
    ACCOMMODATION = "accommodation"
    DINING = "dining"
    CUSTOM = "custom"
