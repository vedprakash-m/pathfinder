from __future__ import annotations

"""Simple dependency injection providers for FastAPI - Unified Cosmos DB Implementation.

This module provides dependency injection functions that work directly with FastAPI's
dependency system, using our unified Cosmos DB approach per Tech Spec.
"""

import os
import sys

from app.application.trip_use_cases import (
    AddParticipantUseCase,
    CreateTripUseCase,
    DeleteTripUseCase,
    GetParticipantsUseCase,
    GetTripStatsUseCase,
    GetTripUseCase,
    ListUserTripsUseCase,
    RemoveParticipantUseCase,
    SendInvitationUseCase,
    UpdateParticipationUseCase,
    UpdateTripUseCase,
)
from app.core.database_unified import get_cosmos_service
from app.core.repositories.trip_cosmos_repository import TripCosmosRepository
from app.core.repositories.trip_repository import TripRepository
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from domain.trip import TripDomainService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from domain.family import FamilyDomainService
from domain.messaging import MessagingDomainService
from domain.reservation import ReservationDomainService


# Repository providers
async def get_trip_repository(db: AsyncSession = None) -> TripRepository:
    """Get TripRepository instance."""
    if db is None:
        # Create a new session if none provided
        async with SessionLocal() as session:
            return TripRepository(session=session)
    return TripRepository(session=db)


def get_trip_cosmos_repository() -> TripCosmosRepository:
    """Get TripCosmosRepository instance."""
    return TripCosmosRepository()


# Domain service providers
async def get_trip_domain_service(
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_service),
) -> TripDomainService:
    """Get TripDomainService instance with unified Cosmos DB repository."""
    return TripDomainService(
        unified_cosmos_repository=cosmos_repo,
    )


def get_family_domain_service() -> FamilyDomainService:
    """Get FamilyDomainService instance."""
    return FamilyDomainService()


def get_reservation_domain_service() -> ReservationDomainService:
    """Get ReservationDomainService instance."""
    return ReservationDomainService()


def get_messaging_domain_service() -> MessagingDomainService:
    """Get MessagingDomainService instance."""
    return MessagingDomainService()


# Use case providers
async def get_create_trip_use_case() -> CreateTripUseCase:
    """Get CreateTripUseCase instance."""
    trip_service = await get_trip_domain_service()
    return CreateTripUseCase(trip_service=trip_service)


async def get_get_trip_use_case() -> GetTripUseCase:
    """Get GetTripUseCase instance."""
    trip_service = await get_trip_domain_service()
    return GetTripUseCase(trip_service=trip_service)


async def get_list_user_trips_use_case() -> ListUserTripsUseCase:
    """Get ListUserTripsUseCase instance."""
    trip_service = await get_trip_domain_service()
    return ListUserTripsUseCase(trip_service=trip_service)


async def get_update_trip_use_case() -> UpdateTripUseCase:
    """Get UpdateTripUseCase instance."""
    trip_service = await get_trip_domain_service()
    return UpdateTripUseCase(trip_service=trip_service)


async def get_delete_trip_use_case() -> DeleteTripUseCase:
    """Get DeleteTripUseCase instance."""
    trip_service = await get_trip_domain_service()
    return DeleteTripUseCase(trip_service=trip_service)


async def get_get_trip_stats_use_case() -> GetTripStatsUseCase:
    """Get GetTripStatsUseCase instance."""
    trip_service = await get_trip_domain_service()
    return GetTripStatsUseCase(trip_service=trip_service)


async def get_add_participant_use_case() -> AddParticipantUseCase:
    """Get AddParticipantUseCase instance."""
    trip_service = await get_trip_domain_service()
    return AddParticipantUseCase(trip_service=trip_service)


async def get_get_participants_use_case() -> GetParticipantsUseCase:
    """Get GetParticipantsUseCase instance."""
    trip_service = await get_trip_domain_service()
    return GetParticipantsUseCase(trip_service=trip_service)


async def get_update_participation_use_case() -> UpdateParticipationUseCase:
    """Get UpdateParticipationUseCase instance."""
    trip_service = await get_trip_domain_service()
    return UpdateParticipationUseCase(trip_service=trip_service)


async def get_remove_participant_use_case() -> RemoveParticipantUseCase:
    """Get RemoveParticipantUseCase instance."""
    trip_service = await get_trip_domain_service()
    return RemoveParticipantUseCase(trip_service=trip_service)


async def get_send_invitation_use_case() -> SendInvitationUseCase:
    """Get SendInvitationUseCase instance."""
    trip_service = await get_trip_domain_service()
    return SendInvitationUseCase(trip_service=trip_service)
