"""
Reservation management API endpoints.
Handles accommodation and activity reservations for trips.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date
from enum import Enum

from ..core.database import get_db
from ..core.zero_trust import require_permissions
from ..models.user import User
from ..models.trip import Trip, TripParticipation
from ..core.logging_config import get_logger

router = APIRouter(tags=["reservations"])
logger = get_logger(__name__)


# Pydantic models for reservation API
from pydantic import BaseModel, Field


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
    trip_id: int
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
    participants: Optional[List[int]] = None  # user IDs
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
    participants: Optional[List[int]] = None
    booking_reference: Optional[str] = None
    status: Optional[ReservationStatus] = None
    cancellation_policy: Optional[str] = None
    special_requirements: Optional[str] = None
    external_booking_url: Optional[str] = None


class ReservationResponse(BaseModel):
    id: int
    trip_id: int
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
    participants: List[Dict[str, Any]]  # user info
    booking_reference: Optional[str]
    status: ReservationStatus
    cancellation_policy: Optional[str]
    special_requirements: Optional[str]
    external_booking_url: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Mock Reservation model for demonstration (would be in models/reservation.py)
class Reservation:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.id = getattr(self, "id", 1)
        self.created_at = getattr(self, "created_at", datetime.utcnow())
        self.updated_at = getattr(self, "updated_at", datetime.utcnow())
        self.status = getattr(self, "status", ReservationStatus.PENDING)


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation_data: ReservationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "create")),
):
    """Create a new reservation for a trip."""
    try:
        # Verify trip exists and user has access
        trip = db.query(Trip).filter(Trip.id == reservation_data.trip_id).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        # Check if user is a participant
        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == reservation_data.trip_id,
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create reservations for this trip",
            )

        # Validate participants are trip members
        if reservation_data.participants:
            trip_participant_ids = [p.user_id for p in trip.participations]
            invalid_participants = [
                p_id for p_id in reservation_data.participants if p_id not in trip_participant_ids
            ]

            if invalid_participants:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid participants: {invalid_participants}",
                )

        # Create reservation (mock implementation)
        reservation_dict = reservation_data.dict()
        reservation_dict.update(
            {
                "id": 1,  # Would be auto-generated
                "created_by": current_user.id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": ReservationStatus.PENDING,
            }
        )

        # Mock participant details
        participant_details = []
        if reservation_data.participants:
            for user_id in reservation_data.participants:
                # Would query actual user data
                participant_details.append(
                    {
                        "id": user_id,
                        "name": f"User {user_id}",
                        "email": f"user{user_id}@example.com",
                    }
                )

        reservation_dict["participants"] = participant_details
        reservation_dict["participant_count"] = len(participant_details)

        logger.info(
            f"Reservation created for trip {reservation_data.trip_id} by user {current_user.id}"
        )

        return ReservationResponse(**reservation_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating reservation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create reservation"
        )


@router.get("/trip/{trip_id}", response_model=List[ReservationResponse])
async def get_trip_reservations(
    trip_id: int,
    request: Request,
    reservation_type: Optional[ReservationType] = Query(
        None, description="Filter by reservation type"
    ),
    status_filter: Optional[ReservationStatus] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Filter reservations from this date"),
    date_to: Optional[date] = Query(None, description="Filter reservations to this date"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "read")),
):
    """Get all reservations for a trip."""
    try:
        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == trip_id,
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this trip"
            )

        # Mock reservations data (would query actual reservation table)
        mock_reservations = [
            {
                "id": 1,
                "trip_id": trip_id,
                "type": ReservationType.ACCOMMODATION,
                "name": "Grand Hotel",
                "description": "Luxury hotel in downtown",
                "date": date(2024, 7, 15),
                "time": "15:00",
                "duration_hours": 24.0,
                "location": "Downtown",
                "address": "123 Main St",
                "contact_info": {"phone": "+1-555-0123", "email": "reservations@grandhotel.com"},
                "cost_per_person": 150.0,
                "total_cost": 600.0,
                "capacity": 4,
                "participant_count": 4,
                "participants": [
                    {"id": 1, "name": "John Doe", "email": "john@example.com"},
                    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
                ],
                "booking_reference": "GH123456",
                "status": ReservationStatus.CONFIRMED,
                "cancellation_policy": "Free cancellation up to 24 hours before check-in",
                "special_requirements": "Non-smoking rooms",
                "external_booking_url": "https://grandhotel.com/booking/GH123456",
                "created_by": current_user.id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "id": 2,
                "trip_id": trip_id,
                "type": ReservationType.ACTIVITY,
                "name": "City Museum Tour",
                "description": "Guided tour of the city museum",
                "date": date(2024, 7, 16),
                "time": "10:00",
                "duration_hours": 2.5,
                "location": "City Museum",
                "address": "456 Culture Ave",
                "contact_info": {"phone": "+1-555-0124", "email": "tours@citymuseum.com"},
                "cost_per_person": 25.0,
                "total_cost": 100.0,
                "capacity": 20,
                "participant_count": 4,
                "participants": [
                    {"id": 1, "name": "John Doe", "email": "john@example.com"},
                    {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
                ],
                "booking_reference": "CM789012",
                "status": ReservationStatus.CONFIRMED,
                "cancellation_policy": "Refund available up to 48 hours before tour",
                "special_requirements": "Wheelchair accessible",
                "external_booking_url": "https://citymuseum.com/tours/CM789012",
                "created_by": current_user.id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        ]

        # Apply filters
        filtered_reservations = mock_reservations

        if reservation_type:
            filtered_reservations = [
                r for r in filtered_reservations if r["type"] == reservation_type
            ]

        if status_filter:
            filtered_reservations = [
                r for r in filtered_reservations if r["status"] == status_filter
            ]

        if date_from:
            filtered_reservations = [r for r in filtered_reservations if r["date"] >= date_from]

        if date_to:
            filtered_reservations = [r for r in filtered_reservations if r["date"] <= date_to]

        # Apply pagination
        paginated_reservations = filtered_reservations[skip : skip + limit]

        return [ReservationResponse(**res) for res in paginated_reservations]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservations for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch reservations"
        )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "read")),
):
    """Get a specific reservation by ID."""
    try:
        # Mock reservation lookup (would query actual reservation table)
        mock_reservation = {
            "id": reservation_id,
            "trip_id": 1,
            "type": ReservationType.ACCOMMODATION,
            "name": "Grand Hotel",
            "description": "Luxury hotel in downtown",
            "date": date(2024, 7, 15),
            "time": "15:00",
            "duration_hours": 24.0,
            "location": "Downtown",
            "address": "123 Main St",
            "contact_info": {"phone": "+1-555-0123", "email": "reservations@grandhotel.com"},
            "cost_per_person": 150.0,
            "total_cost": 600.0,
            "capacity": 4,
            "participant_count": 2,
            "participants": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            ],
            "booking_reference": "GH123456",
            "status": ReservationStatus.CONFIRMED,
            "cancellation_policy": "Free cancellation up to 24 hours before check-in",
            "special_requirements": "Non-smoking rooms",
            "external_booking_url": "https://grandhotel.com/booking/GH123456",
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == mock_reservation["trip_id"]).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == mock_reservation["trip_id"],
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this reservation",
            )

        return ReservationResponse(**mock_reservation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservation {reservation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch reservation"
        )


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    reservation_data: ReservationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "update")),
):
    """Update a reservation."""
    try:
        # Mock reservation lookup
        mock_reservation = {
            "id": reservation_id,
            "trip_id": 1,
            "type": ReservationType.ACCOMMODATION,
            "name": "Grand Hotel",
            "description": "Luxury hotel in downtown",
            "date": date(2024, 7, 15),
            "time": "15:00",
            "duration_hours": 24.0,
            "location": "Downtown",
            "address": "123 Main St",
            "contact_info": {"phone": "+1-555-0123", "email": "reservations@grandhotel.com"},
            "cost_per_person": 150.0,
            "total_cost": 600.0,
            "capacity": 4,
            "participant_count": 2,
            "participants": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            ],
            "booking_reference": "GH123456",
            "status": ReservationStatus.CONFIRMED,
            "cancellation_policy": "Free cancellation up to 24 hours before check-in",
            "special_requirements": "Non-smoking rooms",
            "external_booking_url": "https://grandhotel.com/booking/GH123456",
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == mock_reservation["trip_id"]).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == mock_reservation["trip_id"],
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this reservation",
            )

        # Update reservation (mock implementation)
        update_data = reservation_data.dict(exclude_unset=True)
        mock_reservation.update(update_data)
        mock_reservation["updated_at"] = datetime.utcnow()

        # Update participant details if participants changed
        if "participants" in update_data and update_data["participants"]:
            participant_details = []
            for user_id in update_data["participants"]:
                participant_details.append(
                    {
                        "id": user_id,
                        "name": f"User {user_id}",
                        "email": f"user{user_id}@example.com",
                    }
                )
            mock_reservation["participants"] = participant_details
            mock_reservation["participant_count"] = len(participant_details)

        logger.info(f"Reservation {reservation_id} updated by user {current_user.id}")

        return ReservationResponse(**mock_reservation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reservation {reservation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update reservation"
        )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reservation(
    reservation_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "delete")),
):
    """Cancel a reservation."""
    try:
        # Mock reservation lookup
        mock_reservation = {"id": reservation_id, "trip_id": 1, "created_by": current_user.id}

        # Verify trip access and permissions
        trip = db.query(Trip).filter(Trip.id == mock_reservation["trip_id"]).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == mock_reservation["trip_id"],
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this reservation",
            )

        # Additional check: only creator or trip admin can cancel
        if mock_reservation["created_by"] != current_user.id and participation.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only reservation creator or trip admin can cancel reservations",
            )

        # Cancel reservation (mock implementation)
        logger.info(f"Reservation {reservation_id} cancelled by user {current_user.id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling reservation {reservation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel reservation"
        )


@router.post("/{reservation_id}/participants", response_model=ReservationResponse)
async def add_participants(
    reservation_id: int,
    participant_ids: List[int],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "update")),
):
    """Add participants to a reservation."""
    try:
        # Mock reservation lookup
        mock_reservation = {
            "id": reservation_id,
            "trip_id": 1,
            "type": ReservationType.ACTIVITY,
            "name": "City Museum Tour",
            "description": "Guided tour of the city museum",
            "date": date(2024, 7, 16),
            "time": "10:00",
            "duration_hours": 2.5,
            "location": "City Museum",
            "address": "456 Culture Ave",
            "contact_info": {"phone": "+1-555-0124", "email": "tours@citymuseum.com"},
            "cost_per_person": 25.0,
            "total_cost": 100.0,
            "capacity": 20,
            "participant_count": 2,
            "participants": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
            ],
            "booking_reference": "CM789012",
            "status": ReservationStatus.CONFIRMED,
            "cancellation_policy": "Refund available up to 48 hours before tour",
            "special_requirements": "Wheelchair accessible",
            "external_booking_url": "https://citymuseum.com/tours/CM789012",
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == mock_reservation["trip_id"]).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == mock_reservation["trip_id"],
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this reservation",
            )

        # Validate capacity
        current_participants = len(mock_reservation["participants"])
        if (
            mock_reservation["capacity"]
            and current_participants + len(participant_ids) > mock_reservation["capacity"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Adding participants would exceed reservation capacity",
            )

        # Add new participants (mock implementation)
        for user_id in participant_ids:
            if user_id not in [p["id"] for p in mock_reservation["participants"]]:
                mock_reservation["participants"].append(
                    {
                        "id": user_id,
                        "name": f"User {user_id}",
                        "email": f"user{user_id}@example.com",
                    }
                )

        mock_reservation["participant_count"] = len(mock_reservation["participants"])
        mock_reservation["total_cost"] = (
            mock_reservation["participant_count"] * mock_reservation["cost_per_person"]
        )
        mock_reservation["updated_at"] = datetime.utcnow()

        logger.info(f"Participants added to reservation {reservation_id} by user {current_user.id}")

        return ReservationResponse(**mock_reservation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding participants to reservation {reservation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add participants"
        )


@router.delete("/{reservation_id}/participants/{user_id}", response_model=ReservationResponse)
async def remove_participant(
    reservation_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("reservations", "update")),
):
    """Remove a participant from a reservation."""
    try:
        # Mock reservation lookup
        mock_reservation = {
            "id": reservation_id,
            "trip_id": 1,
            "type": ReservationType.ACTIVITY,
            "name": "City Museum Tour",
            "description": "Guided tour of the city museum",
            "date": date(2024, 7, 16),
            "time": "10:00",
            "duration_hours": 2.5,
            "location": "City Museum",
            "address": "456 Culture Ave",
            "contact_info": {"phone": "+1-555-0124", "email": "tours@citymuseum.com"},
            "cost_per_person": 25.0,
            "total_cost": 150.0,
            "capacity": 20,
            "participant_count": 6,
            "participants": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
                {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"},
            ],
            "booking_reference": "CM789012",
            "status": ReservationStatus.CONFIRMED,
            "cancellation_policy": "Refund available up to 48 hours before tour",
            "special_requirements": "Wheelchair accessible",
            "external_booking_url": "https://citymuseum.com/tours/CM789012",
            "created_by": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == mock_reservation["trip_id"]).first()
        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        participation = (
            db.query(TripParticipation)
            .filter(
                and_(
                    TripParticipation.trip_id == mock_reservation["trip_id"],
                    TripParticipation.user_id == current_user.id,
                )
            )
            .first()
        )

        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this reservation",
            )

        # Remove participant (mock implementation)
        mock_reservation["participants"] = [
            p for p in mock_reservation["participants"] if p["id"] != user_id
        ]

        mock_reservation["participant_count"] = len(mock_reservation["participants"])
        mock_reservation["total_cost"] = (
            mock_reservation["participant_count"] * mock_reservation["cost_per_person"]
        )
        mock_reservation["updated_at"] = datetime.utcnow()

        logger.info(
            f"Participant {user_id} removed from reservation {reservation_id} by user {current_user.id}"
        )

        return ReservationResponse(**mock_reservation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing participant from reservation {reservation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove participant"
        )
