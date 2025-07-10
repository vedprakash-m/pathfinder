"""Assistant-related schemas for API requests and responses."""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ContextType(str, Enum):
    """Types of context for assistant interactions."""
    GENERAL = "general"
    TRIP = "trip"
    FAMILY = "family"
    BUDGET = "budget"
    ITINERARY = "itinerary"


class ResponseCardType(str, Enum):
    """Types of response cards."""
    MAIN = "main"
    BUDGET = "budget"
    ACTIVITY = "activity"
    SUGGESTION = "suggestion"
    ERROR = "error"


class AIResponseCard(BaseModel):
    """Schema for AI response card."""
    type: ResponseCardType
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None


class AssistantInteraction(BaseModel):
    """Schema for assistant interaction."""
    id: Optional[str] = None
    user_id: str
    message: str
    context_type: ContextType
    trip_id: Optional[str] = None
    family_id: Optional[str] = None
    response_cards: Optional[List[AIResponseCard]] = None
    response_time: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MentionRequest(BaseModel):
    """Request model for @pathfinder mentions"""
    message: str = Field(..., description="The message containing @pathfinder mention")
    context: dict[str, Any] = Field(default_factory=dict, description="Current context information")
    trip_id: Optional[str] = Field(None, description="Current trip ID if applicable")
    family_id: Optional[str] = Field(None, description="Current family ID if applicable")


class FeedbackRequest(BaseModel):
    """Request model for assistant feedback"""
    interaction_id: str = Field(..., description="ID of the assistant interaction")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    feedback_text: Optional[str] = Field(None, description="Optional feedback text")


class SuggestionsRequest(BaseModel):
    """Request model for contextual suggestions"""
    context: dict[str, Any] = Field(default_factory=dict, description="Current context information")
    page: Optional[str] = Field(None, description="Current page/route")
    trip_id: Optional[str] = Field(None, description="Current trip ID if applicable")


def create_assistant_interaction(
    user_id: str,
    message: str,
    context_type: ContextType,
    trip_id: Optional[str] = None,
    family_id: Optional[str] = None,
) -> AssistantInteraction:
    """Create a new assistant interaction."""
    return AssistantInteraction(
        user_id=user_id,
        message=message,
        context_type=context_type,
        trip_id=trip_id,
        family_id=family_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
