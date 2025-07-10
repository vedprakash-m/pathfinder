"""
Cosmos DB model definitions.
These models are used for all database operations in the unified architecture.
"""

from app.models.cosmos.enums import ActivityType, DifficultyLevel, ItineraryStatus

__all__ = [
    "ActivityType",
    "DifficultyLevel", 
    "ItineraryStatus",
]
