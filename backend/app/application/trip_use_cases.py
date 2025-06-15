"""Trip-related application use-cases.

Each use-case is a thin orchestrator that coordinates domain logic and
infrastructure concerns via injected ports (services, repositories, etc.).
"""

from __future__ import annotations

from uuid import UUID

from backend.domain.trip import TripDomainService as TripService
from app.models.trip import (
    TripCreate,
    TripResponse,
    TripDetail,
    TripStats,
    ParticipationCreate,
    ParticipationUpdate,
    ParticipationResponse,
    TripInvitation,
)


class CreateTripUseCase:
    """Create a new trip and return its representation."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(self, trip_data: TripCreate, creator_id: str) -> TripResponse:  # noqa: D401
        """Execute the use-case."""
        return await self._trip_service.create_trip(trip_data, creator_id)


class GetTripUseCase:
    """Retrieve a single trip by ID for an authorized user."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(self, trip_id: UUID, user_id: str) -> TripDetail | None:  # noqa: D401
        return await self._trip_service.get_trip_by_id(trip_id, user_id)


class ListUserTripsUseCase:
    """Return a paginated list of trips the user can access."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: str | None = None,
    ) -> list[TripResponse]:  # noqa: D401
        return await self._trip_service.get_user_trips(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
        )


class UpdateTripUseCase:
    """Modify a trip owned by the requesting creator."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(
        self, trip_id: UUID, update: "TripUpdate", user_id: str
    ) -> TripResponse:  # noqa: D401
        from app.models.trip import TripUpdate  # local import to avoid circular

        return await self._trip_service.update_trip(trip_id, update, user_id)


class DeleteTripUseCase:
    """Hard-delete a trip."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(self, trip_id: UUID, user_id: str) -> None:  # noqa: D401
        await self._trip_service.delete_trip(trip_id, user_id)


class GetTripStatsUseCase:
    """Return aggregate analytics for a single trip."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(self, trip_id: UUID, user_id: str) -> TripStats | None:  # noqa: D401
        return await self._trip_service.get_trip_stats(trip_id, user_id)


class AddParticipantUseCase:
    """Add a participant to a trip."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(
        self, trip_id: UUID, data: ParticipationCreate, user_id: str
    ) -> ParticipationResponse:  # noqa: D401
        # ensure path parameter ID overrides payload trip_id to avoid tampering
        data.trip_id = str(trip_id)
        return await self._trip_service.add_participant(data, user_id)


class GetParticipantsUseCase:
    """List all participants for a trip."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(self, trip_id: UUID, user_id: str) -> list[ParticipationResponse]:  # noqa: D401
        return await self._trip_service.get_trip_participants(trip_id, user_id)


class UpdateParticipationUseCase:
    """Update a participant record."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(
        self,
        participation_id: UUID,
        update: ParticipationUpdate,
        user_id: str,
    ) -> ParticipationResponse:  # noqa: D401
        return await self._trip_service.update_participation(participation_id, update, user_id)


class RemoveParticipantUseCase:
    """Remove a participant from a trip."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(self, participation_id: UUID, user_id: str) -> None:  # noqa: D401
        await self._trip_service.remove_participant(participation_id, user_id)


class SendInvitationUseCase:
    """Send an invitation for a family to join a trip."""

    def __init__(self, trip_service: TripService):
        self._trip_service = trip_service

    async def __call__(
        self, trip_id: UUID, data: TripInvitation, user_id: str
    ) -> None:  # noqa: D401
        data.trip_id = str(trip_id)
        await self._trip_service.send_invitation(data, user_id) 