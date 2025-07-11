"""
Trip Cosmos DB models - Unified architecture implementation.
This replaces the old SQL Trip models with Cosmos DB documents.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.cosmos.enums import TripStatus, ParticipationStatus


class TripDocument(BaseModel):
    """Trip document for Cosmos DB storage."""

    id: str = Field(..., description="Unique trip identifier")
    title: str = Field(..., description="Trip title")
    description: Optional[str] = Field(None, description="Trip description")
    destination: Optional[str] = Field(None, description="Trip destination")
    start_date: Optional[datetime] = Field(None, description="Trip start date")
    end_date: Optional[datetime] = Field(None, description="Trip end date")
    status: TripStatus = Field(TripStatus.DRAFT, description="Trip status")
    budget: Optional[float] = Field(None, description="Trip budget")
    organizer_user_id: str = Field(..., description="User ID of trip organizer")
    participating_family_ids: List[str] = Field(
        default_factory=list, description="List of participating family IDs"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TripParticipation(BaseModel):
    """Trip participation model."""

    id: str = Field(..., description="Participation ID")
    trip_id: str = Field(..., description="Trip ID")
    user_id: str = Field(..., description="User ID")
    status: ParticipationStatus = Field(
        ParticipationStatus.INVITED, description="Participation status"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


# Aliases for backward compatibility
Trip = TripDocument
TripCreate = TripDocument
