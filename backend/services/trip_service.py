"""
Trip Service

Business logic for trip management operations.
"""

import logging
from typing import Optional

from models.documents import TripDocument, UserDocument
from models.schemas import TripCreate, TripUpdate
from repositories.cosmos_repository import cosmos_repo

logger = logging.getLogger(__name__)


# Service singleton
_trip_service: Optional["TripService"] = None


def get_trip_service() -> "TripService":
    """Get or create trip service singleton."""
    global _trip_service
    if _trip_service is None:
        _trip_service = TripService()
    return _trip_service


class TripService:
    """Service for trip-related operations."""

    async def create_trip(self, data: TripCreate, user: UserDocument) -> TripDocument:
        """
        Create a new trip.

        Args:
            data: Trip creation data
            user: Authenticated user creating the trip

        Returns:
            Created trip document
        """
        trip = TripDocument(
            pk=f"trip_{user.id}",
            title=data.title,
            description=data.description,
            destination=data.destination,
            start_date=data.start_date,
            end_date=data.end_date,
            budget=data.budget,
            currency=data.currency,
            organizer_user_id=user.id,
            participating_family_ids=data.participating_family_ids or user.family_ids[:1],
            status="planning",
        )

        created = await cosmos_repo.create(trip)
        logger.info(f"Created trip '{created.title}' by user {user.id}")

        return created

    async def get_trip(self, trip_id: str) -> TripDocument | None:
        """
        Get a trip by ID.

        Args:
            trip_id: Trip ID

        Returns:
            Trip document if found
        """
        # Query by ID across partitions
        query = "SELECT * FROM c WHERE c.entity_type = 'trip' AND c.id = @tripId"
        trips = await cosmos_repo.query(
            query=query, parameters=[{"name": "@tripId", "value": trip_id}], model_class=TripDocument, max_items=1
        )

        return trips[0] if trips else None

    async def get_user_trips(self, user_id: str, status: str | None = None, limit: int = 50) -> list[TripDocument]:
        """
        Get all trips for a user (as organizer or participant).

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum trips to return

        Returns:
            List of trip documents
        """
        # Get trips where user is organizer
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'trip'
            AND c.organizer_user_id = @userId
        """
        params = [{"name": "@userId", "value": user_id}]

        if status:
            query += " AND c.status = @status"
            params.append({"name": "@status", "value": status})

        query += " ORDER BY c.created_at DESC"

        trips = await cosmos_repo.query(query=query, parameters=params, model_class=TripDocument, max_items=limit)

        return trips

    async def get_family_trips(self, family_id: str, status: str | None = None, limit: int = 50) -> list[TripDocument]:
        """
        Get all trips for a family.

        Args:
            family_id: Family ID
            status: Optional status filter
            limit: Maximum trips to return

        Returns:
            List of trip documents
        """
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'trip'
            AND ARRAY_CONTAINS(c.participating_family_ids, @familyId)
        """
        params = [{"name": "@familyId", "value": family_id}]

        if status:
            query += " AND c.status = @status"
            params.append({"name": "@status", "value": status})

        query += " ORDER BY c.created_at DESC"

        return await cosmos_repo.query(query=query, parameters=params, model_class=TripDocument, max_items=limit)

    async def update_trip(self, trip_id: str, data: TripUpdate, user: UserDocument) -> TripDocument | None:
        """
        Update a trip.

        Args:
            trip_id: Trip ID
            data: Update data
            user: Authenticated user

        Returns:
            Updated trip or None if not found/unauthorized
        """
        trip = await self.get_trip(trip_id)

        if not trip:
            return None

        if not self.user_has_access(trip, user.id):
            logger.warning(f"User {user.id} denied access to trip {trip_id}")
            return None

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(trip, field) and value is not None:
                setattr(trip, field, value)

        updated = await cosmos_repo.update(trip)
        logger.info(f"Updated trip {trip_id} by user {user.id}")

        return updated

    async def delete_trip(self, trip_id: str, user: UserDocument) -> bool:
        """
        Delete a trip.

        Args:
            trip_id: Trip ID
            user: Authenticated user

        Returns:
            True if deleted, False otherwise
        """
        trip = await self.get_trip(trip_id)

        if not trip:
            return False

        # Only organizer can delete
        if trip.organizer_user_id != user.id:
            logger.warning(f"User {user.id} cannot delete trip {trip_id}")
            return False

        deleted = await cosmos_repo.delete(trip_id, trip.pk)

        if deleted:
            logger.info(f"Deleted trip {trip_id} by user {user.id}")

        return deleted

    def user_has_access(self, trip: TripDocument, user_id: str) -> bool:
        """
        Check if user has access to a trip.

        Args:
            trip: Trip document
            user_id: User ID to check

        Returns:
            True if user has access
        """
        # Organizer always has access
        if trip.organizer_user_id == user_id:
            return True

        # TODO: Check if user is in any participating family
        # For now, return True for simplicity
        return True

    async def add_family_to_trip(self, trip_id: str, family_id: str, user: UserDocument) -> TripDocument | None:
        """
        Add a family to a trip.

        Args:
            trip_id: Trip ID
            family_id: Family ID to add
            user: Authenticated user

        Returns:
            Updated trip or None
        """
        trip = await self.get_trip(trip_id)

        if not trip or trip.organizer_user_id != user.id:
            return None

        if family_id not in trip.participating_family_ids:
            trip.participating_family_ids.append(family_id)
            return await cosmos_repo.update(trip)

        return trip

    async def remove_family_from_trip(self, trip_id: str, family_id: str, user: UserDocument) -> TripDocument | None:
        """
        Remove a family from a trip.

        Args:
            trip_id: Trip ID
            family_id: Family ID to remove
            user: Authenticated user

        Returns:
            Updated trip or None
        """
        trip = await self.get_trip(trip_id)

        if not trip or trip.organizer_user_id != user.id:
            return None

        if family_id in trip.participating_family_ids:
            trip.participating_family_ids.remove(family_id)
            return await cosmos_repo.update(trip)

        return trip

    async def update_trip_status(self, trip_id: str, status: str, user: UserDocument) -> TripDocument | None:
        """
        Update trip status.

        Args:
            trip_id: Trip ID
            status: New status
            user: Authenticated user

        Returns:
            Updated trip or None
        """
        valid_statuses = ["planning", "voting", "confirmed", "in_progress", "completed", "cancelled"]

        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")

        trip = await self.get_trip(trip_id)

        if not trip or not self.user_has_access(trip, user.id):
            return None

        trip.status = status
        return await cosmos_repo.update(trip)
