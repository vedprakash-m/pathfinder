from __future__ import annotations

"""Domain-level Trip service (first iteration).

In the target hexagonal architecture, all business rules live here and depend
only on domain abstractions (ports).  For now, this service delegates to the
existing `TripService` in *app.services* so that we can migrate piecemeal.

Future milestones will gradually move logic into this class and delete the old
monolith.  The methods implemented are the subset required by the existing
*trip_use_cases*.
"""

from uuid import UUID
from typing import List, Optional, Any
import json
from datetime import datetime

from app.models.trip import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TripDetail,
    TripStats,
    ParticipationCreate,
    ParticipationUpdate,
    ParticipationResponse,
    TripInvitation,
    Trip,
    TripParticipation,
    ParticipationStatus,
)


class TripDomainService:  # pragma: no cover – thin façade for now
    """Domain façade exposing trip use-cases.

    NOTE: This class should become pure business logic.  Today it simply wraps
    the existing *TripService* to avoid a flag-day rewrite.
    """

    def __init__(self, legacy_service: Any | None = None,
                 trip_repository=None,
                 trip_cosmos_repository=None,):
        self._svc = legacy_service
        self._trip_repo = trip_repository
        self._trip_cosmos_repo = trip_cosmos_repository

    # ---------------------------------------------------------------------
    # Trip lifecycle
    # ---------------------------------------------------------------------

    async def create_trip(self, trip_data: TripCreate, creator_id: str) -> TripResponse:
        # If repository not injected, fallback to legacy service
        if not self._trip_repo or not self._trip_cosmos_repo:
            return await self._svc.create_trip(trip_data, creator_id)

        # 1) Persist SQL row
        trip = await self._trip_repo.create_trip(trip_data, creator_id)
        await self._trip_repo.commit()

        # 2) Persist preferences document, if any
        if trip_data.preferences:
            await self._trip_cosmos_repo.save_preferences(
                str(trip.id), trip_data.preferences.dict()
            )

        # 3) Return DTO
        return await self._build_trip_response(trip)

    async def get_trip_by_id(self, trip_id: UUID, user_id: str) -> Optional[TripDetail]:
        if not self._trip_repo:
            return await self._svc.get_trip_by_id(trip_id, user_id)

        trip = await self._trip_repo.get_trip_by_id(trip_id)
        if not trip:
            return None

        # Access control: creator or participant
        if str(trip.creator_id) != user_id and not any(
            p.user_id and str(p.user_id) == user_id for p in (trip.participations or [])
        ):
            return None

        return await self._build_trip_detail(trip)

    async def get_user_trips(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
    ) -> List[TripResponse]:
        if not self._trip_repo:
            return await self._svc.get_user_trips(user_id, skip, limit, status_filter)

        trips = await self._trip_repo.list_user_trips(user_id, skip, limit, status_filter)
        return [await self._build_trip_response(t) for t in trips]

    async def update_trip(self, trip_id: UUID, update: TripUpdate, user_id: str) -> TripResponse:
        if not self._trip_repo:
            return await self._svc.update_trip(trip_id, update, user_id)

        trip = await self._trip_repo.get_trip_by_id(trip_id)
        if not trip:
            raise ValueError("Trip not found")

        if str(trip.creator_id) != user_id:
            raise PermissionError("Only trip creator can update trip details")

        # Apply update fields
        update_data = update.dict(exclude_unset=True)
        if "preferences" in update_data and update_data["preferences"] is not None:
            update_data["preferences"] = json.dumps(update_data["preferences"].dict())

        for field, value in update_data.items():
            if hasattr(trip, field):
                setattr(trip, field, value)

        await self._trip_repo.commit()

        # Update preferences doc if changed
        if "preferences" in update_data and self._trip_cosmos_repo:
            await self._trip_cosmos_repo.save_preferences(str(trip.id), update.preferences.dict())  # type: ignore[arg-type]

        return await self._build_trip_response(trip)

    async def delete_trip(self, trip_id: UUID, user_id: str) -> None:
        if not self._trip_repo:
            await self._svc.delete_trip(trip_id, user_id)
            return

        # Ensure trip exists
        trip = await self._trip_repo.get_trip_by_id(trip_id)
        if not trip:
            raise ValueError("Trip not found")

        # Only creator can delete
        if str(trip.creator_id) != user_id:
            raise PermissionError("Only trip creator can delete the trip")

        await self._trip_repo.delete_trip(trip)
        await self._trip_repo.commit()

    # ---------------------------------------------------------------------
    # Stats & participants
    # ---------------------------------------------------------------------

    async def get_trip_stats(self, trip_id: UUID, user_id: str) -> TripStats | None:  # noqa: D401
        if not self._trip_repo:
            return await self._svc.get_trip_stats(trip_id, user_id)

        trip = await self._trip_repo.get_trip_by_id(trip_id)
        if not trip:
            return None

        # Access check
        if str(trip.creator_id) != user_id and not any(
            p.user_id and str(p.user_id) == user_id for p in (trip.participations or [])
        ):
            return None

        participations = trip.participations or []
        total_families = len(participations)
        confirmed_families = len([p for p in participations if p.status == ParticipationStatus.CONFIRMED])
        pending_families = len([p for p in participations if p.status == ParticipationStatus.PENDING])

        total_participants = total_families  # placeholder – individual members not tracked yet

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
                budget_allocation=float(p.budget_allocation) if p.budget_allocation else None,
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
            return await self._svc.update_participation(participation_id, update, user_id)

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
            budget_allocation=float(participation.budget_allocation) if participation.budget_allocation else None,
            preferences=json.loads(participation.preferences) if participation.preferences else None,
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

    async def _build_trip_response(self, trip: 'Trip') -> TripResponse:  # type: ignore[name-defined]
        """Map SQLAlchemy Trip model → TripResponse DTO."""
        # Ensure participations are loaded
        participations = getattr(trip, 'participations', []) or []
        family_count = len(participations)
        confirmed = [p for p in participations if p.status == ParticipationStatus.CONFIRMED]

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
    def _calculate_completion_percentage(trip: 'Trip', participations) -> float:  # type: ignore[name-defined]
        if not participations:
            participations = []

        completion_factors = []
        # Basic info (25%)
        completion_factors.append(
            25.0 if all([trip.name, trip.destination, trip.start_date, trip.end_date]) else 0.0
        )

        # Participants confirmed (25%)
        total = len(participations)
        confirmed = len([p for p in participations if p.status == ParticipationStatus.CONFIRMED])
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
                    budget_allocation=float(p.budget_allocation) if p.budget_allocation else None,
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
    async def _get_participation(self, trip_id: UUID, family_id: UUID) -> Optional[TripParticipation]:
        if not self._trip_repo:
            return None
        participations = await self._trip_repo.list_trip_participations(trip_id)
        for p in participations:
            if p.family_id == family_id:
                return p
        return None

    async def update_trip_status(self, trip_id: UUID, status: str, user_id: str) -> None:
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