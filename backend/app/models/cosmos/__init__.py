"""
Cosmos DB document models package initialization.
"""

from app.models.cosmos.itinerary import (
    ItineraryDocument,
    ItineraryDayDocument,
    ItineraryActivityDocument,
)
from app.models.cosmos.message import MessageDocument, MessageType, MessageStatus
from app.models.cosmos.preference import PreferenceDocument, PreferenceType

__all__ = [
    "ItineraryDocument",
    "ItineraryDayDocument",
    "ItineraryActivityDocument",
    "MessageDocument",
    "MessageType",
    "MessageStatus",
    "PreferenceDocument",
    "PreferenceType",
]
