"""
WebSocket service for real-time trip collaboration.

This module handles WebSocket connections for real-time features like:
- Trip planning collaboration
- Live itinerary updates
- Real-time notifications
- User presence tracking
- Real-time messaging with Cosmos DB integration
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from app.models.cosmos.message import MessageType
from app.services.trip_cosmos import TripCosmosOperations
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time trip collaboration."""

    def __init__(self):
        # Active connections by trip_id
        self.trip_connections: Dict[str, Set[WebSocket]] = {}
        # User connections by user_id
        self.user_connections: Dict[str, WebSocket] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Cosmos service for messaging
        self.cosmos_ops = TripCosmosOperations()

    async def startup(self):
        """Initialize the connection manager."""
        logger.info("WebSocket connection manager starting up")

    async def shutdown(self):
        """Cleanup connections on shutdown."""
        logger.info("WebSocket connection manager shutting down")
        # Close all connections
        for websocket in list(self.connection_metadata.keys()):
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {e}")

        self.trip_connections.clear()
        self.user_connections.clear()
        self.connection_metadata.clear()

    async def connect(self, websocket: WebSocket, user_id: str, trip_id: Optional[str] = None):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "trip_id": trip_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }

        # Register user connection
        if user_id in self.user_connections:
            # Close existing connection for this user
            old_websocket = self.user_connections[user_id]
            try:
                await old_websocket.close()
            except Exception:
                pass

        self.user_connections[user_id] = websocket

        # Register trip connection if provided
        if trip_id:
            if trip_id not in self.trip_connections:
                self.trip_connections[trip_id] = set()
            self.trip_connections[trip_id].add(websocket)

        logger.info(f"WebSocket connected: user_id={user_id}, trip_id={trip_id}")

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection_established",
                "user_id": user_id,
                "trip_id": trip_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        # Notify trip members about user joining
        if trip_id:
            await self.broadcast_to_trip(
                {
                    "type": "user_joined",
                    "user_id": user_id,
                    "trip_id": trip_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                trip_id,
                exclude=websocket,
            )

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket not in self.connection_metadata:
            return

        metadata = self.connection_metadata[websocket]
        user_id = metadata.get("user_id")
        trip_id = metadata.get("trip_id")

        # Remove from trip connections
        if trip_id and trip_id in self.trip_connections:
            self.trip_connections[trip_id].discard(websocket)
            if not self.trip_connections[trip_id]:
                del self.trip_connections[trip_id]

        # Remove from user connections
        if user_id and user_id in self.user_connections:
            if self.user_connections[user_id] == websocket:
                del self.user_connections[user_id]

        # Remove metadata
        del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected: user_id={user_id}, trip_id={trip_id}")

        # Notify trip members about user leaving
        if trip_id:
            await self.broadcast_to_trip(
                {
                    "type": "user_left",
                    "user_id": user_id,
                    "trip_id": trip_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                trip_id,
            )

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))

            # Update last activity
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_activity"] = datetime.utcnow()

        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send a message to a specific user."""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            await self.send_personal_message(message, websocket)

    async def broadcast_to_trip(
        self, message: Dict[str, Any], trip_id: str, exclude: Optional[WebSocket] = None
    ):
        """Broadcast a message to all users connected to a trip."""
        if trip_id not in self.trip_connections:
            return

        message["trip_id"] = trip_id
        connections = self.trip_connections[trip_id].copy()

        for websocket in connections:
            if websocket != exclude:
                await self.send_personal_message(message, websocket)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected users."""
        for websocket in list(self.connection_metadata.keys()):
            await self.send_personal_message(message, websocket)

    async def join_trip(self, websocket: WebSocket, trip_id: str):
        """Join a trip channel for an existing connection."""
        if websocket not in self.connection_metadata:
            return

        # Update metadata
        self.connection_metadata[websocket]["trip_id"] = trip_id

        # Add to trip connections
        if trip_id not in self.trip_connections:
            self.trip_connections[trip_id] = set()
        self.trip_connections[trip_id].add(websocket)

        user_id = self.connection_metadata[websocket]["user_id"]

        logger.info(f"User {user_id} joined trip {trip_id}")

        # Notify trip members
        await self.broadcast_to_trip(
            {
                "type": "user_joined",
                "user_id": user_id,
                "trip_id": trip_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            trip_id,
            exclude=websocket,
        )

    async def leave_trip(self, websocket: WebSocket):
        """Leave current trip channel."""
        if websocket not in self.connection_metadata:
            return

        metadata = self.connection_metadata[websocket]
        trip_id = metadata.get("trip_id")
        user_id = metadata.get("user_id")

        if not trip_id:
            return

        # Remove from trip connections
        if trip_id in self.trip_connections:
            self.trip_connections[trip_id].discard(websocket)
            if not self.trip_connections[trip_id]:
                del self.trip_connections[trip_id]

        # Update metadata
        self.connection_metadata[websocket]["trip_id"] = None

        logger.info(f"User {user_id} left trip {trip_id}")

        # Notify trip members
        await self.broadcast_to_trip(
            {
                "type": "user_left",
                "user_id": user_id,
                "trip_id": trip_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
            trip_id,
        )

    def get_trip_users(self, trip_id: str) -> List[str]:
        """Get list of user IDs connected to a trip."""
        if trip_id not in self.trip_connections:
            return []

        users = []
        for websocket in self.trip_connections[trip_id]:
            if websocket in self.connection_metadata:
                user_id = self.connection_metadata[websocket]["user_id"]
                if user_id:
                    users.append(user_id)

        return users

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connection_metadata)

    def get_trip_connection_count(self, trip_id: str) -> int:
        """Get number of connections for a specific trip."""
        if trip_id not in self.trip_connections:
            return 0
        return len(self.trip_connections[trip_id])

    async def send_trip_message(
        self,
        websocket: WebSocket,
        text: str,
        message_type: MessageType = MessageType.CHAT,
        room_id: Optional[str] = None,
    ) -> bool:
        """
        Send a new message to a trip chat and store it in Cosmos DB.

        Args:
            websocket: The WebSocket connection of the sender
            text: The message text
            message_type: The type of message (default: chat)
            room_id: Optional room ID for focused discussions

        Returns:
            True if sent successfully, False otherwise
        """
        if websocket not in self.connection_metadata:
            return False

        metadata = self.connection_metadata[websocket]
        trip_id = metadata.get("trip_id")
        user_id = metadata.get("user_id")

        if not trip_id or not user_id:
            return False

        try:
            # Save message to Cosmos DB
            message = await self.cosmos_ops.send_trip_message(
                trip_id=trip_id,
                sender_id=user_id,
                sender_name=metadata.get("user_name", user_id),
                text=text,
                message_type=message_type,
                room_id=room_id,
            )

            if message:
                # Broadcast the message to all users in the trip
                await self.broadcast_to_trip(
                    {
                        "type": "new_message",
                        "message": message.dict(exclude={"_resource_id", "_etag", "_ts"}),
                        "trip_id": trip_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    trip_id,
                )

                return True
            return False
        except Exception as e:
            logger.error(f"Error sending trip message: {e}")
            return False

    async def get_trip_recent_messages(self, websocket: WebSocket, limit: int = 20) -> None:
        """
        Get and send recent messages for the current trip to a user.

        Args:
            websocket: The WebSocket connection requesting messages
            limit: Maximum number of messages to retrieve
        """
        if websocket not in self.connection_metadata:
            return

        metadata = self.connection_metadata[websocket]
        trip_id = metadata.get("trip_id")

        if not trip_id:
            return

        try:
            # Get messages from Cosmos DB
            messages = await self.cosmos_ops.get_trip_messages(trip_id=trip_id, limit=limit)

            if messages:
                # Send messages to the requesting client
                await self.send_personal_message(
                    {
                        "type": "message_history",
                        "messages": [
                            m.dict(exclude={"_resource_id", "_etag", "_ts"}) for m in messages
                        ],
                        "trip_id": trip_id,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    websocket,
                )
        except Exception as e:
            logger.error(f"Error getting trip messages: {e}")


# Global connection manager instance
websocket_manager = ConnectionManager()


# WebSocket message handlers
async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any], user_id: str):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")

    try:
        if message_type == "ping":
            await websocket_manager.send_personal_message(
                {"type": "pong", "timestamp": datetime.utcnow().isoformat()}, websocket
            )

        elif message_type == "join_trip":
            trip_id = message.get("trip_id")
            if trip_id:
                await websocket_manager.join_trip(websocket, trip_id)

        elif message_type == "leave_trip":
            await websocket_manager.leave_trip(websocket)

        elif message_type == "trip_update":
            # Handle trip updates (itinerary changes, etc.)
            trip_id = message.get("trip_id")
            if trip_id:
                await websocket_manager.broadcast_to_trip(
                    {
                        "type": "trip_updated",
                        "user_id": user_id,
                        "data": message.get("data", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    trip_id,
                    exclude=websocket,
                )

        elif message_type == "chat_message":
            # Handle chat messages with Cosmos DB integration
            text = message.get("text")
            room_id = message.get("room_id")
            msg_type = message.get("message_type", "chat")

            if text:
                await websocket_manager.send_trip_message(
                    websocket=websocket,
                    text=text,
                    message_type=MessageType(msg_type),
                    room_id=room_id,
                )

        elif message_type == "get_messages":
            # Handle message history requests
            limit = message.get("limit", 20)
            await websocket_manager.get_trip_recent_messages(websocket=websocket, limit=limit)

        elif message_type == "itinerary_update":
            # Handle itinerary updates
            trip_id = message.get("trip_id")
            if trip_id:
                await websocket_manager.broadcast_to_trip(
                    {
                        "type": "itinerary_updated",
                        "user_id": user_id,
                        "itinerary_id": message.get("itinerary_id"),
                        "data": message.get("data", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    trip_id,
                    exclude=websocket,
                )

        elif message_type == "typing":
            # Handle typing indicators
            trip_id = message.get("trip_id")
            if trip_id:
                await websocket_manager.broadcast_to_trip(
                    {
                        "type": "user_typing",
                        "user_id": user_id,
                        "component": message.get("component"),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    trip_id,
                    exclude=websocket,
                )

        elif message_type == "send_message":
            # Handle sending a message
            trip_id = message.get("trip_id")
            if trip_id:
                # Save message to Cosmos DB
                await websocket_manager.cosmos_ops.create_message(
                    {
                        "trip_id": trip_id,
                        "sender_id": user_id,
                        "content": message.get("content"),
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": MessageStatus.SENT,
                    }
                )

                # Broadcast message to trip members
                await websocket_manager.broadcast_to_trip(
                    {
                        "type": "new_message",
                        "user_id": user_id,
                        "trip_id": trip_id,
                        "content": message.get("content"),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    trip_id,
                )

        else:
            logger.warning(f"Unknown message type: {message_type}")

    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket_manager.send_personal_message(
            {
                "type": "error",
                "message": "Failed to process message",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )


# Notification helpers
async def notify_trip_update(trip_id: str, update_type: str, data: Dict[str, Any]):
    """Notify trip members about updates."""
    await websocket_manager.broadcast_to_trip(
        {
            "type": "trip_notification",
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        trip_id,
    )


async def notify_user(user_id: str, notification: Dict[str, Any]):
    """Send notification to a specific user."""
    notification["timestamp"] = datetime.utcnow().isoformat()
    await websocket_manager.send_to_user(notification, user_id)


async def notify_itinerary_update(
    trip_id: str, itinerary_id: str, update_type: str, data: Dict[str, Any]
):
    """Notify trip members about itinerary updates."""
    await websocket_manager.broadcast_to_trip(
        {
            "type": "itinerary_notification",
            "itinerary_id": itinerary_id,
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        trip_id,
    )


async def notify_poll_created(trip_id: str, poll_id: str, poll_data: Dict[str, Any]):
    """Notify trip members about new poll creation."""
    await websocket_manager.broadcast_to_trip(
        {
            "type": "poll_notification",
            "event": "poll_created",
            "poll_id": poll_id,
            "data": poll_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        trip_id,
    )


async def notify_poll_vote(trip_id: str, poll_id: str, voter_id: str, vote_data: Dict[str, Any]):
    """Notify trip members about a new vote on a poll."""
    await websocket_manager.broadcast_to_trip(
        {
            "type": "poll_notification",
            "event": "poll_vote",
            "poll_id": poll_id,
            "voter_id": voter_id,
            "data": vote_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        trip_id,
    )


async def notify_poll_results(trip_id: str, poll_id: str, results_data: Dict[str, Any]):
    """Notify trip members about poll results and AI analysis."""
    await websocket_manager.broadcast_to_trip(
        {
            "type": "poll_notification",
            "event": "poll_results",
            "poll_id": poll_id,
            "data": results_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        trip_id,
    )


async def notify_poll_completed(trip_id: str, poll_id: str, consensus_data: Dict[str, Any]):
    """Notify trip members about poll completion with consensus recommendation."""
    await websocket_manager.broadcast_to_trip(
        {
            "type": "poll_notification",
            "event": "poll_completed",
            "poll_id": poll_id,
            "data": consensus_data,
            "timestamp": datetime.utcnow().isoformat(),
        },
        trip_id,
    )
