from __future__ import annotations
"""
Reservation management API endpoints.
Handles accommodation and activity reservations for trips.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..core.database_unified import get_cosmos_repository
from ..core.logging_config import get_logger
from ..core.zero_trust import require_permissions
# SQL User model removed - use Cosmos UserDocument
from ..repositories.cosmos_unified import UnifiedCosmosRepository

router = APIRouter(tags=["reservations"])
logger = get_logger(__name__)


# Pydantic models for reservation API
from pydantic import BaseModel


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
contact_info: Optional[dict[str, str]] = None
cost_per_person: Optional[float] = None
total_cost: Optional[float] = None
capacity: Optional[int] = None
participants: Optional[list[int]] = None  # user IDs
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
contact_info: Optional[dict[str, str]] = None
cost_per_person: Optional[float] = None
total_cost: Optional[float] = None
capacity: Optional[int] = None
participants: Optional[list[int]] = None
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
contact_info: Optional[dict[str, str]]
cost_per_person: Optional[float]
total_cost: Optional[float]
capacity: Optional[int]
participant_count: int
participants: list[dict[str, Any]]  # user info
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
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: dict = Depends(require_permissions("reservations", "create")
):
    """Create a new reservation for a trip."""
try:
        # Verify trip exists and user has access
trip = await cosmos_repo.get_trip_by_id(str(reservation_data.trip_id))
if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

# Check if user is a participant (check if user has access to trip)
user_trips = await cosmos_repo.get_user_trips(current_user["id"])
if not any(t.id == str(reservation_data.trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
detail="Not authorized to create reservations for this trip",
)
raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
detail="Not authorized to create reservations for this trip",
)

# Validate participants are trip members if specified
if reservation_data.participants:
            # Get trip participants from family members
trip_families = await cosmos_repo.get_trip_families(str(reservation_data.trip_id))
trip_participant_ids = []
for family in trip_families:
                family_members = await cosmos_repo.get_family_members(family.id)
trip_participant_ids.extend([member.id for member in family_members])

invalid_participants = [
str(p_id)
for p_id in reservation_data.participants
if str(p_id) not in trip_participant_ids
]

if invalid_participants:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
detail=f"Invalid participants: (invalid_participants)",
)

# Create reservation using Cosmos DB
reservation_dict = reservation_data.model_dump()
reservation_dict.update(
            (
                "trip_id": str(reservation_data.trip_id),
"created_by": current_user["id"],
"date": reservation_data.date.isoformat(),
"participants": [str(p) for p in (reservation_data.participants or [])],
)
)

reservation_doc = await cosmos_repo.create_reservation(reservation_dict)

# Get participant details for response
participant_details = []
if reservation_data.participants:
            for user_id in reservation_data.participants:
                user = await cosmos_repo.get_user_by_id(str(user_id))
if user:
                    participant_details.append(
                        (
                            "id": user_id,
"name": user.name or f"User(user_id)",
"email": user.email,
)
)

# Prepare response
response_data = {
            "id": int(reservation_doc.id.split("-")[0], 16)
% (10**9),  # Generate numeric ID for response
"trip_id": int(reservation_data.trip_id),
"type": reservation_data.type,
"name": reservation_data.name,
"description": reservation_data.description,
"date": reservation_data.date,
"time": reservation_data.time,
"duration_hours": reservation_data.duration_hours,
"location": reservation_data.location,
"address": reservation_data.address,
"contact_info": reservation_data.contact_info,
"cost_per_person": reservation_data.cost_per_person,
"total_cost": reservation_data.total_cost,
"capacity": reservation_data.capacity,
"participants": participant_details,
"participant_count": len(participant_details),
"booking_reference": reservation_data.booking_reference,
"status": ReservationStatus.PENDING,
"cancellation_policy": reservation_data.cancellation_policy,
"special_requirements": reservation_data.special_requirements,
"external_booking_url": reservation_data.external_booking_url,
"created_by": int(current_user["id"]),
"created_at": reservation_doc.created_at,
"updated_at": reservation_doc.updated_at,
)

logger.info(
            f"Reservation created for trip(reservation_data.trip_id) by user(current_user['id'])"
)

return ReservationResponse(**response_data)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error creating reservation: (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to create reservation",
)


@router.get("/trip/(trip_id)", response_model=list[ReservationResponse])
async def get_trip_reservations(
    trip_id: int,
request: Request,
reservation_type: Optional[ReservationType] = Query(
        None, description="Filter by reservation type"
),:
    status_filter: Optional[ReservationStatus] = Query(None, description="Filter by status"),
date_from: Optional[date] = Query(None, description="Filter reservations from this date"),
date_to: Optional[date] = Query(None, description="Filter reservations to this date"),
skip: int = 0,
limit: int = 100,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
current_user: dict = Depends(require_permissions("reservations", "read")
):
    """Get all reservations for a trip."""
try:
        # Verify trip access
trip = await cosmos_repo.get_trip_by_id(str(trip_id))
if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

# Check if user has access to trip
user_trips = await cosmos_repo.get_user_trips(current_user["id"])
if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
detail="Not authorized to access this trip",
)

# Get reservations from Cosmos DB
reservations = await cosmos_repo.get_trip_reservations(str(trip_id))

# Convert to response format
result = []
for reservation in reservations:
            # Apply filters
if reservation_type and reservation.type != reservation_type:
                continue

if status_filter and reservation.status != status_filter:
                continue

# Parse date for filtering
try:
                res_date = date.fromisoformat(reservation.date)
if date_from and res_date < date_from:
                    continue
if date_to and res_date > date_to:
                    continue
except Exception:
                pass  # Skip date filtering if date format is invalid

# Get participant details
participant_details = []
if reservation.participants:
                for user_id in reservation.participants:
                    user = await cosmos_repo.get_user_by_id(user_id)
if user:
                        participant_details.append(
                            (
                                "id": int(user_id),
"name": user.name or f"User(user_id)",
"email": user.email,
)
)

response_data = {
                "id": int(reservation.id.split("-")[0], 16) % (10**9),
"trip_id": trip_id,
"type": reservation.type,
"name": reservation.name,
"description": reservation.description,
"date": date.fromisoformat(reservation.date),
"time": reservation.time,
"duration_hours": reservation.duration_hours,
"location": reservation.location,
"address": reservation.address,
"contact_info": reservation.contact_info,
"cost_per_person": reservation.cost_per_person,
"total_cost": reservation.total_cost,
"capacity": reservation.capacity,
"participants": participant_details,
"participant_count": len(participant_details),
"booking_reference": reservation.booking_reference,
"status": reservation.status,
"cancellation_policy": reservation.cancellation_policy,
"special_requirements": reservation.special_requirements,
"external_booking_url": reservation.external_booking_url,
"created_by": int(reservation.created_by),
"created_at": reservation.created_at,
"updated_at": reservation.updated_at,
)
result.append(ReservationResponse(**response_data))

# Apply pagination
return result[skip : skip + limit]

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error fetching reservations for trip(trip_id): (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to fetch reservations",
)


@router.get("/(reservation_id)", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
request: Request,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: dict = Depends(require_permissions("reservations", "read")
):
    """Get a specific reservation by ID."""
try:
        # Convert numeric ID to string format for document lookup
# This is a simple implementation - in production you'd want a better ID mapping
reservation_uuid = f"(reservation_id:08x)-0000-0000-0000-000000000000"

reservation_doc = await cosmos_repo._get_document_by_id(reservation_uuid)
if not reservation_doc or reservation_doc.get("entity_type") != "reservation":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found"
)

# Verify user has access to the trip
trip_id = reservation_doc["trip_id"]
user_trips = await cosmos_repo.get_user_trips(current_user["id"])
if not any(t.id == trip_id for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
detail="Not authorized to access this reservation",
)

# Get participant details
participant_details = []
if reservation_doc.get("participants"):
            for user_id in reservation_doc["participants"]:
                user = await cosmos_repo.get_user_by_id(user_id)
if user:
                    participant_details.append(
                        (
                            "id": int(user_id),
"name": user.name or f"User(user_id)",
"email": user.email,
)
)

response_data = {
            "id": reservation_id,
"trip_id": int(trip_id),
"type": reservation_doc["type"],
"name": reservation_doc["name"],
"description": reservation_doc.get("description"),
"date": date.fromisoformat(reservation_doc["date"]),
"time": reservation_doc.get("time"),
"duration_hours": reservation_doc.get("duration_hours"),
"location": reservation_doc["location"],
"address": reservation_doc.get("address"),
"contact_info": reservation_doc.get("contact_info"),
"cost_per_person": reservation_doc.get("cost_per_person"),
"total_cost": reservation_doc.get("total_cost"),
"capacity": reservation_doc.get("capacity"),
"participants": participant_details,
"participant_count": len(participant_details),
"booking_reference": reservation_doc.get("booking_reference"),
"status": reservation_doc["status"],
"cancellation_policy": reservation_doc.get("cancellation_policy"),
"special_requirements": reservation_doc.get("special_requirements"),
"external_booking_url": reservation_doc.get("external_booking_url"),
"created_by": int(reservation_doc["created_by"]),
"created_at": datetime.fromisoformat(reservation_doc["created_at"]),
"updated_at": datetime.fromisoformat(reservation_doc["updated_at"]),
)

return ReservationResponse(**response_data)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error fetching reservation(reservation_id): (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to fetch reservation",
)


@router.put("/(reservation_id)", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
reservation_data: ReservationUpdate,
request: Request,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: dict = Depends(require_permissions("reservations", "update")
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
"contact_info": (
                "phone": "+1-555-0123",
"email": "reservations@grandhotel.com",
),
"cost_per_person": 150.0,
"total_cost": 600.0,
"capacity": 4,
"participant_count": 2,
"participants": [
("id": 1, "name": "John Doe", "email": "john@example.com"),
("id": 2, "name": "Jane Smith", "email": "jane@example.com"),
],
"booking_reference": "GH123456",
"status": ReservationStatus.CONFIRMED,
"cancellation_policy": "Free cancellation up to 24 hours before check-in",
"special_requirements": "Non-smoking rooms",
"external_booking_url": "https://grandhotel.com/booking/GH123456",
"created_by": current_user.id,
"created_at": datetime.utcnow(),
"updated_at": datetime.utcnow(),
)

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
                    (
                        "id": user_id,
"name": f"User(user_id)",
"email": f"user(user_id)@example.com",
)
)
mock_reservation["participants"] = participant_details
mock_reservation["participant_count"] = len(participant_details)

logger.info(f"Reservation(reservation_id) updated by user(current_user.id)")

return ReservationResponse(**mock_reservation)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error updating reservation(reservation_id): (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to update reservation",
)


@router.delete("/(reservation_id)", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reservation(
    reservation_id: int,
request: Request,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("reservations", "delete")
):
    """Cancel a reservation."""
try:
        # Mock reservation lookup
mock_reservation = {
            "id": reservation_id,
"trip_id": 1,
"created_by": current_user.id,
)

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
logger.info(f"Reservation(reservation_id) cancelled by user(current_user.id)")

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error cancelling reservation(reservation_id): (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to cancel reservation",
)


@router.post("/(reservation_id)/participants", response_model=ReservationResponse)
async def add_participants(
    reservation_id: int,
participant_ids: list[int],
request: Request,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("reservations", "update")
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
"contact_info": ("phone": "+1-555-0124", "email": "tours@citymuseum.com"),
"cost_per_person": 25.0,
"total_cost": 100.0,
"capacity": 20,
"participant_count": 2,
"participants": [
("id": 1, "name": "John Doe", "email": "john@example.com"),
("id": 2, "name": "Jane Smith", "email": "jane@example.com"),
],
"booking_reference": "CM789012",
"status": ReservationStatus.CONFIRMED,
"cancellation_policy": "Refund available up to 48 hours before tour",
"special_requirements": "Wheelchair accessible",
"external_booking_url": "https://citymuseum.com/tours/CM789012",
"created_by": current_user.id,
"created_at": datetime.utcnow(),
"updated_at": datetime.utcnow(),
)

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
                    (
                        "id": user_id,
"name": f"User(user_id)",
"email": f"user(user_id)@example.com",
)
)

mock_reservation["participant_count"] = len(mock_reservation["participants"])
mock_reservation["total_cost"] = (
            mock_reservation["participant_count"] * mock_reservation["cost_per_person"]
)
mock_reservation["updated_at"] = datetime.utcnow()

logger.info(f"Participants added to reservation(reservation_id) by user(current_user.id)")

return ReservationResponse(**mock_reservation)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error adding participants to reservation(reservation_id): (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to add participants",
)


@router.delete("/(reservation_id)/participants/(user_id)", response_model=ReservationResponse)
async def remove_participant(
    reservation_id: int,
user_id: int,
request: Request,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("reservations", "update")
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
"contact_info": ("phone": "+1-555-0124", "email": "tours@citymuseum.com"),
"cost_per_person": 25.0,
"total_cost": 150.0,
"capacity": 20,
"participant_count": 6,
"participants": [
("id": 1, "name": "John Doe", "email": "john@example.com"),
("id": 2, "name": "Jane Smith", "email": "jane@example.com"),
(
                    "id": user_id,
"name": f"User(user_id)",
"email": f"user(user_id)@example.com",
),
],
"booking_reference": "CM789012",
"status": ReservationStatus.CONFIRMED,
"cancellation_policy": "Refund available up to 48 hours before tour",
"special_requirements": "Wheelchair accessible",
"external_booking_url": "https://citymuseum.com/tours/CM789012",
"created_by": current_user.id,
"created_at": datetime.utcnow(),
"updated_at": datetime.utcnow(),
)

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
            f"Participant(user_id) removed from reservation(reservation_id) by user(current_user.id)"
)

return ReservationResponse(**mock_reservation)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error removing participant from reservation(reservation_id): (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to remove participant",
)
