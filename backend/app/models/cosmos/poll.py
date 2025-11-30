"""
Magic Polls Cosmos models for AI-powered group decision making.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .enums import PollStatus


class MagicPoll(BaseModel):
    """Magic Poll model for AI-powered decision making."""

    id: str = Field(..., description="Unique poll identifier")
    trip_id: str = Field(..., description="Associated trip ID")
    creator_id: str = Field(..., description="User who created the poll")
    title: str = Field(..., max_length=255, description="Poll title")
    description: Optional[str] = Field(None, description="Poll description")
    poll_type: str = Field(..., max_length=50, description="Type of poll")

    # Poll data stored as JSON
    options: List[Dict[str, Any]] = Field(
        default_factory=list, description="Poll options with metadata"
    )
    responses: Optional[Dict[str, Any]] = Field(None, description="User responses and preferences")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI analysis of responses")
    consensus_recommendation: Optional[Dict[str, Any]] = Field(
        None, description="AI recommendation"
    )

    # Status and timing
    status: PollStatus = Field(default=PollStatus.ACTIVE, description="Poll status")
    expires_at: Optional[datetime] = Field(None, description="Poll expiration time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def is_expired(self) -> bool:
        """Check if poll has expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert poll to dictionary format."""
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "creator_id": self.creator_id,
            "title": self.title,
            "description": self.description,
            "poll_type": self.poll_type,
            "options": self.options,
            "responses": self.responses,
            "ai_analysis": self.ai_analysis,
            "consensus_recommendation": self.consensus_recommendation,
            "status": self.status.value if isinstance(self.status, PollStatus) else self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
