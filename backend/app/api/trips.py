"""
Trip management API endpoints.
"""

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

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
from app.core.container import Container

# from app.core.database import get_db
# from app.core.security import get_current_active_user  # No longer needed
from app.core.zero_trust import require_permissions
from app.models.trip import (
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
from app.models.user import User

# from app.services.trip_service import TripService  # TODO: will be removed after repository migration
from app.services.trip_cosmos import TripCosmosOperations
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status

# from sqlalchemy.ext.asyncio import AsyncSession



router = APIRouter()


@router.post("/", response_model=TripResponse)
@inject
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(require_permissions("trips", "create")),
    use_case: CreateTripUseCase = Depends(Provide[Container.create_trip_use_case]),
):
    """Create a new trip (application layer)."""

    try:
        return await use_case(trip_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# --------------------------------------------------------------
# 🆕  Sample Trip Endpoint for Golden-Path Onboarding
# --------------------------------------------------------------


from datetime import date, timedelta  # NEW import (keep grouped at top if sorted)


@router.post("/sample", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_sample_trip(
    template: str = Query(
        "weekend_getaway",
        regex="^(weekend_getaway|family_vacation|adventure_trip)$",
        description="Sample trip template to use",
    ),
    current_user: User = Depends(require_permissions("trips", "create")),
    use_case: CreateTripUseCase = Depends(Provide[Container.create_trip_use_case]),
):
    """Create a pre-populated *sample* trip used by the Golden Path onboarding flow.

    The trip is **private** (`is_public=False`) and linked to the creator’s family only.
    """

    # Enhanced template data with realistic details and decision scenarios
    template_map = {
        "weekend_getaway": {
            "name": "Napa Valley Family Weekend",
            "description": "A relaxing weekend exploring California wine country with family-friendly activities, scenic hot air balloon rides, and farm-to-table dining experiences.",
            "destination": "Napa Valley, California",
            "duration": 3,
            "budget": 1200.0,
            "activities": [
                "Family-friendly wineries with kids' activities",
                "Hot air balloon ride over vineyards",
                "Oxbow Public Market food tour",
                "Castello di Amorosa castle tour",
            ],
            "decision_scenarios": [
                {
                    "title": "Balloon Ride Timing",
                    "options": ["Early morning (6 AM)", "Late afternoon (4 PM)"],
                    "context": "Weather is best in morning, but kids prefer afternoon",
                },
                {
                    "title": "Dining Choice",
                    "options": [
                        "Fancy restaurant ($80/person)",
                        "Casual family place ($35/person)",
                    ],
                    "context": "Budget vs experience decision",
                },
            ],
        },
        "family_vacation": {
            "name": "Yellowstone National Park Adventure",
            "description": "A week-long exploration of America's first national park with wildlife viewing, geothermal wonders, and Junior Ranger programs for kids.",
            "destination": "Yellowstone National Park, Wyoming",
            "duration": 7,
            "budget": 3200.0,
            "activities": [
                "Old Faithful geyser viewing",
                "Wildlife safari in Lamar Valley",
                "Junior Ranger program participation",
                "Grand Prismatic Spring boardwalk",
                "Yellowstone Lake boat tour",
            ],
            "decision_scenarios": [
                {
                    "title": "Accommodation Type",
                    "options": [
                        "Park lodge ($200/night)",
                        "Camping ($30/night)",
                        "Outside hotel ($120/night)",
                    ],
                    "context": "Comfort vs budget vs park experience",
                },
                {
                    "title": "Activity Level",
                    "options": [
                        "Easy trails only",
                        "Mix of easy and moderate",
                        "Include challenging hikes",
                    ],
                    "context": "Family fitness levels vary",
                },
            ],
        },
        "adventure_trip": {
            "name": "Costa Rica Eco-Adventure",
            "description": "Multi-family adventure featuring zip-lining, wildlife spotting, volcano hikes, and beach relaxation in Costa Rica's diverse landscapes.",
            "destination": "Costa Rica (Manuel Antonio & Arenal)",
            "duration": 5,
            "budget": 2800.0,
            "activities": [
                "Zip-lining through cloud forest canopy",
                "Arenal Volcano hiking and hot springs",
                "Manuel Antonio beach and wildlife",
                "Coffee plantation tour",
                "White water rafting (family-friendly)",
            ],
            "decision_scenarios": [
                {
                    "title": "Adventure Intensity",
                    "options": [
                        "High adventure (zip-line, rafting)",
                        "Moderate (hiking, wildlife)",
                        "Relaxed (beaches, culture)",
                    ],
                    "context": "Different comfort levels with adventure activities",
                },
                {
                    "title": "Transportation",
                    "options": [
                        "Rental car (flexible)",
                        "Private shuttle (convenient)",
                        "Public transport (budget)",
                    ],
                    "context": "Independence vs convenience vs cost",
                },
            ],
        },
    }

    cfg = template_map[template]
    today = date.today()

    trip_data = TripCreate(
        name=cfg["name"],
        description=cfg["description"],
        destination=cfg["destination"],
        start_date=today + timedelta(days=14),
        end_date=today + timedelta(days=14 + cfg["duration"]),
        budget_total=cfg["budget"],
        preferences={
            "trip_type": template.replace("_", " ").title(),
            "activities": cfg["activities"],
            "decision_scenarios": cfg["decision_scenarios"],
            "sample_trip": True,
            "template_used": template,
        },
        is_public=False,
        family_ids=[],  # The CreateTripUseCase will auto-attach creator’s family
    )

    return await use_case(trip_data, current_user.id)


@router.get("/", response_model=List[TripResponse])
@inject
async def get_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(require_permissions("trips", "read")),
    use_case: ListUserTripsUseCase = Depends(Provide[Container.list_user_trips_use_case]),
):
    """Get user's trips with optional filtering (application layer)."""

    return await use_case(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.get("/{trip_id}", response_model=TripDetail)
@inject
async def get_trip(
    trip_id: UUID,
    current_user: User = Depends(require_permissions("trips", "read")),
    use_case: GetTripUseCase = Depends(Provide[Container.get_trip_use_case]),
):
    """Get trip details by ID (application layer)."""

    trip = await use_case(trip_id, current_user.id)
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )
    return trip


@router.put("/{trip_id}", response_model=TripResponse)
@inject
async def update_trip(
    trip_id: UUID,
    trip_update: TripUpdate,
    current_user: User = Depends(require_permissions("trips", "update")),
    use_case: UpdateTripUseCase = Depends(Provide[Container.update_trip_use_case]),
):
    """Update trip details (application layer)."""

    try:
        return await use_case(trip_id, trip_update, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this trip",
        )


@router.delete("/{trip_id}")
@inject
async def delete_trip(
    trip_id: UUID,
    current_user: User = Depends(require_permissions("trips", "delete")),
    use_case: DeleteTripUseCase = Depends(Provide[Container.delete_trip_use_case]),
):
    """Delete a trip (application layer)."""

    try:
        await use_case(trip_id, current_user.id)
        return {"message": "Trip deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this trip",
        )


@router.get("/{trip_id}/stats", response_model=TripStats)
@inject
async def get_trip_stats(
    trip_id: UUID,
    current_user: User = Depends(require_permissions("trips", "read")),
    use_case: GetTripStatsUseCase = Depends(Provide[Container.get_trip_stats_use_case]),
):
    """Get trip statistics (application layer)."""

    stats = await use_case(trip_id, current_user.id)
    if stats is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return stats


# Participation endpoints


@router.post("/{trip_id}/participants", response_model=ParticipationResponse)
@inject
async def add_participant(
    trip_id: UUID,
    participation_data: ParticipationCreate,
    current_user: User = Depends(require_permissions("trips", "update")),
    use_case: AddParticipantUseCase = Depends(Provide[Container.add_participant_use_case]),
):
    """Add a family to the trip (application layer)."""

    try:
        return await use_case(trip_id, participation_data, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{trip_id}/participants", response_model=List[ParticipationResponse])
@inject
async def get_participants(
    trip_id: UUID,
    current_user: User = Depends(require_permissions("trips", "read")),
    use_case: GetParticipantsUseCase = Depends(Provide[Container.get_participants_use_case]),
):
    """Get trip participants (application layer)."""

    return await use_case(trip_id, current_user.id)


@router.put("/{trip_id}/participants/{participation_id}", response_model=ParticipationResponse)
@inject
async def update_participation(
    trip_id: UUID,
    participation_id: UUID,
    participation_update: ParticipationUpdate,
    current_user: User = Depends(require_permissions("trips", "update")),
    use_case: UpdateParticipationUseCase = Depends(
        Provide[Container.update_participation_use_case]
    ),
):
    """Update family participation status (application layer)."""

    try:
        return await use_case(participation_id, participation_update, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this participation",
        )


@router.delete("/{trip_id}/participants/{participation_id}")
@inject
async def remove_participant(
    trip_id: UUID,
    participation_id: UUID,
    current_user: User = Depends(require_permissions("trips", "delete")),
    use_case: RemoveParticipantUseCase = Depends(Provide[Container.remove_participant_use_case]),
):
    """Remove a family from the trip (application layer)."""

    try:
        await use_case(participation_id, current_user.id)
        return {"message": "Participant removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this participant",
        )


# Invitation endpoints


@router.post("/{trip_id}/invitations")
@inject
async def send_invitation(
    trip_id: UUID,
    invitation_data: TripInvitation,
    current_user: User = Depends(require_permissions("trips", "update")),
    use_case: SendInvitationUseCase = Depends(Provide[Container.send_invitation_use_case]),
):
    """Send trip invitation to a family (application layer)."""

    try:
        await use_case(trip_id, invitation_data, current_user.id)
        return {"message": "Invitation sent successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{trip_id}/messages")
async def get_trip_messages(
    trip_id: UUID,
    current_user: User = Depends(require_permissions("trips", "read")),
    # db: AsyncSession = Depends(get_db)
):
    """Get trip messages."""
    cosmos_service = TripCosmosOperations()

    messages = await cosmos_service.get_trip_messages(str(trip_id))
    if messages is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip messages not found")

    return messages
