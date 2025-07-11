from __future__ import annotations

"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
WebSocket API endpoints for real-time communication.
Provides WebSocket connections for real-time trip collaboration.
"""

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from app.core.container import Container
from app.core.database_unified import get_cosmos_repository
from app.core.security import get_current_user, get_current_user_websocket

# SQL User model removed - use Cosmos UserDocument
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.services.websocket import handle_websocket_message, websocket_manager
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/trip/{trip_id}")
async def websocket_trip_endpoint(
    websocket: WebSocket,
    trip_id: UUID,
    token: str = Query(..., description="Authentication token"),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """
    WebSocket endpoint for real-time trip collaboration.

        Args:
            websocket: WebSocket connection
            trip_id: Trip ID to connect to
            token: Authentication token
            cosmos_repo: Unified Cosmos DB repository
    """
    trip_service = Container().trip_domain_service()
    try:
        # Authenticate user from token
        user = await get_current_user_websocket(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # Check if user has access to the trip
        trip = await trip_service.get_trip_by_id(trip_id, user.id)
        if not trip:
            await websocket.close(code=4003, reason="Trip not found or access denied")
            return

        # Accept connection
        await websocket.accept()

        # Connect to WebSocket manager with trip context
        user_name = user.name or user.email.split("@")[0]
        await websocket_manager.connect(websocket, str(user.id), str(trip_id))

        # Set additional metadata
        if websocket in websocket_manager.connection_metadata:
            websocket_manager.connection_metadata[websocket]["user_name"] = user_name

        # Send recent messages from Cosmos DB
        await websocket_manager.get_trip_recent_messages(websocket)

        # WebSocket message loop
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Process the message using the global message handler
                await handle_websocket_message(websocket, message_data, user.id)

        except WebSocketDisconnect:
            # Handle disconnection
            await websocket_manager.disconnect(websocket)
            logger.info(f"User {user.id} disconnected from trip {trip_id}")

        except json.JSONDecodeError:
            # Handle invalid JSON
            error_message = {
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(error_message))

        except Exception as e:
            # Handle other errors
            logger.error(f"WebSocket error for user {user.id} in trip {trip_id}: {e}")
            error_message = {
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(error_message))

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Internal server error")


@router.websocket("/notifications")
async def websocket_notifications_endpoint(
    websocket: WebSocket, token: str = Query(..., description="Authentication token")
):
    """WebSocket endpoint for real-time notifications."""
    try:
        # Authenticate user from token
        user = await get_current_user_websocket(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # Accept the connection
        await websocket.accept()

        # Add connection to notifications room
        _notifications_room = f"notifications_{user.id}"
        await websocket_manager.connect(websocket, user.id, None)

        # Send welcome message
        welcome_message = {
            "type": "notifications_connected",
            "message": "Connected to notifications",
            "user_id": str(user.id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send_text(json.dumps(welcome_message))

        # Listen for messages (mainly for keep-alive)
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Handle keep-alive or other notification-related messages
                if message_data.get("type") == "ping":
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await websocket.send_text(json.dumps(pong_message))

        except WebSocketDisconnect:
            # Handle disconnection
            await websocket_manager.disconnect(websocket)
            logger.info(f"User {user.id} disconnected from notifications")

        except json.JSONDecodeError:
            # Handle invalid JSON
            error_message = {
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(error_message))

        except Exception as e:
            # Handle other errors
            logger.error(f"Notifications WebSocket error for user {user.id}: {e}")
            error_message = {
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(error_message))

    except Exception as e:
        logger.error(f"Notifications WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Internal server error")


# Additional utility endpoints for WebSocket management


@router.get("/connections/trip/{trip_id}")
async def get_trip_connections(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get active connections for a trip using unified Cosmos DB."""
    trip_service = Container().trip_domain_service()
    try:
        # Check if user has access to the trip
        trip = await trip_service.get_trip_by_id(trip_id, current_user.id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Get connection info using the correct method
        connected_users = websocket_manager.get_trip_users(str(trip_id))
        connection_count = websocket_manager.get_trip_connection_count(str(trip_id))

        return {
            "trip_id": str(trip_id),
            "active_connections": connection_count,
            "connected_users": connected_users,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trip connections: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving connection information"
        )


@router.post("/broadcast/trip/{trip_id}")
async def broadcast_to_trip(
    trip_id: UUID,
    message: dict,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Broadcast a message to all users in a trip using unified Cosmos DB."""
    trip_service = Container().trip_domain_service()
    try:
        # Check if user has access to the trip
        trip = await trip_service.get_trip_by_id(trip_id, current_user.id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Add sender information to message
        broadcast_message = {
            **message,
            "sender_id": str(current_user.id),
            "sender_name": current_user.name,
            "trip_id": str(trip_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Broadcast to all connections in the trip room
        await websocket_manager.broadcast_to_trip(broadcast_message, str(trip_id))

        return {
            "success": True,
            "message": "Message broadcasted successfully",
            "trip_id": str(trip_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting to trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="Error broadcasting message")
