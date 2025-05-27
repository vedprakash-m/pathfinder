"""
Enhanced real-time chat service for collaborative trip planning.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.core.telemetry import monitoring
from app.models.trip import Trip
from app.models.family import Family

logger = get_logger(__name__)


class MessageType(Enum):
    """Types of real-time messages."""
    CHAT = "chat"
    TYPING = "typing"
    ACTIVITY_UPDATE = "activity_update"
    ITINERARY_CHANGE = "itinerary_change"
    FAMILY_STATUS = "family_status"
    SYSTEM_NOTIFICATION = "system_notification"
    VOTE_REQUEST = "vote_request"
    VOTE_RESPONSE = "vote_response"
    USER_PRESENCE = "user_presence"


@dataclass
class ChatMessage:
    """Chat message data structure."""
    id: str
    trip_id: str
    user_id: str
    user_name: str
    family_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "family_id": self.family_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class UserPresence:
    """User presence information."""
    user_id: str
    user_name: str
    family_id: str
    status: str  # online, typing, away, offline
    last_activity: datetime
    current_page: Optional[str] = None


class TripChatRoom:
    """Manages real-time chat for a specific trip."""
    
    def __init__(self, trip_id: str):
        self.trip_id = trip_id
        self.connections: Dict[str, WebSocket] = {}  # user_id -> websocket
        self.user_presence: Dict[str, UserPresence] = {}  # user_id -> presence
        self.message_history: List[ChatMessage] = []
        self.active_votes: Dict[str, Dict[str, Any]] = {}  # vote_id -> vote_data
        self.typing_users: Set[str] = set()
        
    async def add_user(self, user_id: str, user_name: str, family_id: str, websocket: WebSocket):
        """Add a user to the chat room."""
        self.connections[user_id] = websocket
        self.user_presence[user_id] = UserPresence(
            user_id=user_id,
            user_name=user_name,
            family_id=family_id,
            status="online",
            last_activity=datetime.utcnow()
        )
        
        # Notify others of user joining
        await self.broadcast_presence_update(user_id, "joined")
        
        # Send recent message history to the new user
        await self.send_message_history(user_id)
        
        logger.info(f"User {user_name} joined trip chat {self.trip_id}")
    
    async def remove_user(self, user_id: str):
        """Remove a user from the chat room."""
        if user_id in self.connections:
            del self.connections[user_id]
        
        if user_id in self.user_presence:
            user_name = self.user_presence[user_id].user_name
            del self.user_presence[user_id]
            
            # Notify others of user leaving
            await self.broadcast_presence_update(user_id, "left", user_name)
            
            logger.info(f"User {user_name} left trip chat {self.trip_id}")
    
    async def broadcast_message(self, message: ChatMessage, exclude_user: Optional[str] = None):
        """Broadcast a message to all users in the room."""
        message_data = message.to_dict()
        
        # Store in message history
        self.message_history.append(message)
        
        # Keep only last 100 messages in memory
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        
        # Broadcast to all connected users
        disconnected_users = []
        for user_id, websocket in self.connections.items():
            if exclude_user and user_id == exclude_user:
                continue
                
            try:
                await websocket.send_text(json.dumps(message_data))
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.remove_user(user_id)
            
        # Track message for monitoring
        if monitoring:
            monitoring.track_custom_event("chat_message_sent", {
                "trip_id": self.trip_id,
                "message_type": message.message_type.value,
                "user_count": len(self.connections)
            })
    
    async def send_message_history(self, user_id: str):
        """Send recent message history to a specific user."""
        if user_id not in self.connections:
            return
            
        websocket = self.connections[user_id]
        
        # Send last 20 messages
        recent_messages = self.message_history[-20:] if self.message_history else []
        
        history_data = {
            "type": "message_history",
            "messages": [msg.to_dict() for msg in recent_messages]
        }
        
        try:
            await websocket.send_text(json.dumps(history_data))
        except Exception as e:
            logger.warning(f"Failed to send message history to user {user_id}: {e}")
    
    async def broadcast_presence_update(self, user_id: str, action: str, user_name: str = None):
        """Broadcast user presence updates."""
        if not user_name and user_id in self.user_presence:
            user_name = self.user_presence[user_id].user_name
        
        presence_data = {
            "type": "presence_update",
            "user_id": user_id,
            "user_name": user_name,
            "action": action,
            "online_users": [
                {
                    "user_id": p.user_id,
                    "user_name": p.user_name,
                    "family_id": p.family_id,
                    "status": p.status
                }
                for p in self.user_presence.values()
            ]
        }
        
        disconnected_users = []
        for uid, websocket in self.connections.items():
            try:
                await websocket.send_text(json.dumps(presence_data))
            except Exception as e:
                logger.warning(f"Failed to send presence update to user {uid}: {e}")
                disconnected_users.append(uid)
        
        # Clean up disconnected users
        for uid in disconnected_users:
            await self.remove_user(uid)
    
    async def handle_typing_indicator(self, user_id: str, is_typing: bool):
        """Handle typing indicators."""
        if is_typing:
            self.typing_users.add(user_id)
        else:
            self.typing_users.discard(user_id)
        
        user_name = self.user_presence.get(user_id, {}).user_name if user_id in self.user_presence else "Unknown"
        
        typing_data = {
            "type": "typing_indicator",
            "user_id": user_id,
            "user_name": user_name,
            "is_typing": is_typing,
            "typing_users": [
                {
                    "user_id": uid,
                    "user_name": self.user_presence.get(uid, {}).user_name or "Unknown"
                }
                for uid in self.typing_users
            ]
        }
        
        # Broadcast to all users except the typer
        disconnected_users = []
        for uid, websocket in self.connections.items():
            if uid == user_id:
                continue
                
            try:
                await websocket.send_text(json.dumps(typing_data))
            except Exception as e:
                logger.warning(f"Failed to send typing indicator to user {uid}: {e}")
                disconnected_users.append(uid)
        
        # Clean up disconnected users
        for uid in disconnected_users:
            await self.remove_user(uid)
    
    async def create_vote(self, creator_id: str, vote_data: Dict[str, Any]) -> str:
        """Create a new vote for the trip."""
        vote_id = str(uuid.uuid4())
        
        self.active_votes[vote_id] = {
            "id": vote_id,
            "creator_id": creator_id,
            "title": vote_data.get("title", ""),
            "description": vote_data.get("description", ""),
            "options": vote_data.get("options", []),
            "votes": {},  # user_id -> option_index
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "status": "active"
        }
        
        # Broadcast vote to all users
        vote_message = ChatMessage(
            id=str(uuid.uuid4()),
            trip_id=self.trip_id,
            user_id=creator_id,
            user_name=self.user_presence.get(creator_id, {}).user_name or "Unknown",
            family_id=self.user_presence.get(creator_id, {}).family_id or "",
            message_type=MessageType.VOTE_REQUEST,
            content=f"New vote: {vote_data.get('title', 'Untitled')}",
            timestamp=datetime.utcnow(),
            metadata={"vote_id": vote_id, "vote_data": self.active_votes[vote_id]}
        )
        
        await self.broadcast_message(vote_message)
        
        return vote_id
    
    async def cast_vote(self, user_id: str, vote_id: str, option_index: int):
        """Cast a vote for a user."""
        if vote_id not in self.active_votes:
            return False
        
        vote = self.active_votes[vote_id]
        if vote["status"] != "active":
            return False
        
        vote["votes"][user_id] = option_index
        
        # Broadcast vote update
        vote_message = ChatMessage(
            id=str(uuid.uuid4()),
            trip_id=self.trip_id,
            user_id=user_id,
            user_name=self.user_presence.get(user_id, {}).user_name or "Unknown",
            family_id=self.user_presence.get(user_id, {}).family_id or "",
            message_type=MessageType.VOTE_RESPONSE,
            content=f"Voted on: {vote['title']}",
            timestamp=datetime.utcnow(),
            metadata={"vote_id": vote_id, "option_index": option_index, "vote_summary": self._get_vote_summary(vote_id)}
        )
        
        await self.broadcast_message(vote_message)
        
        return True
    
    def _get_vote_summary(self, vote_id: str) -> Dict[str, Any]:
        """Get vote summary with current results."""
        if vote_id not in self.active_votes:
            return {}
        
        vote = self.active_votes[vote_id]
        options = vote["options"]
        votes = vote["votes"]
        
        # Count votes for each option
        vote_counts = [0] * len(options)
        for option_index in votes.values():
            if 0 <= option_index < len(vote_counts):
                vote_counts[option_index] += 1
        
        return {
            "vote_id": vote_id,
            "title": vote["title"],
            "options": options,
            "vote_counts": vote_counts,
            "total_votes": len(votes),
            "participants": list(votes.keys())
        }


class EnhancedChatService:
    """Enhanced chat service for managing multiple trip chat rooms."""
    
    def __init__(self):
        self.chat_rooms: Dict[str, TripChatRoom] = {}  # trip_id -> TripChatRoom
        
    def get_or_create_room(self, trip_id: str) -> TripChatRoom:
        """Get or create a chat room for a trip."""
        if trip_id not in self.chat_rooms:
            self.chat_rooms[trip_id] = TripChatRoom(trip_id)
        return self.chat_rooms[trip_id]
    
    async def add_user_to_trip(self, trip_id: str, user_id: str, user_name: str, family_id: str, websocket: WebSocket):
        """Add a user to a trip's chat room."""
        room = self.get_or_create_room(trip_id)
        await room.add_user(user_id, user_name, family_id, websocket)
    
    async def remove_user_from_trip(self, trip_id: str, user_id: str):
        """Remove a user from a trip's chat room."""
        if trip_id in self.chat_rooms:
            await self.chat_rooms[trip_id].remove_user(user_id)
            
            # Clean up empty rooms
            if not self.chat_rooms[trip_id].connections:
                del self.chat_rooms[trip_id]
    
    async def send_message_to_trip(self, trip_id: str, user_id: str, message_type: MessageType, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Send a message to a trip's chat room."""
        if trip_id not in self.chat_rooms:
            return False
        
        room = self.chat_rooms[trip_id]
        if user_id not in room.user_presence:
            return False
        
        user_presence = room.user_presence[user_id]
        
        message = ChatMessage(
            id=str(uuid.uuid4()),
            trip_id=trip_id,
            user_id=user_id,
            user_name=user_presence.user_name,
            family_id=user_presence.family_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        await room.broadcast_message(message)
        return True
    
    async def handle_typing_indicator(self, trip_id: str, user_id: str, is_typing: bool):
        """Handle typing indicators for a trip."""
        if trip_id in self.chat_rooms:
            await self.chat_rooms[trip_id].handle_typing_indicator(user_id, is_typing)
    
    async def create_vote(self, trip_id: str, user_id: str, vote_data: Dict[str, Any]) -> Optional[str]:
        """Create a vote in a trip's chat room."""
        if trip_id in self.chat_rooms:
            return await self.chat_rooms[trip_id].create_vote(user_id, vote_data)
        return None
    
    async def cast_vote(self, trip_id: str, user_id: str, vote_id: str, option_index: int) -> bool:
        """Cast a vote in a trip's chat room."""
        if trip_id in self.chat_rooms:
            return await self.chat_rooms[trip_id].cast_vote(user_id, vote_id, option_index)
        return False
    
    def get_room_stats(self) -> Dict[str, Any]:
        """Get statistics about all chat rooms."""
        return {
            "total_rooms": len(self.chat_rooms),
            "total_connections": sum(len(room.connections) for room in self.chat_rooms.values()),
            "rooms": {
                trip_id: {
                    "user_count": len(room.connections),
                    "message_count": len(room.message_history),
                    "active_votes": len(room.active_votes)
                }
                for trip_id, room in self.chat_rooms.items()
            }
        }


# Global chat service instance
enhanced_chat_service = EnhancedChatService()
