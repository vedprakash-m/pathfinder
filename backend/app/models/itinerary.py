"""
Itinerary models for the Pathfinder application.
"""

from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from app.core.database import GUID, Base
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


class ItineraryStatus(str, Enum):
    """Itinerary status types."""

    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    APPROVED = "approved"
    MODIFIED = "modified"
    ARCHIVED = "archived"


class ActivityType(str, Enum):
    """Activity types."""

    ACCOMMODATION = "accommodation"
    DINING = "dining"
    ATTRACTION = "attraction"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    OUTDOOR = "outdoor"
    CULTURAL = "cultural"
    ADVENTURE = "adventure"
    RELAXATION = "relaxation"
    TRANSPORTATION = "transportation"
    CUSTOM = "custom"


class DifficultyLevel(str, Enum):
    """Activity difficulty levels."""

    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


class Itinerary(Base):
    """Itinerary model."""

    __tablename__ = "itineraries"

    id = Column(GUID(), primary_key=True, default=uuid4)
    trip_id = Column(GUID(), ForeignKey("trips.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ItineraryStatus), default=ItineraryStatus.DRAFT)

    # AI generation metadata
    generation_prompt = Column(Text, nullable=True)
    ai_model_used = Column(String(100), nullable=True)
    generation_cost = Column(Numeric(10, 4), nullable=True)
    generation_tokens = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="itineraries")
    approver = relationship("User", foreign_keys=[approved_by])
    days = relationship(
        "ItineraryDay", back_populates="itinerary", cascade="all, delete-orphan"
    )


class ItineraryDay(Base):
    """Itinerary day model."""

    __tablename__ = "itinerary_days"

    id = Column(GUID(), primary_key=True, default=uuid4)
    itinerary_id = Column(GUID(), ForeignKey("itineraries.id"), nullable=False)
    day_number = Column(Integer, nullable=False)  # 1-based day number
    date = Column(DateTime, nullable=True)  # Actual date when scheduled
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # Daily budget and metrics
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    driving_time_minutes = Column(Integer, nullable=True)
    driving_distance_km = Column(Numeric(8, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    itinerary = relationship("Itinerary", back_populates="days")
    activities = relationship(
        "ItineraryActivity", back_populates="day", cascade="all, delete-orphan"
    )


class ItineraryActivity(Base):
    """Itinerary activity model."""

    __tablename__ = "itinerary_activities"

    id = Column(GUID(), primary_key=True, default=uuid4)
    day_id = Column(GUID(), ForeignKey("itinerary_days.id"), nullable=False)
    sequence_order = Column(Integer, nullable=False)  # Order within the day

    # Activity details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(ActivityType), nullable=False)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=True)

    # Location information
    location_name = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    google_place_id = Column(String(100), nullable=True)

    # Timing
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # Cost and booking
    estimated_cost_per_person = Column(Numeric(10, 2), nullable=True)
    booking_required = Column(Boolean, default=False)
    booking_url = Column(Text, nullable=True)
    booking_phone = Column(String(20), nullable=True)

    # Additional information
    notes = Column(Text, nullable=True)
    website_url = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    is_optional = Column(Boolean, default=False)
    # User modified from AI suggestion
    is_customized = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    day = relationship("ItineraryDay", back_populates="activities")


# Pydantic models for API serialization
class ItineraryActivityBase(BaseModel):
    """Base itinerary activity model."""

    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    type: ActivityType
    difficulty: Optional[DifficultyLevel] = None
    location_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    google_place_id: Optional[str] = Field(None, max_length=100)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    estimated_cost_per_person: Optional[Decimal] = None
    booking_required: bool = False
    booking_url: Optional[str] = None
    booking_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    is_optional: bool = False


class ItineraryActivityCreate(ItineraryActivityBase):
    """Itinerary activity creation model."""

    sequence_order: int


class ItineraryActivityUpdate(BaseModel):
    """Itinerary activity update model."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    type: Optional[ActivityType] = None
    difficulty: Optional[DifficultyLevel] = None
    location_name: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    google_place_id: Optional[str] = Field(None, max_length=100)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    estimated_cost_per_person: Optional[Decimal] = None
    booking_required: Optional[bool] = None
    booking_url: Optional[str] = None
    booking_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    is_optional: Optional[bool] = None
    sequence_order: Optional[int] = None


class ItineraryActivityResponse(ItineraryActivityBase):
    """Itinerary activity response model."""

    id: UUID
    day_id: UUID
    sequence_order: int
    is_customized: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItineraryDayBase(BaseModel):
    """Base itinerary day model."""

    day_number: int
    date: Optional[datetime] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    driving_time_minutes: Optional[int] = None
    driving_distance_km: Optional[Decimal] = None


class ItineraryDayCreate(ItineraryDayBase):
    """Itinerary day creation model."""

    activities: list[ItineraryActivityCreate] = []


class ItineraryDayUpdate(BaseModel):
    """Itinerary day update model."""

    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    driving_time_minutes: Optional[int] = None
    driving_distance_km: Optional[Decimal] = None


class ItineraryDayResponse(ItineraryDayBase):
    """Itinerary day response model."""

    id: UUID
    itinerary_id: UUID
    activities: list[ItineraryActivityResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItineraryBase(BaseModel):
    """Base itinerary model."""

    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    status: ItineraryStatus = ItineraryStatus.DRAFT


class ItineraryCreate(ItineraryBase):
    """Itinerary creation model."""

    trip_id: UUID
    days: list[ItineraryDayCreate] = []


class ItineraryUpdate(BaseModel):
    """Itinerary update model."""

    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[ItineraryStatus] = None


class ItineraryResponse(ItineraryBase):
    """Itinerary response model."""

    id: UUID
    trip_id: UUID
    generation_prompt: Optional[str] = None
    ai_model_used: Optional[str] = None
    generation_cost: Optional[Decimal] = None
    generation_tokens: Optional[int] = None
    days: list[ItineraryDayResponse] = []
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class ItineraryGenerationRequest(BaseModel):
    """AI itinerary generation request."""

    trip_id: UUID
    preferences: dict = {}  # User preferences for the itinerary
    force_regenerate: bool = False  # Force regeneration even if one exists


class ItineraryOptimizationRequest(BaseModel):
    """Itinerary optimization request."""

    itinerary_id: UUID
    optimization_type: str = "time"  # "time", "cost", "distance"
    constraints: dict = {}  # Optimization constraints


class ItinerarySummary(BaseModel):
    """Itinerary summary statistics."""

    total_days: int
    total_activities: int
    total_estimated_cost: Decimal
    total_driving_time_minutes: int
    total_driving_distance_km: Decimal
    activities_by_type: dict[str, int]
    average_activities_per_day: float
