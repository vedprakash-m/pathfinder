from __future__ import annotations

"""Domain-level Trip service (first iteration).

In the target hexagonal architecture, all business rules live here and depend
only on domain abstractions (ports).  For now, this service delegates to the
existing `TripService` in *app.services* so that we can migrate piecemeal.

Future milestones will gradually move logic into this class and delete the old
monolith.  The methods implemented are the subset required by the existing
*trip_use_cases*.
"""

import json
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.models.cosmos.trip import (
    TripDocument as Trip,
    TripParticipation,
)
from app.models.cosmos.enums import ParticipationStatus
from app.schemas.trip import (
    ParticipationCreate,
    ParticipationResponse,
    ParticipationUpdate,
    TripCreate,
    TripDetail,
    TripInvitation,
    TripResponse,
    TripStats,
    TripUpdate,
)


class TripDomainService:  # pragma: no cover – thin façade for now
    """Domain façade exposing trip use-cases.

    Updated to use unified Cosmos DB repository per Tech Spec requirements.
    """

    def __init__(
        self,
        unified_cosmos_repository=None,
    ):
        from app.repositories.cosmos_unified import unified_cosmos_repo

        self._cosmos_repo = unified_cosmos_repository or unified_cosmos_repo

    # ---------------------------------------------------------------------
    # Trip lifecycle
    # ---------------------------------------------------------------------

    async def create_trip(self, trip_data: TripCreate, creator_id: str) -> TripResponse:
        """Create a new trip using unified Cosmos DB storage."""
        # Create trip document in Cosmos DB
        trip_doc = await self._cosmos_repo.create_trip(trip_data, creator_id)

        # Convert to response format
        return TripResponse(
            id=trip_doc.id,
            name=trip_doc.name,
            description=trip_doc.description,
            destination=trip_doc.destination,
            start_date=trip_doc.start_date,
            end_date=trip_doc.end_date,
            budget=trip_doc.budget,
            status=trip_doc.status,
            creator_id=trip_doc.creator_id,
            created_at=trip_doc.created_at,
            updated_at=trip_doc.updated_at,
            participant_count=len(trip_doc.participants)
            if trip_doc.participants
            else 0,
            preferences=trip_doc.preferences,
        )

    async def get_trip_by_id(self, trip_id: UUID, user_id: str) -> Optional[TripDetail]:
        """Get trip by ID with access control using unified Cosmos DB."""
        trip_doc = await self._cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip_doc:
            return None

        # Access control: creator or participant
        if trip_doc.creator_id != user_id and user_id not in (
            trip_doc.participants or []
        ):
            return None

        # Convert to TripDetail format
        return TripDetail(
            id=trip_doc.id,
            name=trip_doc.name,
            description=trip_doc.description,
            destination=trip_doc.destination,
            start_date=trip_doc.start_date,
            end_date=trip_doc.end_date,
            budget=trip_doc.budget,
            status=trip_doc.status,
            creator_id=trip_doc.creator_id,
            created_at=trip_doc.created_at,
            updated_at=trip_doc.updated_at,
            participants=trip_doc.participants or [],
            preferences=trip_doc.preferences or {},
        )

    async def get_user_trips(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
    ) -> List[TripResponse]:
        """Get all trips for a user using unified Cosmos DB."""
        trip_docs = await self._cosmos_repo.get_user_trips(
            user_id, skip, limit, status_filter
        )

        return [
            TripResponse(
                id=trip.id,
                name=trip.name,
                description=trip.description,
                destination=trip.destination,
                start_date=trip.start_date,
                end_date=trip.end_date,
                budget=trip.budget,
                status=trip.status,
                creator_id=trip.creator_id,
                created_at=trip.created_at,
                updated_at=trip.updated_at,
                participant_count=len(trip.participants) if trip.participants else 0,
                preferences=trip.preferences,
            )
            for trip in trip_docs
        ]

    async def update_trip(
        self, trip_id: UUID, update: TripUpdate, user_id: str
    ) -> TripResponse:
        """Update trip using unified Cosmos DB repository."""
        trip_doc = await self._cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip_doc:
            raise ValueError("Trip not found")

        if trip_doc.creator_id != user_id:
            raise PermissionError("Only trip creator can update trip details")

        # Update the trip document
        updated_trip = await self._cosmos_repo.update_trip(str(trip_id), update)

        # Convert to response format
        return TripResponse(
            id=updated_trip.id,
            name=updated_trip.name,
            description=updated_trip.description,
            destination=updated_trip.destination,
            start_date=updated_trip.start_date,
            end_date=updated_trip.end_date,
            budget=updated_trip.budget,
            status=updated_trip.status,
            creator_id=updated_trip.creator_id,
            created_at=updated_trip.created_at,
            updated_at=updated_trip.updated_at,
            participant_count=len(updated_trip.participants)
            if updated_trip.participants
            else 0,
            preferences=updated_trip.preferences,
        )

    async def delete_trip(self, trip_id: UUID, user_id: str) -> None:
        """Delete trip using unified Cosmos DB repository."""
        # Ensure trip exists
        trip_doc = await self._cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip_doc:
            raise ValueError("Trip not found")

        # Only creator can delete
        if trip_doc.creator_id != user_id:
            raise PermissionError("Only trip creator can delete the trip")

        await self._cosmos_repo.delete_trip(str(trip_id))

    # ---------------------------------------------------------------------
    # Stats & participants
    # ---------------------------------------------------------------------

    async def get_trip_stats(
        self, trip_id: UUID, user_id: str
    ) -> TripStats | None:  # noqa: D401
        """Get trip statistics using unified Cosmos DB repository."""
        trip_doc = await self._cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip_doc:
            return None

        # Access check
        if trip_doc.creator_id != user_id and user_id not in (
            trip_doc.participants or []
        ):
            return None

        _participants = trip_doc.participants or []
        total_families = len(participations)
        confirmed_families = len(
            [p for p in participations if p.status == ParticipationStatus.CONFIRMED]
        )
        pending_families = len(
            [p for p in participations if p.status == ParticipationStatus.PENDING]
        )

        total_participants = (
            total_families  # placeholder – individual members not tracked yet
        )

        budget_allocated = sum(float(p.budget_allocation or 0) for p in participations)
        budget_spent = 0.0  # TODO: aggregate reservations once repository exists

        days_until_trip = None
        if trip.start_date:
            from datetime import date

            today = date.today()
            days_until_trip = (trip.start_date - today).days

        completion = self._calculate_completion_percentage(trip, participations)

        return TripStats(
            total_families=total_families,
            confirmed_families=confirmed_families,
            pending_families=pending_families,
            total_participants=total_participants,
            budget_allocated=budget_allocated,
            budget_spent=budget_spent,
            days_until_trip=days_until_trip,
            completion_percentage=completion,
        )

    async def add_participant(
        self, trip_id: UUID, data: ParticipationCreate, user_id: str
    ) -> ParticipationResponse:
        if not self._trip_repo:
            return await self._svc.add_participant(data, user_id)  # type: ignore[arg-type]

        # Validate trip exists
        trip = await self._trip_repo.get_trip_by_id(trip_id)
        if not trip:
            raise ValueError("Trip not found")

        # Participant cannot already exist
        existing = await self._get_participation(trip_id, UUID(data.family_id))
        if existing:
            raise ValueError("Family already participating")

        participation = TripParticipation(
            trip_id=trip_id,
            family_id=UUID(data.family_id),
            user_id=UUID(user_id),
            status=ParticipationStatus.PENDING,
            budget_allocation=data.budget_allocation,
            preferences=json.dumps(data.preferences) if data.preferences else None,
            notes=data.notes,
            joined_at=datetime.utcnow(),
        )

        await self._trip_repo.create_participation(participation)
        await self._trip_repo.commit()

        return ParticipationResponse(
            id=str(participation.id),
            trip_id=str(participation.trip_id),
            family_id=str(participation.family_id),
            user_id=str(participation.user_id),
            status=participation.status,
            budget_allocation=participation.budget_allocation,
            preferences=data.preferences,
            notes=participation.notes,
            joined_at=participation.joined_at,
            updated_at=participation.updated_at,
        )

    async def get_trip_participants(
        self, trip_id: UUID, user_id: str
    ) -> List[ParticipationResponse]:
        if not self._trip_repo:
            return await self._svc.get_trip_participants(trip_id, user_id)

        participations = await self._trip_repo.list_trip_participations(trip_id)
        return [
            ParticipationResponse(
                id=str(p.id),
                trip_id=str(p.trip_id),
                family_id=str(p.family_id),
                user_id=str(p.user_id),
                status=p.status,
                budget_allocation=float(p.budget_allocation)
                if p.budget_allocation
                else None,
                preferences=json.loads(p.preferences) if p.preferences else None,
                notes=p.notes,
                joined_at=p.joined_at,
                updated_at=p.updated_at,
            )
            for p in participations
        ]

    async def update_participation(
        self,
        participation_id: UUID,
        update: ParticipationUpdate,
        user_id: str,
    ) -> ParticipationResponse:
        if not self._trip_repo:
            return await self._svc.update_participation(
                participation_id, update, user_id
            )

        participation = await self._trip_repo.get_participation_by_id(participation_id)
        if not participation:
            raise ValueError("Participation not found")

        # Only the user who added participation or trip creator can update
        trip = participation.trip  # relationship loaded via SQLA lazy loading
        if str(participation.user_id) != user_id and str(trip.creator_id) != user_id:  # type: ignore[attr-defined]
            raise PermissionError("Not authorized to update participation")

        update_data = update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "preferences" and value is not None:
                value = json.dumps(value)
            setattr(participation, field, value)

        participation.updated_at = datetime.utcnow()
        await self._trip_repo.commit()

        return ParticipationResponse(
            id=str(participation.id),
            trip_id=str(participation.trip_id),
            family_id=str(participation.family_id),
            user_id=str(participation.user_id),
            status=participation.status,
            budget_allocation=(
                float(participation.budget_allocation)
                if participation.budget_allocation
                else None
            ),
            preferences=(
                json.loads(participation.preferences)
                if participation.preferences
                else None
            ),
            notes=participation.notes,
            joined_at=participation.joined_at,
            updated_at=participation.updated_at,
        )

    async def remove_participant(self, participation_id: UUID, user_id: str) -> None:
        if not self._trip_repo:
            await self._svc.remove_participant(participation_id, user_id)
            return

        participation = await self._trip_repo.get_participation_by_id(participation_id)
        if not participation:
            raise ValueError("Participation not found")

        trip = participation.trip
        if str(trip.creator_id) != user_id and str(participation.user_id) != user_id:
            raise PermissionError("Not authorized to remove participant")

        await self._trip_repo.delete_participation(participation)
        await self._trip_repo.commit()

    async def send_invitation(
        self, trip_id: UUID, data: TripInvitation, user_id: str
    ) -> None:
        await self._svc.send_invitation(data, user_id)

    # ---------------------------------------------------------------------
    # Helpers (temporary – to be moved to separate mapper)
    # ---------------------------------------------------------------------

    async def _build_trip_response(self, trip: "Trip") -> TripResponse:  # type: ignore[name-defined]
        """Map SQLAlchemy Trip model → TripResponse DTO."""
        # For newly created trips, avoid lazy loading participations
        # Since this is called right after trip creation, participations should be empty
        try:
            # Check if the trip is in a session that's still active
            from sqlalchemy.inspection import inspect

            state = inspect(trip)

            # If the participations haven't been loaded yet, assume empty for new trips
            if "participations" in state.unloaded:
                participations = []
            else:
                # If already loaded, use the loaded value
                participations = getattr(trip, "participations", []) or []

        except Exception:
            # Fallback to empty list for new trips to avoid any session issues
            participations = []

        family_count = len(participations)
        confirmed = [
            p
            for p in participations
            if hasattr(p, "status") and p.status == ParticipationStatus.CONFIRMED
        ]

        completion = self._calculate_completion_percentage(trip, participations)

        return TripResponse(
            id=str(trip.id),
            name=trip.name,
            description=trip.description,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            status=trip.status,
            creator_id=str(trip.creator_id),
            created_at=trip.created_at,
            updated_at=trip.updated_at,
            family_count=family_count,
            confirmed_families=len(confirmed),
            completion_percentage=completion,  # type: ignore[arg-type]
        )

    @staticmethod
    def _calculate_completion_percentage(trip: "Trip", participations) -> float:  # type: ignore[name-defined]
        if not participations:
            participations = []

        completion_factors = []
        # Basic info (25%)
        completion_factors.append(
            25.0
            if all([trip.name, trip.destination, trip.start_date, trip.end_date])
            else 0.0
        )

        # Participants confirmed (25%)
        total = len(participations)
        confirmed = len(
            [p for p in participations if p.status == ParticipationStatus.CONFIRMED]
        )
        completion_factors.append(25.0 * (confirmed / max(1, total)))

        # Budget planning (25%)
        budget_completion = 0.0
        if trip.budget_total:
            allocated = sum(float(p.budget_allocation or 0) for p in participations)
            budget_completion = min(25.0, 25.0 * (allocated / float(trip.budget_total)))
        completion_factors.append(budget_completion)

        # Itinerary (25%)
        completion_factors.append(25.0 if trip.itinerary_data else 0.0)

        return sum(completion_factors)

    # ------------------------------------------------------------------
    # Detail mapping helper
    # ------------------------------------------------------------------

    async def _build_trip_detail(self, trip: Trip) -> TripDetail:
        participations = getattr(trip, "participations", []) or []

        participation_responses: List[ParticipationResponse] = []
        for p in participations:
            participation_responses.append(
                ParticipationResponse(
                    id=str(p.id),
                    trip_id=str(p.trip_id),
                    family_id=str(p.family_id),
                    user_id=str(p.user_id),
                    status=p.status,
                    budget_allocation=float(p.budget_allocation)
                    if p.budget_allocation
                    else None,
                    preferences=json.loads(p.preferences) if p.preferences else None,
                    notes=p.notes,
                    joined_at=p.joined_at,
                    updated_at=p.updated_at,
                )
            )

        base = await self._build_trip_response(trip)
        return TripDetail(
            **base.model_dump(),  # type: ignore[arg-type]
            participations=participation_responses,
            has_itinerary=bool(trip.itinerary_data),
        )

    # Helper to fetch participation by trip and family
    async def _get_participation(
        self, trip_id: UUID, family_id: UUID
    ) -> Optional[TripParticipation]:
        if not self._trip_repo:
            return None
        participations = await self._trip_repo.list_trip_participations(trip_id)
        for p in participations:
            if p.family_id == family_id:
                return p
        return None

    async def update_trip_status(
        self, trip_id: UUID, status: str, user_id: str
    ) -> None:
        """Update the `status` field of a trip with permission checks."""

        if not self._trip_repo:
            # Fallback: use legacy svc if still present
            if self._svc is not None and hasattr(self._svc, "update_trip_status"):
                await self._svc.update_trip_status(trip_id, status, user_id)  # type: ignore[attr-defined]
            else:
                raise RuntimeError("Trip repository not configured")
            return

        trip = await self._trip_repo.get_trip_by_id(trip_id)
        if not trip:
            raise ValueError("Trip not found")

        # Only creator can change status
        if str(trip.creator_id) != user_id:
            raise PermissionError("Only trip creator can update status")

        trip.status = status  # type: ignore[assignment]
        await self._trip_repo.commit()
