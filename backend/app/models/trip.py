"""
Trip model for managing group trips and coordination.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.database import GUID, Base
from pydantic import BaseModel, validator
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship


class TripStatus(str, Enum):
    """Trip status enumeration."""

    PLANNING = "planning"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipationStatus(str, Enum):
    """Family participation status."""

    INVITED = "invited"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    PENDING = "pending"


class Trip(Base):
    """Trip model for SQLAlchemy."""

    __tablename__ = "trips"

    id = Column(GUID(), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    destination = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(TripStatus), default=TripStatus.PLANNING)
    budget_total = Column(Numeric(10, 2), nullable=True)
    creator_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    preferences = Column(Text, nullable=True)  # JSON string
    itinerary_data = Column(Text, nullable=True)  # JSON string for Cosmos DB reference
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_trips")
    participations = relationship(
        "TripParticipation", back_populates="trip", cascade="all, delete-orphan"
    )
    reservations = relationship("Reservation", back_populates="trip", cascade="all, delete-orphan")
    itineraries = relationship("Itinerary", back_populates="trip", cascade="all, delete-orphan")
    notifications = relationship(
        "Notification", back_populates="trip", cascade="all, delete-orphan"
    )


class TripParticipation(Base):
    """Trip participation model for families."""

    __tablename__ = "trip_participations"

    id = Column(GUID(), primary_key=True, default=uuid4)
    trip_id = Column(GUID(), ForeignKey("trips.id"), nullable=False)
    family_id = Column(GUID(), ForeignKey("families.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ParticipationStatus), default=ParticipationStatus.INVITED)
    budget_allocation = Column(Numeric(10, 2), nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string
    notes = Column(Text, nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trip = relationship("Trip", back_populates="participations")
    family = relationship("Family", back_populates="trip_participations")
    user = relationship("User", back_populates="trip_participations")


# Pydantic models for API


class TripPreferences(BaseModel):
    """Trip preferences model."""

    accommodation_type: List[str] = []
    transportation_mode: List[str] = []
    activity_types: List[str] = []
    dining_preferences: List[str] = []
    pace: str = "moderate"  # relaxed, moderate, active
    budget_distribution: Dict[str, float] = {}
    special_requirements: List[str] = []


class TripBase(BaseModel):
    """Base trip model."""

    name: str
    description: Optional[str] = None
    destination: str
    start_date: date
    end_date: date
    budget_total: Optional[float] = None
    preferences: Optional[TripPreferences] = None
    is_public: bool = False

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class TripCreate(TripBase):
    """Trip creation model."""

    family_ids: List[str] = []


class TripUpdate(BaseModel):
    """Trip update model."""

    name: Optional[str] = None
    description: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TripStatus] = None
    budget_total: Optional[float] = None
    preferences: Optional[TripPreferences] = None
    is_public: Optional[bool] = None


class TripResponse(TripBase):
    """Trip response model."""

    id: str
    status: TripStatus
    creator_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    family_count: int = 0
    confirmed_families: int = 0

    class Config:
        from_attributes = True


class ParticipationBase(BaseModel):
    """Base participation model."""

    status: ParticipationStatus
    budget_allocation: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ParticipationCreate(ParticipationBase):
    """Participation creation model."""

    trip_id: str
    family_id: str


class ParticipationUpdate(BaseModel):
    """Participation update model."""

    status: Optional[ParticipationStatus] = None
    budget_allocation: Optional[float] = None
    preferences: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ParticipationResponse(ParticipationBase):
    """Participation response model."""

    id: str
    trip_id: str
    family_id: str
    user_id: str
    joined_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TripDetail(TripResponse):
    """Detailed trip model with participations."""

    participations: List[ParticipationResponse] = []
    has_itinerary: bool = False

    class Config:
        from_attributes = True


class TripInvitation(BaseModel):
    """Trip invitation model."""

    trip_id: str
    family_id: str
    message: Optional[str] = None
    expires_at: Optional[datetime] = None


class TripStats(BaseModel):
    """Trip statistics model."""

    total_families: int
    confirmed_families: int
    pending_families: int
    total_participants: int
    budget_allocated: float
    budget_spent: float
    days_until_trip: Optional[int] = None
    completion_percentage: float
