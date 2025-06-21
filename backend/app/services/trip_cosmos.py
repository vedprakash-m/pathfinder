"""
Trip hybrid database integrations for the TripService.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from app.models.cosmos.itinerary import ItineraryDocument
from app.models.cosmos.message import MessageDocument, MessageStatus, MessageType
from app.models.cosmos.preference import PreferenceType
from app.services.cosmos.itinerary_service import ItineraryDocumentService
from app.services.cosmos.message_service import MessageDocumentService
from app.services.cosmos.preference_service import PreferenceDocumentService

logger = logging.getLogger(__name__)


class TripCosmosOperations:
    """
    Mixin class for trip service that provides Cosmos DB operations.

    This class implements the hybrid database approach by providing methods
    that bridge between SQL models and Cosmos DB document models.
    """

    def __init__(self):
        """Initialize Cosmos DB service instances."""
        self.itinerary_service = ItineraryDocumentService()
        self.message_service = MessageDocumentService()
        self.preference_service = PreferenceDocumentService()

    async def save_trip_preferences_to_cosmos(
        self, trip_id: str, preferences: Dict[str, Any]
    ) -> bool:
        """
        Save trip preferences to Cosmos DB.

        This method allows storing rich, flexible preference data that might
        change structure over time, which is better suited for a document database.

        Args:
            trip_id: The ID of the trip
            preferences: Dictionary of preferences to store

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create or update preference document
            await self.preference_service.convert_from_model(
                entity_type=PreferenceType.TRIP,
                entity_id=trip_id,
                preferences_data=preferences,
            )
            return True
        except Exception as e:
            logger.error(
                f"Error saving trip preferences to Cosmos DB: {str(e)}")
            return False

    async def get_trip_preferences_from_cosmos(
        self, trip_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get trip preferences from Cosmos DB.

        Args:
            trip_id: The ID of the trip

        Returns:
            Dictionary of preferences if found, None otherwise
        """
        try:
            # Get latest preference document for this trip
            preference = await self.preference_service.get_latest_preference(
                entity_type=PreferenceType.TRIP, entity_id=trip_id
            )

            if preference:
                # Return the combined preferences
                return {
                    **preference.preferences,
                    "dietary_restrictions": preference.dietary_restrictions,
                    "accessibility_needs": preference.accessibility_needs,
                    "preferred_activities": preference.preferred_activities,
                    "accommodation_preferences": preference.accommodation_preferences,
                    "transportation_preferences": preference.transportation_preferences,
                }
            return None
        except Exception as e:
            logger.error(
                f"Error getting trip preferences from Cosmos DB: {str(e)}")
            return None

    async def send_trip_message(
        self,
        trip_id: str,
        sender_id: str,
        sender_name: str,
        text: str,
        message_type: MessageType = MessageType.CHAT,
        room_id: Optional[str] = None,
    ) -> Optional[MessageDocument]:
        """
        Send a message in a trip chat.

        Args:
            trip_id: The ID of the trip
            sender_id: The ID of the sender
            sender_name: The name of the sender
            text: The message text
            message_type: The type of message
            room_id: Optional room ID for focused discussions

        Returns:
            MessageDocument if sent successfully, None otherwise
        """
        try:
            # Create message document
            message = MessageDocument(
                id=str(UUID.uuid4()),
                trip_id=trip_id,
                sender_id=sender_id,
                sender_name=sender_name,
                type=message_type,
                text=text,
                status=MessageStatus.SENDING,
                room_id=room_id,
                created_at=datetime.utcnow(),
                read_by={},
            )

            # Create message in Cosmos DB
            result = await self.message_service.create_message(message)

            # Update status to sent
            await self.message_service.update_message_status(
                message_id=result.id, trip_id=trip_id, new_status=MessageStatus.SENT
            )

            return result
        except Exception as e:
            logger.error(f"Error sending trip message: {str(e)}")
            return None

    async def save_itinerary_to_cosmos(
        self, trip_id: str, sql_itinerary: Any
    ) -> Optional[ItineraryDocument]:
        """
        Save an itinerary from SQL to Cosmos DB.

        This method converts a SQL itinerary model to a document model
        and stores it in Cosmos DB for better versioning and flexible schema.

        Args:
            trip_id: The ID of the trip
            sql_itinerary: The SQL itinerary model instance

        Returns:
            ItineraryDocument if saved successfully, None otherwise
        """
        try:
            # Convert from SQL model to document model
            itinerary_doc = await self.itinerary_service.convert_from_sql(sql_itinerary)

            # Save to Cosmos DB
            return await self.itinerary_service.create_itinerary(itinerary_doc)
        except Exception as e:
            logger.error(f"Error saving itinerary to Cosmos DB: {str(e)}")
            return None

    async def get_trip_messages(
        self, trip_id: str, room_id: Optional[str] = None, limit: int = 50
    ) -> list:
        """
        Get messages for a trip.

        Args:
            trip_id: The ID of the trip
            room_id: Optional room ID to filter by
            limit: Maximum number of messages to return

        Returns:
            List of message documents
        """
        try:
            return await self.message_service.list_messages(
                trip_id=trip_id, room_id=room_id, limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting trip messages: {str(e)}")
            return []

    async def get_current_itinerary_from_cosmos(
        self, trip_id: str
    ) -> Optional[ItineraryDocument]:
        """
        Get the current itinerary for a trip from Cosmos DB.

        Args:
            trip_id: The ID of the trip

        Returns:
            ItineraryDocument if found, None otherwise
        """
        try:
            return await self.itinerary_service.get_current_itinerary(trip_id)
        except Exception as e:
            logger.error(
                f"Error getting current itinerary from Cosmos DB: {str(e)}")
            return None
