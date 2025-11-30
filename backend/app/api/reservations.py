from __future__ import annotations

"""
Reservation management API endpoints.
Handles accommodation and activity reservations for trips.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from ..core.database_unified import get_cosmos_repository
from ..core.logging_config import get_logger
from ..core.zero_trust import require_permissions
from ..repositories.cosmos_unified import UnifiedCosmosRepository

router = APIRouter(tags=["reservations"])
logger = get_logger(__name__)


class ReservationType(str, Enum):
    ACCOMMODATION = "accommodation"
    ACTIVITY = "activity"
    TRANSPORTATION = "transportation"
    RESTAURANT = "restaurant"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ReservationCreate(BaseModel):
    trip_id: str
    type: ReservationType
    name: str
    description: Optional[str] = None
    date: date
    time: Optional[str] = None
    duration_hours: Optional[float] = None
    location: str
    address: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    cost_per_person: Optional[float] = None
    total_cost: Optional[float] = None
    capacity: Optional[int] = None
    participants: Optional[List[str]] = None  # user IDs
    booking_reference: Optional[str] = None
    cancellation_policy: Optional[str] = None
    special_requirements: Optional[str] = None
    external_booking_url: Optional[str] = None


class ReservationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    time: Optional[str] = None
    duration_hours: Optional[float] = None
    location: Optional[str] = None
    address: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    cost_per_person: Optional[float] = None
    total_cost: Optional[float] = None
    capacity: Optional[int] = None
    participants: Optional[List[str]] = None
    booking_reference: Optional[str] = None
    status: Optional[ReservationStatus] = None
    cancellation_policy: Optional[str] = None
    special_requirements: Optional[str] = None
    external_booking_url: Optional[str] = None


class ReservationResponse(BaseModel):
    id: str
    trip_id: str
    type: ReservationType
    name: str
    description: Optional[str]
    date: date
    time: Optional[str]
    duration_hours: Optional[float]
    location: str
    address: Optional[str]
    contact_info: Optional[Dict[str, str]]
    cost_per_person: Optional[float]
    total_cost: Optional[float]
    capacity: Optional[int]
    participant_count: int
    participants: List[Dict[str, Any]]
    booking_reference: Optional[str]
    status: ReservationStatus
    cancellation_policy: Optional[str]
    special_requirements: Optional[str]
    external_booking_url: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.get("/trip/{trip_id}", response_model=List[ReservationResponse])
async def get_trip_reservations(
    trip_id: str,
    type: Optional[ReservationType] = None,
    status: Optional[ReservationStatus] = None,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get all reservations for a trip with optional filtering."""
    try:
        # Query reservations from Cosmos DB
        query = f"SELECT * FROM c WHERE c.entity_type = 'reservation' AND c.trip_id = '{trip_id}'"

        if type:
            query += f" AND c.type = '{type.value}'"
        if status:
            query += f" AND c.status = '{status.value}'"

        query += " ORDER BY c.date ASC"

        items = await cosmos_repo.query_items(query)

        reservations = []
        for item in items:
            reservations.append(
                ReservationResponse(
                    id=item["id"],
                    trip_id=item["trip_id"],
                    type=item["type"],
                    name=item["name"],
                    description=item.get("description"),
                    date=item["date"],
                    time=item.get("time"),
                    duration_hours=item.get("duration_hours"),
                    location=item["location"],
                    address=item.get("address"),
                    contact_info=item.get("contact_info"),
                    cost_per_person=item.get("cost_per_person"),
                    total_cost=item.get("total_cost"),
                    capacity=item.get("capacity"),
                    participant_count=len(item.get("participants", [])),
                    participants=item.get("participants", []),
                    booking_reference=item.get("booking_reference"),
                    status=item.get("status", ReservationStatus.PENDING),
                    cancellation_policy=item.get("cancellation_policy"),
                    special_requirements=item.get("special_requirements"),
                    external_booking_url=item.get("external_booking_url"),
                    created_at=item.get("created_at", datetime.utcnow()),
                    updated_at=item.get("updated_at", datetime.utcnow()),
                )
            )

        return reservations

    except Exception as e:
        logger.error(f"Error fetching reservations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch reservations"
        )


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation: ReservationCreate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Create a new reservation for a trip."""
    try:
        import uuid

        reservation_id = str(uuid.uuid4())
        now = datetime.utcnow()

        reservation_doc = {
            "id": reservation_id,
            "pk": f"reservation_{reservation_id}",
            "entity_type": "reservation",
            "trip_id": reservation.trip_id,
            "type": reservation.type.value,
            "name": reservation.name,
            "description": reservation.description,
            "date": reservation.date.isoformat(),
            "time": reservation.time,
            "duration_hours": reservation.duration_hours,
            "location": reservation.location,
            "address": reservation.address,
            "contact_info": reservation.contact_info,
            "cost_per_person": reservation.cost_per_person,
            "total_cost": reservation.total_cost,
            "capacity": reservation.capacity,
            "participants": reservation.participants or [],
            "booking_reference": reservation.booking_reference,
            "status": ReservationStatus.PENDING.value,
            "cancellation_policy": reservation.cancellation_policy,
            "special_requirements": reservation.special_requirements,
            "external_booking_url": reservation.external_booking_url,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        created = await cosmos_repo.create_item(reservation_doc)

        return ReservationResponse(
            id=created["id"],
            trip_id=created["trip_id"],
            type=created["type"],
            name=created["name"],
            description=created.get("description"),
            date=reservation.date,
            time=created.get("time"),
            duration_hours=created.get("duration_hours"),
            location=created["location"],
            address=created.get("address"),
            contact_info=created.get("contact_info"),
            cost_per_person=created.get("cost_per_person"),
            total_cost=created.get("total_cost"),
            capacity=created.get("capacity"),
            participant_count=len(created.get("participants", [])),
            participants=created.get("participants", []),
            booking_reference=created.get("booking_reference"),
            status=ReservationStatus.PENDING,
            cancellation_policy=created.get("cancellation_policy"),
            special_requirements=created.get("special_requirements"),
            external_booking_url=created.get("external_booking_url"),
            created_at=now,
            updated_at=now,
        )

    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create reservation"
        )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get a specific reservation by ID."""
    try:
        reservation = await cosmos_repo.get_item(reservation_id, f"reservation_{reservation_id}")

        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )

        return ReservationResponse(
            id=reservation["id"],
            trip_id=reservation["trip_id"],
            type=reservation["type"],
            name=reservation["name"],
            description=reservation.get("description"),
            date=reservation["date"],
            time=reservation.get("time"),
            duration_hours=reservation.get("duration_hours"),
            location=reservation["location"],
            address=reservation.get("address"),
            contact_info=reservation.get("contact_info"),
            cost_per_person=reservation.get("cost_per_person"),
            total_cost=reservation.get("total_cost"),
            capacity=reservation.get("capacity"),
            participant_count=len(reservation.get("participants", [])),
            participants=reservation.get("participants", []),
            booking_reference=reservation.get("booking_reference"),
            status=reservation.get("status", ReservationStatus.PENDING),
            cancellation_policy=reservation.get("cancellation_policy"),
            special_requirements=reservation.get("special_requirements"),
            external_booking_url=reservation.get("external_booking_url"),
            created_at=reservation.get("created_at", datetime.utcnow()),
            updated_at=reservation.get("updated_at", datetime.utcnow()),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch reservation"
        )


@router.patch("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: str,
    update_data: ReservationUpdate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Update a reservation."""
    try:
        existing = await cosmos_repo.get_item(reservation_id, f"reservation_{reservation_id}")

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if isinstance(value, Enum):
                    existing[key] = value.value
                elif isinstance(value, date):
                    existing[key] = value.isoformat()
                else:
                    existing[key] = value

        existing["updated_at"] = datetime.utcnow().isoformat()

        updated = await cosmos_repo.upsert_item(existing)

        return ReservationResponse(
            id=updated["id"],
            trip_id=updated["trip_id"],
            type=updated["type"],
            name=updated["name"],
            description=updated.get("description"),
            date=updated["date"],
            time=updated.get("time"),
            duration_hours=updated.get("duration_hours"),
            location=updated["location"],
            address=updated.get("address"),
            contact_info=updated.get("contact_info"),
            cost_per_person=updated.get("cost_per_person"),
            total_cost=updated.get("total_cost"),
            capacity=updated.get("capacity"),
            participant_count=len(updated.get("participants", [])),
            participants=updated.get("participants", []),
            booking_reference=updated.get("booking_reference"),
            status=updated.get("status", ReservationStatus.PENDING),
            cancellation_policy=updated.get("cancellation_policy"),
            special_requirements=updated.get("special_requirements"),
            external_booking_url=updated.get("external_booking_url"),
            created_at=updated.get("created_at", datetime.utcnow()),
            updated_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update reservation"
        )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Delete a reservation."""
    try:
        existing = await cosmos_repo.get_item(reservation_id, f"reservation_{reservation_id}")

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )

        await cosmos_repo.delete_item(reservation_id, f"reservation_{reservation_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete reservation"
        )


@router.post("/{reservation_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def add_participant(
    reservation_id: str,
    user_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Add a participant to a reservation."""
    try:
        existing = await cosmos_repo.get_item(reservation_id, f"reservation_{reservation_id}")

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )

        participants = existing.get("participants", [])
        if user_id not in participants:
            participants.append(user_id)
            existing["participants"] = participants
            existing["updated_at"] = datetime.utcnow().isoformat()
            await cosmos_repo.upsert_item(existing)

        return {"message": "Participant added successfully", "participant_count": len(participants)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding participant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add participant"
        )


@router.delete("/{reservation_id}/participants/{user_id}", status_code=status.HTTP_200_OK)
async def remove_participant(
    reservation_id: str,
    user_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Remove a participant from a reservation."""
    try:
        existing = await cosmos_repo.get_item(reservation_id, f"reservation_{reservation_id}")

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
            )

        participants = existing.get("participants", [])
        if user_id in participants:
            participants.remove(user_id)
            existing["participants"] = participants
            existing["updated_at"] = datetime.utcnow().isoformat()
            await cosmos_repo.upsert_item(existing)

        return {
            "message": "Participant removed successfully",
            "participant_count": len(participants),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing participant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove participant"
        )
