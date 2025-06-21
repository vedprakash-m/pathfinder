"""
Itinerary document models for Cosmos DB.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.itinerary import ActivityType, DifficultyLevel, ItineraryStatus
from pydantic import BaseModel, Field


class ItineraryActivityDocument(BaseModel):
    """Itinerary activity document model for Cosmos DB."""

    id: str
    day_id: str
    sequence_order: int
    title: str
    description: Optional[str] = None
    type: ActivityType
    difficulty: Optional[DifficultyLevel] = None

    # Location information
    location_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    google_place_id: Optional[str] = None

    # Timing
    start_time: Optional[str] = None  # Store as ISO format string
    end_time: Optional[str] = None  # Store as ISO format string
    duration_minutes: Optional[int] = None

    # Cost and booking
    estimated_cost_per_person: Optional[Decimal] = None
    booking_required: bool = False
    booking_url: Optional[str] = None
    booking_phone: Optional[str] = None

    # Additional information
    notes: Optional[str] = None
    website_url: Optional[str] = None
    image_url: Optional[str] = None
    is_optional: bool = False
    is_customized: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Document metadata
    _resource_id: Optional[str] = None
    _etag: Optional[str] = None
    _ts: Optional[int] = None


class ItineraryDayDocument(BaseModel):
    """Itinerary day document model for Cosmos DB."""

    id: str
    itinerary_id: str
    day_number: int
    date: Optional[str] = None  # Store as ISO format string
    title: Optional[str] = None
    description: Optional[str] = None

    # Daily budget and metrics
    estimated_cost: Optional[Decimal] = None
    driving_time_minutes: Optional[int] = None
    driving_distance_km: Optional[Decimal] = None

    # Activities
    activities: List[ItineraryActivityDocument] = []

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Document metadata
    _resource_id: Optional[str] = None
    _etag: Optional[str] = None
    _ts: Optional[int] = None


class ItineraryDocument(BaseModel):
    """Itinerary document model for Cosmos DB."""

    id: str
    trip_id: str  # This is the partition key
    name: str
    description: Optional[str] = None
    status: ItineraryStatus

    # AI generation metadata
    generation_prompt: Optional[str] = None
    ai_model_used: Optional[str] = None
    generation_cost: Optional[Decimal] = None
    generation_tokens: Optional[int] = None

    # Timestamps and approvals
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    # Days data (embedded documents)
    days: List[ItineraryDayDocument] = []

    # Additional metadata
    version: int = 1
    is_current: bool = True
    weather_data: Optional[Dict[str, Any]] = None
    optimization_history: Optional[List[Dict[str, Any]]] = None
    user_feedback: Optional[List[Dict[str, Any]]] = None

    # Document metadata
    _resource_id: Optional[str] = None
    _etag: Optional[str] = None
    _ts: Optional[int] = None
