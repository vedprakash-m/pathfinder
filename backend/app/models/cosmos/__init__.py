"""
Cosmos DB document models package initialization.
"""

from app.models.cosmos.itinerary import (
    ItineraryActivityDocument,
    ItineraryDayDocument,
    ItineraryDocument,
)
from app.models.cosmos.message import MessageDocument, MessageStatus, MessageType
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
