from __future__ import annotations

"""Cosmos-DB repository for Trip-related document storage.

This adapter provides a thin, awaitable façade around *TripCosmosOperations*
so that the infrastructure dependency is hidden behind a repository interface.
"""

from typing import Any, Dict, List, Optional

from app.services.trip_cosmos import TripCosmosOperations


class TripCosmosRepository:  # pragma: no cover – infra wrapper
    """Adapter that speaks the *document store* dialect for trips.

    Eventually, this will be replaced by a proper *Port* interface with unit
    tests.  For now it simply delegates to the already-existing operations
    helper so upper layers can be refactored incrementally without touching the
    persistence details.
    """

    def __init__(self, ops: TripCosmosOperations | None = None) -> None:
        self._ops = ops or TripCosmosOperations()

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    async def save_preferences(self, trip_id: str, preferences: Dict[str, Any]) -> None:
        """Persist structured user preferences for a trip."""
        await self._ops.save_trip_preferences_to_cosmos(trip_id, preferences)

    async def get_preferences(self, trip_id: str) -> Optional[Dict[str, Any]]:
        return await self._ops.get_trip_preferences_from_cosmos(trip_id)

    # ------------------------------------------------------------------
    # Itineraries
    # ------------------------------------------------------------------

    async def save_itinerary(self, trip_id: str, itinerary: Dict[str, Any]) -> bool:
        return await self._ops.itinerary_service.save_itinerary(trip_id, itinerary)  # type: ignore[arg-type]

    async def get_latest_itinerary(self, trip_id: str) -> Optional[Dict[str, Any]]:
        return await self._ops.itinerary_service.get_latest_itinerary(trip_id)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def save_message(self, trip_id: str, message: Dict[str, Any]) -> None:
        await self._ops.message_service.save_message(trip_id, message)  # type: ignore[arg-type]

    async def get_messages(self, trip_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return await self._ops.message_service.get_messages(trip_id, limit) 