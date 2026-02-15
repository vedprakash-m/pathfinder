"""Unit tests for TripService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from services.trip_service import TripService


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def trip_service(mock_repository):
    """Create a trip service with mocked repository."""
    with patch("services.trip_service.CosmosRepository") as MockRepo:
        MockRepo.return_value = mock_repository
        service = TripService()
        service.repository = mock_repository
        return service


class TestTripService:
    """Test cases for TripService."""

    @pytest.mark.asyncio
    async def test_create_trip(self, trip_service, mock_repository):
        """Test creating a trip."""
        mock_repository.create = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Summer Vacation",
                "destination": "Hawaii",
                "start_date": "2024-07-01",
                "end_date": "2024-07-14",
                "family_ids": ["family_1"],
                "created_by": "user_1",
                "status": "planning",
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )

        result = await trip_service.create_trip(
            name="Summer Vacation",
            destination="Hawaii",
            start_date="2024-07-01",
            end_date="2024-07-14",
            family_ids=["family_1"],
            created_by="user_1",
        )

        assert result["name"] == "Summer Vacation"
        assert result["destination"] == "Hawaii"
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trip(self, trip_service, mock_repository):
        """Test getting a trip by ID."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Summer Vacation",
                "status": "planning",
            }
        )

        result = await trip_service.get_trip("trip_123")

        assert result["id"] == "trip_123"
        assert result["name"] == "Summer Vacation"
        mock_repository.get_by_id.assert_called_once_with("trip_123", "trip_123")

    @pytest.mark.asyncio
    async def test_get_trip_not_found(self, trip_service, mock_repository):
        """Test getting a non-existent trip."""
        mock_repository.get_by_id = AsyncMock(return_value=None)

        result = await trip_service.get_trip("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_trips(self, trip_service, mock_repository):
        """Test getting trips for a user."""
        mock_repository.query = AsyncMock(
            return_value=[
                {"id": "trip_1", "name": "Trip 1"},
                {"id": "trip_2", "name": "Trip 2"},
            ]
        )

        results = await trip_service.get_user_trips("user_1")

        assert len(results) == 2
        mock_repository.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_trip(self, trip_service, mock_repository):
        """Test updating a trip."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Summer Vacation",
                "destination": "Hawaii",
            }
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Winter Getaway",
                "destination": "Aspen",
            }
        )

        result = await trip_service.update_trip("trip_123", {"name": "Winter Getaway", "destination": "Aspen"})

        assert result["name"] == "Winter Getaway"
        assert result["destination"] == "Aspen"

    @pytest.mark.asyncio
    async def test_delete_trip(self, trip_service, mock_repository):
        """Test deleting a trip."""
        mock_repository.delete = AsyncMock()

        await trip_service.delete_trip("trip_123")

        mock_repository.delete.assert_called_once_with("trip_123", "trip_123")

    @pytest.mark.asyncio
    async def test_user_has_access_as_creator(self, trip_service, mock_repository):
        """Test that trip creator has access."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "trip_123",
                "created_by": "user_1",
                "family_ids": ["family_1"],
            }
        )
        mock_repository.query = AsyncMock(return_value=[])

        result = await trip_service.user_has_access("trip_123", "user_1")

        assert result is True

    @pytest.mark.asyncio
    async def test_user_has_access_as_family_member(self, trip_service, mock_repository):
        """Test that family member has access."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "trip_123",
                "created_by": "user_2",
                "family_ids": ["family_1"],
            }
        )
        mock_repository.query = AsyncMock(return_value=[{"id": "family_1", "member_ids": ["user_1", "user_2"]}])

        result = await trip_service.user_has_access("trip_123", "user_1")

        assert result is True

    @pytest.mark.asyncio
    async def test_user_no_access(self, trip_service, mock_repository):
        """Test that unauthorized user has no access."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "trip_123",
                "created_by": "user_2",
                "family_ids": ["family_1"],
            }
        )
        mock_repository.query = AsyncMock(return_value=[{"id": "family_1", "member_ids": ["user_2", "user_3"]}])

        result = await trip_service.user_has_access("trip_123", "user_1")

        assert result is False
