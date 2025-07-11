"""Poll-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PollCreate(BaseModel):
    """Schema for creating a magic poll."""

    trip_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    poll_type: str = Field(..., pattern="^(single_choice|multiple_choice|ranking)$")
    options: List[str] = Field(..., min_items=2, max_items=10)
    expires_at: Optional[datetime] = None


class PollResponse(BaseModel):
    """Schema for poll response."""

    id: str
    trip_id: str
    creator_id: str
    title: str
    description: Optional[str] = None
    poll_type: str
    options: List[str]
    responses: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None
    consensus_recommendation: Optional[Dict[str, Any]] = None
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PollVote(BaseModel):
    """Schema for poll voting."""

    selected_options: List[int] = Field(..., min_items=1)
    comment: Optional[str] = Field(None, max_length=500)


class MagicPollRequest(BaseModel):
    """Schema for AI-generated poll request."""

    trip_id: str
    context: str = Field(..., min_length=1, max_length=500)
    poll_type: str = Field(
        default="single_choice", pattern="^(single_choice|multiple_choice|ranking)$"
    )
