"""Unit tests for CollaborationService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from services.collaboration_service import CollaborationService


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_realtime_service():
    """Create a mock realtime service."""
    service = AsyncMock()
    return service


@pytest.fixture
def collaboration_service(mock_repository, mock_realtime_service):
    """Create a collaboration service with mocked dependencies."""
    with (
        patch("services.collaboration_service.CosmosRepository") as MockRepo,
        patch("services.collaboration_service.RealtimeService") as MockRealtime,
    ):
        MockRepo.return_value = mock_repository
        MockRealtime.return_value = mock_realtime_service
        service = CollaborationService()
        service.repository = mock_repository
        service.realtime_service = mock_realtime_service
        return service


class TestCollaborationService:
    """Test cases for CollaborationService."""

    @pytest.mark.asyncio
    async def test_create_poll(self, collaboration_service, mock_repository, mock_realtime_service):
        """Test creating a poll."""
        mock_repository.create = AsyncMock(
            return_value={
                "id": "poll_123",
                "pk": "trip_123",
                "entity_type": "poll",
                "trip_id": "trip_123",
                "question": "Which restaurant for dinner?",
                "options": [
                    {"id": "opt_1", "text": "Italian", "votes": []},
                    {"id": "opt_2", "text": "Japanese", "votes": []},
                ],
                "created_by": "user_1",
                "status": "open",
                "created_at": datetime.now(UTC).isoformat(),
            }
        )

        result = await collaboration_service.create_poll(
            trip_id="trip_123",
            question="Which restaurant for dinner?",
            options=["Italian", "Japanese"],
            created_by="user_1",
        )

        assert result["question"] == "Which restaurant for dinner?"
        assert len(result["options"]) == 2
        mock_repository.create.assert_called_once()
        mock_realtime_service.send_to_group.assert_called()

    @pytest.mark.asyncio
    async def test_vote_on_poll(self, collaboration_service, mock_repository, mock_realtime_service):
        """Test voting on a poll."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "poll_123",
                "pk": "trip_123",
                "entity_type": "poll",
                "trip_id": "trip_123",
                "question": "Which restaurant?",
                "options": [
                    {"id": "opt_1", "text": "Italian", "votes": []},
                    {"id": "opt_2", "text": "Japanese", "votes": []},
                ],
                "status": "open",
            }
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "poll_123",
                "options": [
                    {"id": "opt_1", "text": "Italian", "votes": ["user_1"]},
                    {"id": "opt_2", "text": "Japanese", "votes": []},
                ],
            }
        )

        result = await collaboration_service.vote_on_poll(
            poll_id="poll_123", trip_id="trip_123", option_id="opt_1", user_id="user_1"
        )

        assert "user_1" in result["options"][0]["votes"]
        mock_realtime_service.send_to_group.assert_called()

    @pytest.mark.asyncio
    async def test_vote_on_closed_poll(self, collaboration_service, mock_repository):
        """Test that voting on a closed poll fails."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "poll_123",
                "pk": "trip_123",
                "status": "closed",
            }
        )

        with pytest.raises(ValueError, match="Poll is closed"):
            await collaboration_service.vote_on_poll(
                poll_id="poll_123", trip_id="trip_123", option_id="opt_1", user_id="user_1"
            )

    @pytest.mark.asyncio
    async def test_close_poll(self, collaboration_service, mock_repository, mock_realtime_service):
        """Test closing a poll."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "poll_123",
                "pk": "trip_123",
                "entity_type": "poll",
                "created_by": "user_1",
                "status": "open",
                "options": [
                    {"id": "opt_1", "text": "Italian", "votes": ["user_1", "user_2"]},
                    {"id": "opt_2", "text": "Japanese", "votes": ["user_3"]},
                ],
            }
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "poll_123",
                "status": "closed",
                "winner_option_id": "opt_1",
            }
        )

        result = await collaboration_service.close_poll(poll_id="poll_123", trip_id="trip_123", user_id="user_1")

        assert result["status"] == "closed"
        assert result["winner_option_id"] == "opt_1"

    @pytest.mark.asyncio
    async def test_close_poll_unauthorized(self, collaboration_service, mock_repository):
        """Test that non-creator cannot close poll."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "poll_123",
                "pk": "trip_123",
                "created_by": "user_1",
                "status": "open",
            }
        )

        with pytest.raises(PermissionError):
            await collaboration_service.close_poll(
                poll_id="poll_123",
                trip_id="trip_123",
                user_id="user_2",  # Not the creator
            )

    @pytest.mark.asyncio
    async def test_get_consensus_status(self, collaboration_service, mock_repository):
        """Test getting consensus status for a trip."""
        mock_repository.query = AsyncMock(
            return_value=[
                {
                    "id": "poll_1",
                    "status": "closed",
                    "options": [
                        {"id": "opt_1", "votes": ["u1", "u2", "u3"]},
                        {"id": "opt_2", "votes": ["u4"]},
                    ],
                    "winner_option_id": "opt_1",
                },
                {
                    "id": "poll_2",
                    "status": "open",
                    "options": [
                        {"id": "opt_1", "votes": ["u1"]},
                        {"id": "opt_2", "votes": ["u2"]},
                    ],
                },
            ]
        )

        result = await collaboration_service.get_consensus_status("trip_123")

        assert result["total_polls"] == 2
        assert result["closed_polls"] == 1
        assert result["open_polls"] == 1
