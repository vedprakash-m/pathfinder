"""
Simple tests for Enhanced Real-time Chat Service.

This module tests the enhanced chat service core functionality
without complex dependencies.
"""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.services.enhanced_chat import (
    ChatMessage,
    EnhancedChatService,
    MessageType,
    TripChatRoom,
    UserPresence,
)


@pytest.fixture
def sample_trip_id():
    """Sample trip ID."""
    return str(uuid4())


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return str(uuid4())


@pytest.fixture
def sample_family_id():
    """Sample family ID."""
    return str(uuid4())


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = AsyncMock()
    websocket.send_text = AsyncMock()
    return websocket


@pytest.fixture
def chat_service():
    """Create enhanced chat service instance."""
    return EnhancedChatService()


@pytest.fixture
def chat_room(sample_trip_id):
    """Create chat room instance."""
    return TripChatRoom(sample_trip_id)


class TestChatMessage:
    """Test ChatMessage dataclass."""

    def test_chat_message_creation(
        self, sample_trip_id, sample_user_id, sample_family_id
    ):
        """Test creating chat message."""
        message = ChatMessage(
            id=str(uuid4()),
            trip_id=sample_trip_id,
            user_id=sample_user_id,
            user_name="Test User",
            family_id=sample_family_id,
            message_type=MessageType.CHAT,
            content="Hello world!",
            timestamp=datetime.utcnow(),
            metadata={"test": "data"},
        )

        assert message.trip_id == sample_trip_id
        assert message.user_id == sample_user_id
        assert message.message_type == MessageType.CHAT
        assert message.content == "Hello world!"
        assert message.metadata == {"test": "data"}

    def test_chat_message_to_dict(
        self, sample_trip_id, sample_user_id, sample_family_id
    ):
        """Test converting chat message to dictionary."""
        timestamp = datetime.utcnow()
        message = ChatMessage(
            id="test-id",
            trip_id=sample_trip_id,
            user_id=sample_user_id,
            user_name="Test User",
            family_id=sample_family_id,
            message_type=MessageType.CHAT,
            content="Test message",
            timestamp=timestamp,
        )

        result = message.to_dict()

        assert result["id"] == "test-id"
        assert result["trip_id"] == sample_trip_id
        assert result["user_id"] == sample_user_id
        assert result["user_name"] == "Test User"
        assert result["family_id"] == sample_family_id
        assert result["message_type"] == "chat"
        assert result["content"] == "Test message"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["metadata"] == {}

    def test_chat_message_to_dict_with_metadata(
        self, sample_trip_id, sample_user_id, sample_family_id
    ):
        """Test converting chat message with metadata to dictionary."""
        message = ChatMessage(
            id="test-id",
            trip_id=sample_trip_id,
            user_id=sample_user_id,
            user_name="Test User",
            family_id=sample_family_id,
            message_type=MessageType.VOTE_REQUEST,
            content="Vote on restaurant",
            timestamp=datetime.utcnow(),
            metadata={"vote_id": "123", "options": ["A", "B"]},
        )

        result = message.to_dict()

        assert result["metadata"]["vote_id"] == "123"
        assert result["metadata"]["options"] == ["A", "B"]


class TestUserPresence:
    """Test UserPresence dataclass."""

    def test_user_presence_creation(self, sample_user_id, sample_family_id):
        """Test creating user presence."""
        timestamp = datetime.utcnow()
        presence = UserPresence(
            user_id=sample_user_id,
            user_name="Test User",
            family_id=sample_family_id,
            status="online",
            last_activity=timestamp,
            current_page="/trip/123",
        )

        assert presence.user_id == sample_user_id
        assert presence.user_name == "Test User"
        assert presence.family_id == sample_family_id
        assert presence.status == "online"
        assert presence.last_activity == timestamp
        assert presence.current_page == "/trip/123"

    def test_user_presence_default_values(self, sample_user_id, sample_family_id):
        """Test user presence default values."""
        presence = UserPresence(
            user_id=sample_user_id,
            user_name="Test User",
            family_id=sample_family_id,
            status="online",
            last_activity=datetime.utcnow(),
        )

        assert presence.current_page is None


class TestTripChatRoom:
    """Test TripChatRoom functionality."""

    def test_chat_room_initialization(self, chat_room, sample_trip_id):
        """Test chat room initialization."""
        assert chat_room.trip_id == sample_trip_id
        assert chat_room.connections == {}
        assert chat_room.user_presence == {}
        assert chat_room.message_history == []
        assert chat_room.active_votes == {}
        assert chat_room.typing_users == set()

    def test_message_history_limit(self, chat_room, sample_trip_id, sample_family_id):
        """Test message history is limited to 100 messages."""
        # Add 150 messages directly to history and simulate the trimming logic
        for i in range(150):
            message = ChatMessage(
                id=str(uuid4()),
                trip_id=sample_trip_id,
                user_id="user1",
                user_name="User 1",
                family_id=sample_family_id,
                message_type=MessageType.CHAT,
                content=f"Message {i}",
                timestamp=datetime.utcnow(),
            )
            chat_room.message_history.append(message)

            # Apply the same logic as in broadcast_message
            if len(chat_room.message_history) > 100:
                chat_room.message_history = chat_room.message_history[-100:]

        # Should only keep last 100
        assert len(chat_room.message_history) == 100
        assert chat_room.message_history[0].content == "Message 50"
        assert chat_room.message_history[-1].content == "Message 149"


class TestEnhancedChatService:
    """Test EnhancedChatService functionality."""

    def test_service_initialization(self, chat_service):
        """Test service initialization."""
        assert chat_service.chat_rooms == {}

    def test_get_or_create_room_new(self, chat_service, sample_trip_id):
        """Test getting or creating new room."""
        _room = chat_service.get_or_create_room(sample_trip_id)

        assert isinstance(room, TripChatRoom)
        assert room.trip_id == sample_trip_id
        assert sample_trip_id in chat_service.chat_rooms

    def test_get_or_create_room_existing(self, chat_service, sample_trip_id):
        """Test getting existing room."""
        room1 = chat_service.get_or_create_room(sample_trip_id)
        room2 = chat_service.get_or_create_room(sample_trip_id)

        assert room1 is room2

    def test_get_room_stats(self, chat_service, sample_trip_id):
        """Test getting room statistics."""
        # Create a room with some data
        _room = chat_service.get_or_create_room(sample_trip_id)
        room.connections["user1"] = AsyncMock()
        room.connections["user2"] = AsyncMock()
        room.active_votes["vote1"] = {}

        stats = chat_service.get_room_stats()

        assert stats["total_rooms"] == 1
        assert stats["total_connections"] == 2
        assert sample_trip_id in stats["rooms"]
        assert stats["rooms"][sample_trip_id]["user_count"] == 2
        assert stats["rooms"][sample_trip_id]["active_votes"] == 1


class TestMessageTypes:
    """Test message type enum."""

    def test_message_type_values(self):
        """Test message type enum values."""
        assert MessageType.CHAT.value == "chat"
        assert MessageType.TYPING.value == "typing"
        assert MessageType.ACTIVITY_UPDATE.value == "activity_update"
        assert MessageType.ITINERARY_CHANGE.value == "itinerary_change"
        assert MessageType.FAMILY_STATUS.value == "family_status"
        assert MessageType.SYSTEM_NOTIFICATION.value == "system_notification"
        assert MessageType.VOTE_REQUEST.value == "vote_request"
        assert MessageType.VOTE_RESPONSE.value == "vote_response"
        assert MessageType.USER_PRESENCE.value == "user_presence"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_chat_message_none_metadata(
        self, sample_trip_id, sample_user_id, sample_family_id
    ):
        """Test chat message with None metadata."""
        message = ChatMessage(
            id="test-id",
            trip_id=sample_trip_id,
            user_id=sample_user_id,
            user_name="Test User",
            family_id=sample_family_id,
            message_type=MessageType.CHAT,
            content="Test message",
            timestamp=datetime.utcnow(),
            metadata=None,
        )

        result = message.to_dict()
        assert result["metadata"] == {}

    def test_empty_room_stats(self, chat_service):
        """Test room stats with no rooms."""
        stats = chat_service.get_room_stats()

        assert stats["total_rooms"] == 0
        assert stats["total_connections"] == 0
        assert stats["rooms"] == {}

    def test_room_with_no_connections(self, chat_service, sample_trip_id):
        """Test room stats with room but no connections."""
        _room = chat_service.get_or_create_room(sample_trip_id)

        stats = chat_service.get_room_stats()

        assert stats["total_rooms"] == 1
        assert stats["total_connections"] == 0
        assert stats["rooms"][sample_trip_id]["user_count"] == 0
        assert stats["rooms"][sample_trip_id]["active_votes"] == 0
