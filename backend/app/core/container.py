"""Dependency Injection container for backend application.

This container wires important application-layer providers so that API routers
can request instances via `Depends` without tightly coupling to concrete
implementations.

The container is kept intentionally minimal for now – as we refactor services
into use-case classes and adapters, they will be registered here, keeping FastAPI
controllers thin and testable.
"""

from __future__ import annotations

from typing import AsyncGenerator

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
from app.core.database import get_db  # Existing dependency provider
from app.core.repositories.trip_cosmos_repository import TripCosmosRepository
from app.core.repositories.trip_repository import TripRepository
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.family import FamilyDomainService
from backend.domain.messaging import MessagingDomainService
from backend.domain.reservation import ReservationDomainService
from backend.domain.trip import TripDomainService  # new domain-level facade


class Container(containers.DeclarativeContainer):
    """Global application service container."""

    wiring_config = containers.WiringConfiguration(packages=("app.api",))  # wire all API routers

    # -------------------------------
    # Infrastructure / external deps
    # -------------------------------

    db_session: providers.Callable = providers.Resource(  # type: ignore[assignment]
        get_db  # FastAPI dependency returns an `AsyncGenerator[AsyncSession]`
    )

    # -------------------------------
    # Application services & use-cases
    # -------------------------------

    # New domain-level facade wraps legacy service for gradual migration
    trip_domain_service = providers.Factory(
        TripDomainService,
        legacy_service=None,
        trip_repository=trip_repository,
        trip_cosmos_repository=trip_cosmos_repository,
    )

    # Repositories
    trip_repository = providers.Factory(TripRepository, session=db_session)
    trip_cosmos_repository = providers.Factory(TripCosmosRepository)

    # Use-cases
    create_trip_use_case = providers.Factory(CreateTripUseCase, trip_service=trip_domain_service)
    get_trip_use_case = providers.Factory(GetTripUseCase, trip_service=trip_domain_service)
    list_user_trips_use_case = providers.Factory(
        ListUserTripsUseCase, trip_service=trip_domain_service
    )
    update_trip_use_case = providers.Factory(UpdateTripUseCase, trip_service=trip_domain_service)
    delete_trip_use_case = providers.Factory(DeleteTripUseCase, trip_service=trip_domain_service)

    # Stats & participant management
    get_trip_stats_use_case = providers.Factory(
        GetTripStatsUseCase, trip_service=trip_domain_service
    )
    add_participant_use_case = providers.Factory(
        AddParticipantUseCase, trip_service=trip_domain_service
    )
    get_participants_use_case = providers.Factory(
        GetParticipantsUseCase, trip_service=trip_domain_service
    )
    update_participation_use_case = providers.Factory(
        UpdateParticipationUseCase, trip_service=trip_domain_service
    )
    remove_participant_use_case = providers.Factory(
        RemoveParticipantUseCase, trip_service=trip_domain_service
    )
    send_invitation_use_case = providers.Factory(
        SendInvitationUseCase, trip_service=trip_domain_service
    )

    # Other domain services (currently stubs – to be implemented)
    family_domain_service = providers.Factory(FamilyDomainService)
    reservation_domain_service = providers.Factory(ReservationDomainService)
    messaging_domain_service = providers.Factory(MessagingDomainService)


# Helper function for FastAPI Depends -----------------------------


async def get_container() -> AsyncGenerator[Container, None]:  # pragma: no cover
    """Yield a singleton DI container instance for the request lifespan."""

    container = Container()  # Could be cached in a real app
    try:
        yield container
    finally:
        await container.shutdown_resources()
