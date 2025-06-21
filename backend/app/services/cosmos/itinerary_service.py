"""
Itinerary document service for Cosmos DB operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.cosmos_db import CosmosDBService
from app.models.cosmos.itinerary import (
    ItineraryActivityDocument,
    ItineraryDayDocument,
    ItineraryDocument,
)
from app.models.itinerary import ItineraryStatus

settings = get_settings()
logger = logging.getLogger(__name__)


class ItineraryDocumentService:
    """
    Service for managing itinerary documents in Cosmos DB.

    This service handles the document storage for itineraries,
    which allows for more flexible schema and versioning than SQL.
    """

    def __init__(self):
        """Initialize the Cosmos DB service with itinerary container."""
        self.cosmos_service = CosmosDBService[ItineraryDocument](
            container_name=settings.COSMOS_DB_CONTAINER_ITINERARIES,
            model_type=ItineraryDocument,
            partition_key="trip_id",
        )

    async def create_itinerary(self, itinerary: ItineraryDocument) -> ItineraryDocument:
        """Create a new itinerary document."""
        # Ensure we have an ID
        if not itinerary.id:
            itinerary.id = str(uuid.uuid4())

        # Set timestamps
        current_time = datetime.utcnow()
        itinerary.created_at = current_time
        itinerary.updated_at = current_time

        # Create the document in Cosmos DB
        result = await self.cosmos_service.create_item(itinerary)

        # Convert back to Pydantic model and return
        return ItineraryDocument(**result)

    async def get_itinerary(self, itinerary_id: str, trip_id: str) -> Optional[ItineraryDocument]:
        """Get an itinerary document by ID and trip ID."""
        return await self.cosmos_service.get_item(itinerary_id, trip_id)

    async def list_itineraries(self, trip_id: str) -> List[ItineraryDocument]:
        """List all itineraries for a trip."""
        query = "SELECT * FROM c WHERE c.trip_id = @trip_id"
        parameters = [{"name": "@trip_id", "value": trip_id}]

        return await self.cosmos_service.query_items(
            query=query, parameters=parameters, partition_key_value=trip_id
        )

    async def update_itinerary(self, itinerary: ItineraryDocument) -> ItineraryDocument:
        """Update an existing itinerary document."""
        # Update timestamp
        itinerary.updated_at = datetime.utcnow()

        # Replace the document in Cosmos DB
        result = await self.cosmos_service.replace_item(
            item_id=itinerary.id, item=itinerary, partition_key_value=itinerary.trip_id
        )

        # Convert back to Pydantic model and return
        return ItineraryDocument(**result)

    async def delete_itinerary(self, itinerary_id: str, trip_id: str) -> None:
        """Delete an itinerary document."""
        await self.cosmos_service.delete_item(itinerary_id, trip_id)

    async def create_itinerary_version(self, itinerary: ItineraryDocument) -> ItineraryDocument:
        """Create a new version of an itinerary document."""
        # First mark all existing versions as not current
        existing_itineraries = await self.list_itineraries(itinerary.trip_id)
        for existing in existing_itineraries:
            if existing.is_current and existing.id != itinerary.id:
                existing.is_current = False
                await self.update_itinerary(existing)

        # Create a new version with a new ID
        new_version = itinerary.model_copy(deep=True)
        new_version.id = str(uuid.uuid4())
        new_version.version = itinerary.version + 1
        new_version.is_current = True
        new_version.created_at = datetime.utcnow()
        new_version.updated_at = datetime.utcnow()

        # Create the new version in Cosmos DB
        return await self.create_itinerary(new_version)

    async def get_current_itinerary(self, trip_id: str) -> Optional[ItineraryDocument]:
        """Get the current (active) itinerary for a trip."""
        query = "SELECT * FROM c WHERE c.trip_id = @trip_id AND c.is_current = true"
        parameters = [{"name": "@trip_id", "value": trip_id}]

        results = await self.cosmos_service.query_items(
            query=query, parameters=parameters, partition_key_value=trip_id
        )

        return results[0] if results else None

    async def approve_itinerary(
        self, itinerary_id: str, trip_id: str, approver_id: str
    ) -> ItineraryDocument:
        """Approve an itinerary and mark it as finalized."""
        itinerary = await self.get_itinerary(itinerary_id, trip_id)
        if not itinerary:
            raise ValueError(f"Itinerary {itinerary_id} not found")

        itinerary.status = ItineraryStatus.APPROVED
        itinerary.approved_at = datetime.utcnow()
        itinerary.approved_by = approver_id

        return await self.update_itinerary(itinerary)

    async def add_user_feedback(
        self, itinerary_id: str, trip_id: str, user_id: str, feedback: Dict[str, Any]
    ) -> ItineraryDocument:
        """Add user feedback to an itinerary."""
        itinerary = await self.get_itinerary(itinerary_id, trip_id)
        if not itinerary:
            raise ValueError(f"Itinerary {itinerary_id} not found")

        # Initialize feedback list if needed
        if not itinerary.user_feedback:
            itinerary.user_feedback = []

        # Add new feedback with timestamp
        feedback_entry = {
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **feedback,
        }

        itinerary.user_feedback.append(feedback_entry)

        return await self.update_itinerary(itinerary)

    async def convert_from_sql(
        self, sql_itinerary: Any, include_days: bool = True
    ) -> ItineraryDocument:
        """
        Convert a SQLAlchemy itinerary model to a Cosmos DB document model.

        This method facilitates the hybrid database approach by allowing
        data to move between SQL and document databases.
        """
        # Create base itinerary document
        itinerary_doc = ItineraryDocument(
            id=str(sql_itinerary.id),
            trip_id=str(sql_itinerary.trip_id),
            name=sql_itinerary.name,
            description=sql_itinerary.description,
            status=sql_itinerary.status,
            generation_prompt=sql_itinerary.generation_prompt,
            ai_model_used=sql_itinerary.ai_model_used,
            generation_cost=sql_itinerary.generation_cost,
            generation_tokens=sql_itinerary.generation_tokens,
            created_at=sql_itinerary.created_at,
            updated_at=sql_itinerary.updated_at,
            approved_at=sql_itinerary.approved_at,
            approved_by=str(sql_itinerary.approved_by) if sql_itinerary.approved_by else None,
            days=[],
        )

        # Add days and activities if requested
        if include_days and sql_itinerary.days:
            for sql_day in sql_itinerary.days:
                day_doc = ItineraryDayDocument(
                    id=str(sql_day.id),
                    itinerary_id=str(sql_itinerary.id),
                    day_number=sql_day.day_number,
                    date=sql_day.date.isoformat() if sql_day.date else None,
                    title=sql_day.title,
                    description=sql_day.description,
                    estimated_cost=sql_day.estimated_cost,
                    driving_time_minutes=sql_day.driving_time_minutes,
                    driving_distance_km=sql_day.driving_distance_km,
                    created_at=sql_day.created_at,
                    updated_at=sql_day.updated_at,
                    activities=[],
                )

                # Add activities for this day
                if sql_day.activities:
                    for sql_activity in sql_day.activities:
                        activity_doc = ItineraryActivityDocument(
                            id=str(sql_activity.id),
                            day_id=str(sql_day.id),
                            sequence_order=sql_activity.sequence_order,
                            title=sql_activity.title,
                            description=sql_activity.description,
                            type=sql_activity.type,
                            difficulty=sql_activity.difficulty,
                            location_name=sql_activity.location_name,
                            address=sql_activity.address,
                            latitude=sql_activity.latitude,
                            longitude=sql_activity.longitude,
                            google_place_id=sql_activity.google_place_id,
                            start_time=(
                                sql_activity.start_time.isoformat()
                                if sql_activity.start_time
                                else None
                            ),
                            end_time=(
                                sql_activity.end_time.isoformat() if sql_activity.end_time else None
                            ),
                            duration_minutes=sql_activity.duration_minutes,
                            estimated_cost_per_person=sql_activity.estimated_cost_per_person,
                            booking_required=sql_activity.booking_required,
                            booking_url=sql_activity.booking_url,
                            booking_phone=sql_activity.booking_phone,
                            notes=sql_activity.notes,
                            website_url=sql_activity.website_url,
                            image_url=sql_activity.image_url,
                            is_optional=sql_activity.is_optional,
                            is_customized=sql_activity.is_customized,
                            created_at=sql_activity.created_at,
                            updated_at=sql_activity.updated_at,
                        )
                        day_doc.activities.append(activity_doc)

                itinerary_doc.days.append(day_doc)

        return itinerary_doc
