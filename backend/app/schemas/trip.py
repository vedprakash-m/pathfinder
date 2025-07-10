"""Trip-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TripCreate(BaseModel):
    """Schema for creating a new trip."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    destination: Optional[str] = Field(None, max_length=200)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)

class TripResponse(BaseModel):
    """Schema for trip response."""
    id: str
    title: str
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    budget: Optional[float] = None
    organizer_user_id: str
    participating_family_ids: List[str]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_document(cls, doc):
        """Create response from TripDocument."""
        return cls(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            destination=doc.destination,
            start_date=doc.start_date,
            end_date=doc.end_date,
            status=doc.status,
            budget=doc.budget,
            organizer_user_id=doc.organizer_user_id,
            participating_family_ids=doc.participating_family_ids,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )

class TripUpdate(BaseModel):
    """Schema for updating trip information."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    destination: Optional[str] = Field(None, max_length=200)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)

class TripStats(BaseModel):
    """Schema for trip statistics."""
    total_trips: int
    active_trips: int
    completed_trips: int
    total_families: int
    average_budget: Optional[float] = None

class TripInvitation(BaseModel):
    """Schema for trip invitation."""
    family_id: str
    message: Optional[str] = Field(None, max_length=500)

class ParticipationCreate(BaseModel):
    """Schema for creating trip participation."""
    family_id: str
    status: str = "invited"

class ParticipationResponse(BaseModel):
    """Schema for participation response."""
    id: str
    trip_id: str
    family_id: str
    status: str
    joined_at: Optional[datetime] = None

class ParticipationUpdate(BaseModel):
    """Schema for updating participation."""
    status: str

class TripDetail(BaseModel):
    """Schema for detailed trip information."""
    trip: TripResponse
    participating_families: List[dict]
    stats: TripStats
