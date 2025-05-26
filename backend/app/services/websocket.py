"""
WebSocket service for real-time trip collaboration.

This module handles WebSocket connections for real-time features like:
- Trip planning collaboration
- Live itinerary updates
- Real-time notifications
- User presence tracking
"""

import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import settings

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
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: str, 
        trip_id: Optional[str] = None
    ):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "trip_id": trip_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
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
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "trip_id": trip_id,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        # Notify trip members about user joining
        if trip_id:
            await self.broadcast_to_trip({
                "type": "user_joined",
                "user_id": user_id,
                "trip_id": trip_id,
                "timestamp": datetime.utcnow().isoformat()
            }, trip_id, exclude=websocket)
    
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
            await self.broadcast_to_trip({
                "type": "user_left",
                "user_id": user_id,
                "trip_id": trip_id,
                "timestamp": datetime.utcnow().isoformat()
            }, trip_id)
    
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
        self, 
        message: Dict[str, Any], 
        trip_id: str, 
        exclude: Optional[WebSocket] = None
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
        await self.broadcast_to_trip({
            "type": "user_joined",
            "user_id": user_id,
            "trip_id": trip_id,
            "timestamp": datetime.utcnow().isoformat()
        }, trip_id, exclude=websocket)
    
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
        await self.broadcast_to_trip({
            "type": "user_left",
            "user_id": user_id,
            "trip_id": trip_id,
            "timestamp": datetime.utcnow().isoformat()
        }, trip_id)
    
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


# Global connection manager instance
websocket_manager = ConnectionManager()


# WebSocket message handlers
async def handle_websocket_message(
    websocket: WebSocket, 
    message: Dict[str, Any], 
    user_id: str
):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    try:
        if message_type == "ping":
            await websocket_manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
        
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
                await websocket_manager.broadcast_to_trip({
                    "type": "trip_updated",
                    "user_id": user_id,
                    "data": message.get("data", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }, trip_id, exclude=websocket)
        
        elif message_type == "itinerary_update":
            # Handle itinerary updates
            trip_id = message.get("trip_id")
            if trip_id:
                await websocket_manager.broadcast_to_trip({
                    "type": "itinerary_updated",
                    "user_id": user_id,
                    "itinerary_id": message.get("itinerary_id"),
                    "data": message.get("data", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }, trip_id, exclude=websocket)
        
        elif message_type == "typing":
            # Handle typing indicators
            trip_id = message.get("trip_id")
            if trip_id:
                await websocket_manager.broadcast_to_trip({
                    "type": "user_typing",
                    "user_id": user_id,
                    "component": message.get("component"),
                    "timestamp": datetime.utcnow().isoformat()
                }, trip_id, exclude=websocket)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket_manager.send_personal_message({
            "type": "error",
            "message": "Failed to process message",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)


# Notification helpers
async def notify_trip_update(trip_id: str, update_type: str, data: Dict[str, Any]):
    """Notify trip members about updates."""
    await websocket_manager.broadcast_to_trip({
        "type": "trip_notification",
        "update_type": update_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }, trip_id)


async def notify_user(user_id: str, notification: Dict[str, Any]):
    """Send notification to a specific user."""
    notification["timestamp"] = datetime.utcnow().isoformat()
    await websocket_manager.send_to_user(notification, user_id)


async def notify_itinerary_update(
    trip_id: str, 
    itinerary_id: str, 
    update_type: str, 
    data: Dict[str, Any]
):
    """Notify trip members about itinerary updates."""
    await websocket_manager.broadcast_to_trip({
        "type": "itinerary_notification",
        "itinerary_id": itinerary_id,
        "update_type": update_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }, trip_id)
