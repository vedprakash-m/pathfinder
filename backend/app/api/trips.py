"""
Trip management API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.trip import (
    TripCreate, TripUpdate, TripResponse, TripDetail, TripStats,
    ParticipationCreate, ParticipationUpdate, ParticipationResponse,
    TripInvitation
)
from app.services.trip_service import TripService

router = APIRouter()


@router.post("/", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new trip."""
    trip_service = TripService(db)
    
    try:
        trip = await trip_service.create_trip(trip_data, current_user.id)
        return trip
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[TripResponse])
async def get_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's trips with optional filtering."""
    trip_service = TripService(db)
    return await trip_service.get_user_trips(
        current_user.id, 
        skip=skip, 
        limit=limit, 
        status_filter=status_filter
    )


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trip details by ID."""
    trip_service = TripService(db)
    
    trip = await trip_service.get_trip_by_id(trip_id, current_user.id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    return trip


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: UUID,
    trip_update: TripUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update trip details."""
    trip_service = TripService(db)
    
    try:
        trip = await trip_service.update_trip(trip_id, trip_update, current_user.id)
        return trip
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this trip"
        )


@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a trip."""
    trip_service = TripService(db)
    
    try:
        await trip_service.delete_trip(trip_id, current_user.id)
        return {"message": "Trip deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this trip"
        )


@router.get("/{trip_id}/stats", response_model=TripStats)
async def get_trip_stats(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trip statistics."""
    trip_service = TripService(db)
    
    stats = await trip_service.get_trip_stats(trip_id, current_user.id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    return stats


# Participation endpoints

@router.post("/{trip_id}/participants", response_model=ParticipationResponse)
async def add_participant(
    trip_id: UUID,
    participation_data: ParticipationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a family to the trip."""
    trip_service = TripService(db)
    
    # Override trip_id from URL
    participation_data.trip_id = str(trip_id)
    
    try:
        participation = await trip_service.add_participant(participation_data, current_user.id)
        return participation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{trip_id}/participants", response_model=List[ParticipationResponse])
async def get_participants(
    trip_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trip participants."""
    trip_service = TripService(db)
    return await trip_service.get_trip_participants(trip_id, current_user.id)


@router.put("/{trip_id}/participants/{participation_id}", response_model=ParticipationResponse)
async def update_participation(
    trip_id: UUID,
    participation_id: UUID,
    participation_update: ParticipationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update family participation status."""
    trip_service = TripService(db)
    
    try:
        participation = await trip_service.update_participation(
            participation_id, participation_update, current_user.id
        )
        return participation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this participation"
        )


@router.delete("/{trip_id}/participants/{participation_id}")
async def remove_participant(
    trip_id: UUID,
    participation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a family from the trip."""
    trip_service = TripService(db)
    
    try:
        await trip_service.remove_participant(participation_id, current_user.id)
        return {"message": "Participant removed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to remove this participant"
        )


# Invitation endpoints

@router.post("/{trip_id}/invitations")
async def send_invitation(
    trip_id: UUID,
    invitation_data: TripInvitation,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Send trip invitation to a family."""
    trip_service = TripService(db)
    
    # Override trip_id from URL
    invitation_data.trip_id = str(trip_id)
    
    try:
        await trip_service.send_invitation(invitation_data, current_user.id)
        return {"message": "Invitation sent successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )