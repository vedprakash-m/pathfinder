"""
Document Models

Pydantic models representing Cosmos DB documents.
All entities use a single container with a partition key based on entity type.
"""
from datetime import UTC, datetime
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class BaseDocument(BaseModel):
    """Base document for all Cosmos DB entities."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    pk: str = Field(..., description="Partition key")
    entity_type: str = Field(..., description="Document type discriminator")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    version: int = Field(default=1)

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "populate_by_name": True,
    }

    def touch(self) -> None:
        """Update the updated_at timestamp and increment version."""
        self.updated_at = utc_now()
        self.version += 1


class UserDocument(BaseDocument):
    """User document representing an authenticated user."""

    entity_type: Literal["user"] = "user"

    # Identity (Microsoft Entra ID)
    entra_id: str = Field(..., description="Microsoft Entra ID subject")
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(default=None, description="Display name")

    # Profile
    role: str = Field(default="family_admin", description="User role")
    picture: Optional[str] = Field(default=None, description="Profile picture URL")
    phone: Optional[str] = Field(default=None, description="Phone number")
    preferences: Optional[dict[str, Any]] = Field(default=None, description="User preferences")

    # Status
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Email verified status")

    # Onboarding
    onboarding_completed: bool = Field(default=False)
    onboarding_completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    family_ids: list[str] = Field(default_factory=list, description="Family memberships")


class FamilyDocument(BaseDocument):
    """Family document representing a family group."""

    entity_type: Literal["family"] = "family"

    name: str = Field(..., description="Family name")
    description: Optional[str] = Field(default=None, description="Family description")
    admin_user_id: str = Field(..., description="Admin user ID")
    member_ids: list[str] = Field(default_factory=list, description="Member user IDs")

    # Settings
    settings: Optional[dict[str, Any]] = Field(default=None, description="Family settings")

    # Metadata
    member_count: int = Field(default=1, description="Number of members")


class TripDocument(BaseDocument):
    """Trip document representing a planned trip."""

    entity_type: Literal["trip"] = "trip"

    # Basic info
    title: str = Field(..., description="Trip title")
    description: Optional[str] = Field(default=None, description="Trip description")
    destination: Optional[str] = Field(default=None, description="Trip destination")

    # Dates
    start_date: Optional[datetime] = Field(default=None, description="Trip start date")
    end_date: Optional[datetime] = Field(default=None, description="Trip end date")

    # Status and budget
    status: str = Field(default="planning", description="Trip status")
    budget: Optional[float] = Field(default=None, description="Trip budget")
    currency: str = Field(default="USD", description="Budget currency")

    # Ownership
    organizer_user_id: str = Field(..., description="Trip organizer user ID")
    participating_family_ids: list[str] = Field(default_factory=list, description="Participating family IDs")

    # Content
    itinerary: Optional[dict[str, Any]] = Field(default=None, description="Trip itinerary")
    expenses: list[dict[str, Any]] = Field(default_factory=list, description="Trip expenses")

    # Collaboration settings
    voting_deadline: Optional[datetime] = Field(default=None)
    decision_mode: str = Field(default="consensus", description="How decisions are made")


class MessageDocument(BaseDocument):
    """Chat message document."""

    entity_type: Literal["message"] = "message"

    trip_id: str = Field(..., description="Associated trip ID")
    user_id: str = Field(..., description="Sender user ID")
    user_name: str = Field(..., description="Sender display name")
    content: str = Field(..., description="Message content")
    message_type: str = Field(default="text", description="Message type")

    # Optional metadata
    metadata: Optional[dict[str, Any]] = Field(default=None)


class PollDocument(BaseDocument):
    """Poll document for collaborative decisions."""

    entity_type: Literal["poll"] = "poll"

    trip_id: str = Field(..., description="Associated trip ID")
    creator_id: str = Field(..., description="Poll creator user ID")

    # Poll content
    title: str = Field(..., description="Poll question/title")
    description: Optional[str] = Field(default=None, description="Poll description")
    poll_type: str = Field(default="single_choice", description="Poll type")

    # Options and votes
    options: list[dict[str, Any]] = Field(default_factory=list, description="Poll options")
    votes: dict[str, Any] = Field(default_factory=dict, description="User votes")

    # Status
    status: str = Field(default="active", description="Poll status")
    expires_at: Optional[datetime] = Field(default=None, description="Poll expiration")

    # Results
    result: Optional[dict[str, Any]] = Field(default=None, description="Final result")


class InvitationDocument(BaseDocument):
    """Family invitation document."""

    entity_type: Literal["invitation"] = "invitation"

    family_id: str = Field(..., description="Target family ID")
    family_name: str = Field(..., description="Family name for display")
    inviter_id: str = Field(..., description="User who sent invitation")
    inviter_name: str = Field(..., description="Inviter name for display")

    # Invitation details
    email: str = Field(..., description="Invitee email address")
    role: str = Field(default="member", description="Invited role")

    # Status
    status: str = Field(default="pending", description="Invitation status")
    expires_at: datetime = Field(..., description="Invitation expiration")

    # Token for accepting
    token: str = Field(default_factory=lambda: str(uuid4()), description="Acceptance token")


class ItineraryDocument(BaseDocument):
    """AI-generated itinerary document."""

    entity_type: Literal["itinerary"] = "itinerary"

    trip_id: str = Field(..., description="Associated trip ID")
    version_number: int = Field(default=1, description="Itinerary version")

    # Content
    title: str = Field(..., description="Itinerary title")
    summary: Optional[str] = Field(default=None, description="Brief summary")
    days: list[dict[str, Any]] = Field(default_factory=list, description="Day-by-day plans")

    # Metadata
    generated_by: str = Field(default="ai", description="Generation source")
    generation_params: Optional[dict[str, Any]] = Field(default=None, description="Parameters used for generation")

    # Status
    status: str = Field(default="draft", description="Itinerary status")
    approved_by: Optional[list[str]] = Field(default=None, description="Approving user IDs")

    # Cost tracking
    ai_tokens_used: int = Field(default=0, description="Tokens used in generation")
    ai_cost_usd: float = Field(default=0.0, description="Generation cost")
