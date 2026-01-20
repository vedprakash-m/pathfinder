"""
API Schemas

Pydantic models for API request/response validation.
These are separate from document models to control what's exposed via API.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field

# ============================================================================
# User Schemas
# ============================================================================


class UserProfile(BaseModel):
    """User profile response schema."""

    id: str
    email: str
    name: Optional[str] = None
    role: str
    picture: Optional[str] = None
    is_active: bool = True
    onboarding_completed: bool = False
    family_ids: list[str] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_document(cls, doc: "UserDocument") -> "UserProfile":
        """Create from UserDocument."""
        return cls(
            id=doc.id,
            email=doc.email,
            name=doc.name,
            role=doc.role,
            picture=doc.picture,
            is_active=doc.is_active,
            onboarding_completed=doc.onboarding_completed,
            family_ids=doc.family_ids,
            created_at=doc.created_at,
        )


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences."""

    preferences: dict[str, Any]


# ============================================================================
# Family Schemas
# ============================================================================


class FamilyCreate(BaseModel):
    """Schema for creating a family."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class FamilyUpdate(BaseModel):
    """Schema for updating a family."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    settings: Optional[dict[str, Any]] = None


class FamilyMember(BaseModel):
    """Family member info for responses."""

    id: str
    name: Optional[str]
    email: str
    role: str


class FamilyResponse(BaseModel):
    """Family response schema."""

    id: str
    name: str
    description: Optional[str] = None
    admin_user_id: str
    member_count: int = 0
    members: list[FamilyMember] = Field(default_factory=list)
    created_at: datetime

    @classmethod
    def from_document(cls, doc: "FamilyDocument", members: Optional[list[FamilyMember]] = None) -> "FamilyResponse":
        """Create from FamilyDocument."""
        return cls(
            id=doc.id,
            name=doc.name,
            description=doc.description,
            admin_user_id=doc.admin_user_id,
            member_count=len(doc.member_ids),
            members=members or [],
            created_at=doc.created_at,
        )


class FamilyInviteRequest(BaseModel):
    """Schema for inviting a family member."""

    email: EmailStr
    role: str = Field(default="member")


# ============================================================================
# Trip Schemas
# ============================================================================


class TripCreate(BaseModel):
    """Schema for creating a trip."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    destination: Optional[str] = Field(default=None, max_length=200)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    participating_family_ids: list[str] = Field(default_factory=list)


class TripUpdate(BaseModel):
    """Schema for updating a trip."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    destination: Optional[str] = Field(default=None, max_length=200)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=3)


class TripResponse(BaseModel):
    """Trip response schema."""

    id: str
    title: str
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    budget: Optional[float] = None
    currency: str = "USD"
    organizer_user_id: str
    participating_family_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: "TripDocument") -> "TripResponse":
        """Create from TripDocument."""
        return cls(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            destination=doc.destination,
            start_date=doc.start_date,
            end_date=doc.end_date,
            status=doc.status,
            budget=doc.budget,
            currency=doc.currency,
            organizer_user_id=doc.organizer_user_id,
            participating_family_ids=doc.participating_family_ids,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


# ============================================================================
# Poll Schemas
# ============================================================================


class PollOption(BaseModel):
    """Single poll option."""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    text: str
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class PollCreate(BaseModel):
    """Schema for creating a poll."""

    trip_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    poll_type: str = Field(default="single_choice")
    options: list[PollOption]
    expires_at: Optional[datetime] = None


class PollVote(BaseModel):
    """Schema for voting on a poll."""

    option_ids: list[str] = Field(..., min_length=1)
    comment: Optional[str] = Field(default=None, max_length=500)


class PollResponse(BaseModel):
    """Poll response schema."""

    id: str
    trip_id: str
    creator_id: str
    title: str
    description: Optional[str] = None
    poll_type: str
    options: list[dict[str, Any]]
    vote_count: int = 0
    user_voted: bool = False
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    @classmethod
    def from_document(cls, doc: "PollDocument", user_id: Optional[str] = None) -> "PollResponse":
        """Create from PollDocument."""
        return cls(
            id=doc.id,
            trip_id=doc.trip_id,
            creator_id=doc.creator_id,
            title=doc.title,
            description=doc.description,
            poll_type=doc.poll_type,
            options=doc.options,
            vote_count=len(doc.votes),
            user_voted=user_id in doc.votes if user_id else False,
            status=doc.status,
            expires_at=doc.expires_at,
            created_at=doc.created_at,
        )


# ============================================================================
# Message Schemas
# ============================================================================


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    trip_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: str = Field(default="text")


class MessageResponse(BaseModel):
    """Message response schema."""

    id: str
    trip_id: str
    user_id: str
    user_name: str
    content: str
    message_type: str
    created_at: datetime

    @classmethod
    def from_document(cls, doc: "MessageDocument") -> "MessageResponse":
        """Create from MessageDocument."""
        return cls(
            id=doc.id,
            trip_id=doc.trip_id,
            user_id=doc.user_id,
            user_name=doc.user_name,
            content=doc.content,
            message_type=doc.message_type,
            created_at=doc.created_at,
        )


# ============================================================================
# Itinerary Schemas
# ============================================================================


class ItineraryDay(BaseModel):
    """Single day in an itinerary."""

    day_number: int
    date: Optional[datetime] = None
    title: str
    activities: list[dict[str, Any]] = Field(default_factory=list)
    meals: list[dict[str, Any]] = Field(default_factory=list)
    accommodation: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class ItineraryGenerateRequest(BaseModel):
    """Schema for requesting AI itinerary generation."""

    trip_id: str
    preferences: Optional[dict[str, Any]] = None
    budget_per_day: Optional[float] = None
    activity_level: str = Field(default="moderate")  # relaxed, moderate, active
    interests: list[str] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    """Itinerary response schema."""

    id: str
    trip_id: str
    version_number: int
    title: str
    summary: Optional[str] = None
    days: list[dict[str, Any]]
    status: str
    generated_by: str
    created_at: datetime

    @classmethod
    def from_document(cls, doc: "ItineraryDocument") -> "ItineraryResponse":
        """Create from ItineraryDocument."""
        return cls(
            id=doc.id,
            trip_id=doc.trip_id,
            version_number=doc.version_number,
            title=doc.title,
            summary=doc.summary,
            days=doc.days,
            status=doc.status,
            generated_by=doc.generated_by,
            created_at=doc.created_at,
        )


# ============================================================================
# AI Assistant Schemas
# ============================================================================


class AssistantMessage(BaseModel):
    """Message in assistant conversation."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class AssistantRequest(BaseModel):
    """Schema for AI assistant request."""

    message: str = Field(..., min_length=1, max_length=2000)
    trip_id: Optional[str] = None
    conversation_history: list[AssistantMessage] = Field(default_factory=list)


class AssistantResponse(BaseModel):
    """AI assistant response schema."""

    message: str
    suggestions: list[str] = Field(default_factory=list)
    tokens_used: int = 0


# ============================================================================
# Generic Schemas
# ============================================================================


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    environment: str = "production"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
