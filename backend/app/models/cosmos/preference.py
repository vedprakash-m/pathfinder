"""
Preference document models for Cosmos DB.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class PreferenceType(str, Enum):
    """Preference types for different entities."""

    USER = "user"
    FAMILY = "family"
    TRIP = "trip"


class PreferenceDocument(BaseModel):
    """Preference document model for Cosmos DB."""

    id: str
    entity_type: PreferenceType
    entity_id: str  # This is the partition key - user_id, family_id or trip_id

    # Core preferences
    preferences: Dict[str, Any]

    # User preferences specifics
    dietary_restrictions: Optional[List[str]] = None
    accessibility_needs: Optional[List[str]] = None
    preferred_activities: Optional[List[str]] = None
    budget_preferences: Optional[Dict[str, Any]] = None

    # Trip preferences specifics
    accommodation_preferences: Optional[Dict[str, Any]] = None
    transportation_preferences: Optional[Dict[str, Any]] = None
    activity_preferences: Optional[Dict[str, Any]] = None

    # AI-generated preference insights
    preference_insights: Optional[Dict[str, Any]] = None

    # Contextual preferences (settings that change based on context)
    contextual_preferences: Optional[Dict[str, Dict[str, Any]]] = None

    # App settings and UI preferences
    app_settings: Optional[Dict[str, Any]] = None
    ui_preferences: Optional[Dict[str, Any]] = None

    # Notification preferences
    notification_settings: Optional[Dict[str, bool]] = None

    # Version tracking
    version: int = 1
    previous_version_id: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    # Document metadata
    _resource_id: Optional[str] = None
    _etag: Optional[str] = None
    _ts: Optional[int] = None
