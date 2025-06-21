"""
Message document service for Cosmos DB operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import get_settings
from app.core.cosmos_db import CosmosDBService
from app.models.cosmos.message import MessageDocument, MessageStatus, MessageType

settings = get_settings()
logger = logging.getLogger(__name__)


class MessageDocumentService:
    """
    Service for managing message documents in Cosmos DB.

    This service provides functionality for real-time messaging capabilities
    with rich features like message status tracking, read receipts, and more.
    """

    def __init__(self):
        """Initialize the Cosmos DB service with message container."""
        self.cosmos_service = CosmosDBService[MessageDocument](
            container_name=settings.COSMOS_DB_CONTAINER_MESSAGES,
            model_type=MessageDocument,
            partition_key="trip_id",
        )

    async def create_message(self, message: MessageDocument) -> MessageDocument:
        """Create a new message document."""
        # Ensure we have an ID
        if not message.id:
            message.id = str(uuid.uuid4())

        # Set timestamp and initial status if not set
        message.created_at = datetime.utcnow()
        if not message.status:
            message.status = MessageStatus.SENDING

        # Create the document in Cosmos DB
        result = await self.cosmos_service.create_item(message)

        # Convert back to Pydantic model and return
        return MessageDocument(**result)

    async def get_message(self, message_id: str, trip_id: str) -> Optional[MessageDocument]:
        """Get a message document by ID and trip ID."""
        return await self.cosmos_service.get_item(message_id, trip_id)

    async def list_messages(
        self,
        trip_id: str,
        room_id: Optional[str] = None,
        limit: int = 50,
        before_timestamp: Optional[int] = None,
    ) -> List[MessageDocument]:
        """
        List messages for a trip, optionally filtered by room.

        Args:
            trip_id: The ID of the trip
            room_id: Optional room ID to filter by
            limit: Maximum number of messages to return
            before_timestamp: Optional timestamp to get messages before this time

        Returns:
            List of message documents
        """
        # Build the query
        if room_id:
            if before_timestamp:
                query = """
                    SELECT TOP @limit * FROM c 
                    WHERE c.trip_id = @trip_id 
                    AND c.room_id = @room_id 
                    AND c._ts < @before_timestamp
                    AND c.is_deleted = false
                    ORDER BY c._ts DESC
                """
                parameters = [
                    {"name": "@trip_id", "value": trip_id},
                    {"name": "@room_id", "value": room_id},
                    {"name": "@before_timestamp", "value": before_timestamp},
                    {"name": "@limit", "value": limit},
                ]
            else:
                query = """
                    SELECT TOP @limit * FROM c 
                    WHERE c.trip_id = @trip_id 
                    AND c.room_id = @room_id
                    AND c.is_deleted = false
                    ORDER BY c._ts DESC
                """
                parameters = [
                    {"name": "@trip_id", "value": trip_id},
                    {"name": "@room_id", "value": room_id},
                    {"name": "@limit", "value": limit},
                ]
        else:
            if before_timestamp:
                query = """
                    SELECT TOP @limit * FROM c 
                    WHERE c.trip_id = @trip_id 
                    AND c._ts < @before_timestamp
                    AND c.is_deleted = false
                    ORDER BY c._ts DESC
                """
                parameters = [
                    {"name": "@trip_id", "value": trip_id},
                    {"name": "@before_timestamp", "value": before_timestamp},
                    {"name": "@limit", "value": limit},
                ]
            else:
                query = """
                    SELECT TOP @limit * FROM c 
                    WHERE c.trip_id = @trip_id
                    AND c.is_deleted = false
                    ORDER BY c._ts DESC
                """
                parameters = [
                    {"name": "@trip_id", "value": trip_id},
                    {"name": "@limit", "value": limit},
                ]

        # Execute the query
        results = await self.cosmos_service.query_items(
            query=query, parameters=parameters, partition_key_value=trip_id
        )

        # Reverse to get chronological order
        results.reverse()
        return results

    async def update_message_status(
        self, message_id: str, trip_id: str, new_status: MessageStatus
    ) -> Optional[MessageDocument]:
        """Update the status of a message."""
        message = await self.get_message(message_id, trip_id)
        if not message:
            logger.warning(f"Message not found: {message_id}")
            return None

        message.status = new_status

        # Update the document in Cosmos DB
        result = await self.cosmos_service.replace_item(
            item_id=message_id, item=message, partition_key_value=trip_id
        )

        return MessageDocument(**result)

    async def mark_as_read(
        self, message_id: str, trip_id: str, user_id: str
    ) -> Optional[MessageDocument]:
        """Mark a message as read by a user."""
        message = await self.get_message(message_id, trip_id)
        if not message:
            logger.warning(f"Message not found: {message_id}")
            return None

        # Add read receipt
        read_time = datetime.utcnow()
        if not message.read_by:
            message.read_by = {}
        message.read_by[user_id] = read_time

        # Update the document in Cosmos DB
        result = await self.cosmos_service.replace_item(
            item_id=message_id, item=message, partition_key_value=trip_id
        )

        return MessageDocument(**result)

    async def edit_message(
        self, message_id: str, trip_id: str, new_text: str
    ) -> Optional[MessageDocument]:
        """Edit the text content of a message."""
        message = await self.get_message(message_id, trip_id)
        if not message:
            logger.warning(f"Message not found: {message_id}")
            return None

        message.text = new_text
        message.is_edited = True
        message.edited_at = datetime.utcnow()

        # Update the document in Cosmos DB
        result = await self.cosmos_service.replace_item(
            item_id=message_id, item=message, partition_key_value=trip_id
        )

        return MessageDocument(**result)

    async def delete_message(self, message_id: str, trip_id: str, soft_delete: bool = True) -> None:
        """
        Delete a message.

        Args:
            message_id: The ID of the message
            trip_id: The ID of the trip
            soft_delete: If True, mark the message as deleted but keep in database.
                         If False, permanently remove from database.
        """
        if soft_delete:
            # Soft delete - mark as deleted but keep in database
            message = await self.get_message(message_id, trip_id)
            if message:
                message.is_deleted = True
                message.deleted_at = datetime.utcnow()
                await self.cosmos_service.replace_item(
                    item_id=message_id, item=message, partition_key_value=trip_id
                )
        else:
            # Hard delete - completely remove from database
            await self.cosmos_service.delete_item(message_id, trip_id)

    async def create_system_message(
        self,
        trip_id: str,
        text: str,
        room_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> MessageDocument:
        """Create a system message for a trip."""
        # Create system message
        message = MessageDocument(
            id=str(uuid.uuid4()),
            trip_id=trip_id,
            sender_id="system",
            sender_name="System",
            type=MessageType.SYSTEM,
            text=text,
            status=MessageStatus.DELIVERED,
            room_id=room_id,
            created_at=datetime.utcnow(),
            data=data or {},
        )

        return await self.create_message(message)

    async def get_unread_count(
        self, trip_id: str, user_id: str, room_id: Optional[str] = None
    ) -> int:
        """Get the count of unread messages for a user."""
        # Build query to count messages not in the read_by map for this user
        if room_id:
            query = """
                SELECT VALUE COUNT(1) FROM c 
                WHERE c.trip_id = @trip_id 
                AND c.room_id = @room_id
                AND c.is_deleted = false
                AND (NOT IS_DEFINED(c.read_by) OR NOT IS_DEFINED(c.read_by[@user_id]))
            """
            parameters = [
                {"name": "@trip_id", "value": trip_id},
                {"name": "@room_id", "value": room_id},
                {"name": "@user_id", "value": user_id},
            ]
        else:
            query = """
                SELECT VALUE COUNT(1) FROM c 
                WHERE c.trip_id = @trip_id
                AND c.is_deleted = false
                AND (NOT IS_DEFINED(c.read_by) OR NOT IS_DEFINED(c.read_by[@user_id]))
            """
            parameters = [
                {"name": "@trip_id", "value": trip_id},
                {"name": "@user_id", "value": user_id},
            ]

        # Execute the query
        results = await self.cosmos_service.query_items(
            query=query, parameters=parameters, partition_key_value=trip_id
        )

        return results[0] if results else 0
