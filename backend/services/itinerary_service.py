"""
Itinerary Service

Business logic for AI-powered itinerary generation and management.
"""

import logging
from typing import Any, Optional

from models.documents import ItineraryDocument, TripDocument, UserDocument
from repositories.cosmos_repository import cosmos_repo
from services.llm.client import llm_client
from services.llm.prompts import ITINERARY_SYSTEM_PROMPT, build_itinerary_prompt

logger = logging.getLogger(__name__)


# Service singleton
_itinerary_service: Optional["ItineraryService"] = None


def get_itinerary_service() -> "ItineraryService":
    """Get or create itinerary service singleton."""
    global _itinerary_service
    if _itinerary_service is None:
        _itinerary_service = ItineraryService()
    return _itinerary_service


class ItineraryService:
    """Service for itinerary-related operations."""

    async def generate_itinerary(
        self, trip_id: str, preferences: dict[str, Any] | None = None, user: UserDocument | None = None
    ) -> ItineraryDocument | None:
        """
        Generate an AI-powered itinerary for a trip.

        Args:
            trip_id: Trip ID
            preferences: Optional generation preferences
            user: Optional user for context

        Returns:
            Generated itinerary document
        """
        # Get trip details
        trip = await self._get_trip(trip_id)
        if not trip:
            logger.error(f"Trip not found: {trip_id}")
            return None

        # Build prompt
        prompt = build_itinerary_prompt(trip, preferences)

        try:
            # Generate itinerary using LLM
            response = await llm_client.complete(
                prompt=prompt, system_prompt=ITINERARY_SYSTEM_PROMPT, max_tokens=3000, temperature=0.7
            )

            # Parse response into itinerary structure
            itinerary_data = self._parse_itinerary_response(response["content"])

            # Get next version number
            version = await self._get_next_version(trip_id)

            # Create itinerary document
            itinerary = ItineraryDocument(
                pk=f"itinerary_{trip_id}",
                trip_id=trip_id,
                version_number=version,
                title=f"Itinerary v{version} - {trip.destination or 'Trip'}",
                summary=itinerary_data.get("summary"),
                days=itinerary_data.get("days", []),
                status="draft",
                generated_by="ai",
                generation_params=preferences,
                ai_tokens_used=response.get("tokens_used", 0),
                ai_cost_usd=response.get("cost", 0.0),
            )

            created = await cosmos_repo.create(itinerary)
            logger.info(f"Generated itinerary for trip {trip_id}, version {version}")

            return created

        except Exception as e:
            logger.exception(f"Failed to generate itinerary: {e}")
            raise

    async def get_itinerary(self, itinerary_id: str) -> ItineraryDocument | None:
        """
        Get an itinerary by ID.

        Args:
            itinerary_id: Itinerary ID

        Returns:
            Itinerary document if found
        """
        query = "SELECT * FROM c WHERE c.entity_type = 'itinerary' AND c.id = @id"
        itineraries = await cosmos_repo.query(
            query=query, parameters=[{"name": "@id", "value": itinerary_id}], model_class=ItineraryDocument, max_items=1
        )

        return itineraries[0] if itineraries else None

    async def get_trip_itineraries(self, trip_id: str, limit: int = 10) -> list[ItineraryDocument]:
        """
        Get all itineraries for a trip.

        Args:
            trip_id: Trip ID
            limit: Maximum itineraries to return

        Returns:
            List of itinerary documents, newest first
        """
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'itinerary'
            AND c.trip_id = @tripId
            ORDER BY c.version_number DESC
        """

        return await cosmos_repo.query(
            query=query,
            parameters=[{"name": "@tripId", "value": trip_id}],
            model_class=ItineraryDocument,
            max_items=limit,
        )

    async def get_current_itinerary(self, trip_id: str) -> ItineraryDocument | None:
        """
        Get the current (approved or latest) itinerary for a trip.

        Args:
            trip_id: Trip ID

        Returns:
            Current itinerary if exists
        """
        # First try to find an approved itinerary
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'itinerary'
            AND c.trip_id = @tripId
            AND c.status = 'approved'
            ORDER BY c.version_number DESC
        """

        approved = await cosmos_repo.query(
            query=query, parameters=[{"name": "@tripId", "value": trip_id}], model_class=ItineraryDocument, max_items=1
        )

        if approved:
            return approved[0]

        # Fall back to latest
        itineraries = await self.get_trip_itineraries(trip_id, limit=1)
        return itineraries[0] if itineraries else None

    async def approve_itinerary(self, itinerary_id: str, user: UserDocument) -> ItineraryDocument | None:
        """
        Approve an itinerary.

        Args:
            itinerary_id: Itinerary ID
            user: Approving user

        Returns:
            Updated itinerary
        """
        itinerary = await self.get_itinerary(itinerary_id)

        if not itinerary:
            return None

        # Add user to approved_by list
        if itinerary.approved_by is None:
            itinerary.approved_by = []

        if user.id not in itinerary.approved_by:
            itinerary.approved_by.append(user.id)

        # Mark as approved if enough approvals (simplified: any approval works)
        itinerary.status = "approved"

        return await cosmos_repo.update(itinerary)

    async def update_itinerary(
        self, itinerary_id: str, updates: dict[str, Any], user: UserDocument
    ) -> ItineraryDocument | None:
        """
        Update an itinerary.

        Args:
            itinerary_id: Itinerary ID
            updates: Fields to update
            user: User making updates

        Returns:
            Updated itinerary
        """
        itinerary = await self.get_itinerary(itinerary_id)

        if not itinerary:
            return None

        # Apply updates
        allowed_fields = {"title", "summary", "days", "status"}
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(itinerary, field, value)

        # Reset generated_by to user if manually edited
        itinerary.generated_by = f"user:{user.id}"

        return await cosmos_repo.update(itinerary)

    async def delete_itinerary(self, itinerary_id: str, user: UserDocument) -> bool:
        """
        Delete an itinerary.

        Args:
            itinerary_id: Itinerary ID
            user: User requesting deletion

        Returns:
            True if deleted
        """
        itinerary = await self.get_itinerary(itinerary_id)

        if not itinerary:
            return False

        return await cosmos_repo.delete(itinerary_id, itinerary.pk)

    async def _get_trip(self, trip_id: str) -> TripDocument | None:
        """Get trip by ID."""
        query = "SELECT * FROM c WHERE c.entity_type = 'trip' AND c.id = @id"
        trips = await cosmos_repo.query(
            query=query, parameters=[{"name": "@id", "value": trip_id}], model_class=TripDocument, max_items=1
        )
        return trips[0] if trips else None

    async def _get_next_version(self, trip_id: str) -> int:
        """Get next version number for a trip's itinerary."""
        query = """
            SELECT VALUE MAX(c.version_number) FROM c
            WHERE c.entity_type = 'itinerary'
            AND c.trip_id = @tripId
        """
        result = await cosmos_repo.query(query=query, parameters=[{"name": "@tripId", "value": trip_id}])

        current_max = result[0] if result and result[0] else 0
        return current_max + 1

    def _parse_itinerary_response(self, content: str) -> dict[str, Any]:
        """
        Parse LLM response into structured itinerary data.

        Args:
            content: Raw LLM response

        Returns:
            Parsed itinerary structure
        """
        import json

        # Try to parse as JSON first
        try:
            # Find JSON block in response
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
            elif "{" in content:
                # Try to extract JSON object
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                json_str = content

            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fall back to simple parsing
            logger.warning("Could not parse itinerary as JSON, using fallback")
            return {
                "summary": content[:500],
                "days": [{"day_number": 1, "title": "Day 1", "activities": [{"description": content}]}],
            }
