"""Dependency Injection container using kink for backend application.

This container provides simple dependency injection using kink library,
replacing the previous dependency-injector setup which had Python 3.12 compatibility issues.

The container wires important application-layer providers so that API routers
can request instances via `Depends` without tightly coupling to concrete
implementations.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import kink

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
from app.core.database import get_db, SessionLocal
from app.core.repositories.trip_cosmos_repository import TripCosmosRepository
from app.core.repositories.trip_repository import TripRepository

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from domain.family import FamilyDomainService
from domain.messaging import MessagingDomainService
from domain.reservation import ReservationDomainService
from domain.trip import TripDomainService


class KinkContainer:
    """Global application service container using kink."""

    def __init__(self):
        """Initialize the container and bind services."""
        self._configured = False
        self.configure()

    def configure(self):
        """Configure all service bindings."""
        if self._configured:
            return
        
        # Clear existing bindings to avoid conflicts
        kink.clear()
        
        # -------------------------------
        # Infrastructure / external deps  
        # -------------------------------
        
        # Database session factory - returns async session
        kink.bind(
            "db_session_factory",
            lambda: SessionLocal()
        )
        
        # -------------------------------
        # Repositories (using proper session management)
        # -------------------------------
        
        def create_trip_repository():
            """Create a TripRepository with a new session."""
            session = SessionLocal()
            return TripRepository(session=session)
        
        kink.bind(
            TripRepository,
            create_trip_repository
        )
        
        kink.bind(
            TripCosmosRepository,
            lambda: TripCosmosRepository()
        )
        
        # -------------------------------
        # Domain Services
        # -------------------------------
        
        kink.bind(
            TripDomainService,
            lambda: TripDomainService(
                legacy_service=None,
                trip_repository=kink.get(TripRepository),
                trip_cosmos_repository=kink.get(TripCosmosRepository),
            )
        )
        
        kink.bind(
            FamilyDomainService,
            lambda: FamilyDomainService()
        )
        
        kink.bind(
            ReservationDomainService, 
            lambda: ReservationDomainService()
        )
        
        kink.bind(
            MessagingDomainService,
            lambda: MessagingDomainService()
        )
        
        # -------------------------------
        # Use-cases
        # -------------------------------
        
        kink.bind(
            CreateTripUseCase,
            lambda: CreateTripUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            GetTripUseCase,
            lambda: GetTripUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            ListUserTripsUseCase,
            lambda: ListUserTripsUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            UpdateTripUseCase,
            lambda: UpdateTripUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            DeleteTripUseCase,
            lambda: DeleteTripUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            GetTripStatsUseCase,
            lambda: GetTripStatsUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            AddParticipantUseCase,
            lambda: AddParticipantUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            GetParticipantsUseCase,
            lambda: GetParticipantsUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            UpdateParticipationUseCase,
            lambda: UpdateParticipationUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            RemoveParticipantUseCase,
            lambda: RemoveParticipantUseCase(trip_service=kink.get(TripDomainService))
        )
        
        kink.bind(
            SendInvitationUseCase,
            lambda: SendInvitationUseCase(trip_service=kink.get(TripDomainService))
        )
        
        self._configured = True

    async def shutdown_resources(self):
        """Cleanup resources when shutting down."""
        # Kink doesn't need explicit cleanup, but we can clear bindings
        pass


# Global container instance
_container = None


def get_container() -> KinkContainer:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = KinkContainer()
    return _container


# Helper functions for FastAPI Depends -----------------------------

async def get_kink_container() -> AsyncGenerator[KinkContainer, None]:
    """Yield the DI container instance for the request lifespan."""
    container = get_container()
    try:
        yield container
    finally:
        await container.shutdown_resources()


# Dependency injection helpers using kink directly
def get_trip_repository() -> TripRepository:
    """Get TripRepository instance via kink."""
    return kink.get(TripRepository)


def get_trip_cosmos_repository() -> TripCosmosRepository:
    """Get TripCosmosRepository instance via kink."""
    return kink.get(TripCosmosRepository)


def get_trip_domain_service() -> TripDomainService:
    """Get TripDomainService instance via kink."""
    return kink.get(TripDomainService)


def get_create_trip_use_case() -> CreateTripUseCase:
    """Get CreateTripUseCase instance via kink."""
    return kink.get(CreateTripUseCase)


def get_get_trip_use_case() -> GetTripUseCase:
    """Get GetTripUseCase instance via kink."""
    return kink.get(GetTripUseCase)


def get_list_user_trips_use_case() -> ListUserTripsUseCase:
    """Get ListUserTripsUseCase instance via kink."""
    return kink.get(ListUserTripsUseCase)


def get_update_trip_use_case() -> UpdateTripUseCase:
    """Get UpdateTripUseCase instance via kink."""
    return kink.get(UpdateTripUseCase)


def get_delete_trip_use_case() -> DeleteTripUseCase:
    """Get DeleteTripUseCase instance via kink."""
    return kink.get(DeleteTripUseCase)


def get_get_trip_stats_use_case() -> GetTripStatsUseCase:
    """Get GetTripStatsUseCase instance via kink."""
    return kink.get(GetTripStatsUseCase)


def get_add_participant_use_case() -> AddParticipantUseCase:
    """Get AddParticipantUseCase instance via kink."""
    return kink.get(AddParticipantUseCase)


def get_get_participants_use_case() -> GetParticipantsUseCase:
    """Get GetParticipantsUseCase instance via kink."""
    return kink.get(GetParticipantsUseCase)


def get_update_participation_use_case() -> UpdateParticipationUseCase:
    """Get UpdateParticipationUseCase instance via kink."""
    return kink.get(UpdateParticipationUseCase)


def get_remove_participant_use_case() -> RemoveParticipantUseCase:
    """Get RemoveParticipantUseCase instance via kink."""
    return kink.get(RemoveParticipantUseCase)


def get_send_invitation_use_case() -> SendInvitationUseCase:
    """Get SendInvitationUseCase instance via kink."""
    return kink.get(SendInvitationUseCase)
