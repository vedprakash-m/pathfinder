"""TripRepository – infrastructure data access for Trip aggregate.

Initially wraps selected SQLAlchemy queries copied from TripService so that we
can later plug it into the application layer and retire TripService.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.core.logging_config import get_logger
from app.models.trip import (
    ParticipationCreate,
    ParticipationResponse,
    ParticipationStatus,
    ParticipationUpdate,
    Trip,
    TripCreate,
    TripDetail,
    TripInvitation,
    TripParticipation,
    TripResponse,
    TripStats,
    TripStatus,
    TripUpdate,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = get_logger(__name__)


class TripRepository:
    """SQL-backed repository for Trip and related aggregates."""

    def __init__(self, session: AsyncSession):
        self._db = session

    # ---------------------------------------------------------------------
    # CRUD operations on Trip
    # ---------------------------------------------------------------------

    async def create_trip(self, trip_data: TripCreate, creator_id: str) -> Trip:
        """Persist new Trip entity and return SQLAlchemy model instance."""
        trip_dict = trip_data.dict(exclude={"family_ids"})
        if trip_data.preferences:
            trip_dict["preferences"] = json.dumps(trip_data.preferences.dict())
        else:
            trip_dict["preferences"] = None

        trip = Trip(
            **trip_dict,
            creator_id=UUID(creator_id),
            status=TripStatus.PLANNING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(trip)
        await self._db.flush()
        return trip

    async def get_trip_by_id(self, trip_id: UUID) -> Optional[Trip]:
        query = (
            select(Trip)
            .options(
                selectinload(Trip.participations).selectinload(TripParticipation.family),
                selectinload(Trip.participations).selectinload(TripParticipation.user),
                selectinload(Trip.creator),
            )
            .where(Trip.id == trip_id)
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def update_trip(self, trip: Trip) -> None:  # trip is already mutated
        trip.updated_at = datetime.utcnow()
        self._db.add(trip)
        await self._db.flush()

    async def delete_trip(self, trip: Trip) -> None:
        await self._db.delete(trip)

    # ---------------------------------------------------------------------
    # Participations
    # ---------------------------------------------------------------------

    async def create_participation(self, participation: TripParticipation) -> None:
        self._db.add(participation)
        await self._db.flush()

    async def list_trip_participations(self, trip_id: UUID) -> List[TripParticipation]:
        stmt = select(TripParticipation).where(TripParticipation.trip_id == trip_id)
        res = await self._db.execute(stmt)
        return res.scalars().all()

    async def get_participation_by_id(self, participation_id: UUID) -> Optional[TripParticipation]:
        stmt = select(TripParticipation).where(TripParticipation.id == participation_id)
        res = await self._db.execute(stmt)
        return res.scalar_one_or_none()

    async def delete_participation(self, participation: TripParticipation) -> None:
        await self._db.delete(participation)

    # ---------------------------------------------------------------------
    # Commit helpers
    # ---------------------------------------------------------------------

    async def commit(self):
        await self._db.commit()

    async def rollback(self):
        await self._db.rollback()

    # ---------------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------------

    async def list_user_trips(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: str | None = None,
    ) -> List[Trip]:
        """Return trips where the user is creator or participant."""

        stmt = (
            select(Trip)
            .options(selectinload(Trip.participations))
            .where(
                (Trip.creator_id == UUID(user_id))
                | (Trip.participations.any(TripParticipation.user_id == UUID(user_id)))
            )
            .offset(skip)
            .limit(limit)
        )

        if status_filter:
            stmt = stmt.where(Trip.status == status_filter)

        res = await self._db.execute(stmt)
        return res.scalars().all()
