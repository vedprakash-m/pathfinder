from __future__ import annotations

"""
Trip management API endpoints - Reconstructed for unified Cosmos DB.
"""

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from app.repositories.cosmos_unified import (
    UnifiedCosmosRepository,
    UserDocument,
    TripDocument,
)
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.core.zero_trust import require_permissions
from app.schemas.trip import (
    TripCreate,
    TripResponse,
    TripUpdate,
    TripStats,
    TripInvitation,
    ParticipationCreate,
    ParticipationResponse,
    ParticipationUpdate,
)
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()


async def get_cosmos_repo() -> UnifiedCosmosRepository:
    """Get Cosmos repository dependency."""
    cosmos_service = get_cosmos_service()
    return cosmos_service.get_repository()


@router.post("/", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Create a new trip."""
    try:
        # Create trip document
        trip_doc = TripDocument(
            id=str(uuid4()),
            pk=f"trip_{str(uuid4())}",
            title=trip_data.title,
            description=trip_data.description,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            budget=trip_data.budget,
            organizer_user_id=current_user.id,
            status="planning",
        )

        created_trip = await cosmos_repo.create_document(trip_doc)
        return TripResponse.from_document(created_trip)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Get trip by ID."""
    try:
        trip = await cosmos_repo.get_document(f"trip_{trip_id}", "trip")
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
        return TripResponse.from_document(trip)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: str,
    trip_update: TripUpdate,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Update trip information."""
    try:
        trip = await cosmos_repo.get_document(f"trip_{trip_id}", "trip")
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Update fields
        update_data = trip_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trip, field, value)

        updated_trip = await cosmos_repo.update_document(trip)
        return TripResponse.from_document(updated_trip)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


# Sample trip creation for Golden Path onboarding
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
            }
        ],
    }
}


@router.post(
    "/sample", response_model=TripResponse, status_code=status.HTTP_201_CREATED
)
async def create_sample_trip(
    template: str = Query(
        "weekend_getaway",
        regex="^(weekend_getaway|family_vacation|adventure_trip)$",
        description="Sample trip template to use",
    ),
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Create a pre-populated sample trip for Golden Path onboarding."""
    # Implementation using template_map data
    pass
