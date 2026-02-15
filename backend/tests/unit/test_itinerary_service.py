"""Unit tests for ItineraryService."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from services.itinerary_service import ItineraryService


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_realtime_service():
    """Create a mock realtime service."""
    service = AsyncMock()
    return service


@pytest.fixture
def itinerary_service(mock_repository, mock_llm_client, mock_realtime_service):
    """Create an itinerary service with mocked dependencies."""
    with (
        patch("services.itinerary_service.CosmosRepository") as MockRepo,
        patch("services.itinerary_service.OpenAIClient") as MockLLM,
        patch("services.itinerary_service.RealtimeService") as MockRealtime,
    ):
        MockRepo.return_value = mock_repository
        MockLLM.return_value = mock_llm_client
        MockRealtime.return_value = mock_realtime_service
        service = ItineraryService()
        service.repository = mock_repository
        service.llm_client = mock_llm_client
        service.realtime_service = mock_realtime_service
        return service


class TestItineraryService:
    """Test cases for ItineraryService."""

    @pytest.mark.asyncio
    async def test_generate_itinerary(self, itinerary_service, mock_repository, mock_llm_client, mock_realtime_service):
        """Test generating an itinerary."""
        # Mock trip data
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "trip_123",
                "pk": "trip_123",
                "entity_type": "trip",
                "name": "Hawaii Vacation",
                "destination": "Honolulu, Hawaii",
                "start_date": "2024-07-01",
                "end_date": "2024-07-07",
                "family_ids": ["family_1"],
            }
        )

        # Mock LLM response
        mock_llm_client.complete = AsyncMock(
            return_value="""
        {
            "days": [
                {
                    "date": "2024-07-01",
                    "activities": [
                        {
                            "time": "09:00",
                            "title": "Beach Morning",
                            "description": "Relax at Waikiki Beach",
                            "location": "Waikiki Beach",
                            "duration_hours": 3
                        }
                    ]
                }
            ]
        }
        """
        )

        mock_repository.create = AsyncMock(
            return_value={
                "id": "itinerary_123",
                "pk": "trip_123",
                "entity_type": "itinerary",
                "trip_id": "trip_123",
                "status": "draft",
                "days": [
                    {
                        "date": "2024-07-01",
                        "activities": [
                            {
                                "time": "09:00",
                                "title": "Beach Morning",
                                "description": "Relax at Waikiki Beach",
                            }
                        ],
                    }
                ],
            }
        )

        result = await itinerary_service.generate_itinerary(
            trip_id="trip_123",
            preferences={
                "budget": "moderate",
                "interests": ["beach", "culture"],
            },
        )

        assert result["trip_id"] == "trip_123"
        assert result["status"] == "draft"
        assert len(result["days"]) > 0
        mock_llm_client.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_itinerary(self, itinerary_service, mock_repository):
        """Test getting an itinerary by trip ID."""
        mock_repository.query = AsyncMock(
            return_value=[
                {
                    "id": "itinerary_123",
                    "pk": "trip_123",
                    "entity_type": "itinerary",
                    "trip_id": "trip_123",
                    "status": "approved",
                    "days": [],
                }
            ]
        )

        result = await itinerary_service.get_itinerary("trip_123")

        assert result["trip_id"] == "trip_123"
        mock_repository.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_itinerary(self, itinerary_service, mock_repository, mock_realtime_service):
        """Test approving an itinerary."""
        mock_repository.query = AsyncMock(
            return_value=[
                {
                    "id": "itinerary_123",
                    "pk": "trip_123",
                    "entity_type": "itinerary",
                    "status": "draft",
                }
            ]
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "itinerary_123",
                "status": "approved",
                "approved_by": "user_1",
                "approved_at": datetime.now(UTC).isoformat(),
            }
        )

        result = await itinerary_service.approve_itinerary(trip_id="trip_123", user_id="user_1")

        assert result["status"] == "approved"
        assert result["approved_by"] == "user_1"
        mock_realtime_service.send_to_group.assert_called()

    @pytest.mark.asyncio
    async def test_update_itinerary_activity(self, itinerary_service, mock_repository, mock_realtime_service):
        """Test updating an activity in the itinerary."""
        mock_repository.query = AsyncMock(
            return_value=[
                {
                    "id": "itinerary_123",
                    "pk": "trip_123",
                    "entity_type": "itinerary",
                    "status": "draft",
                    "days": [
                        {
                            "date": "2024-07-01",
                            "activities": [
                                {
                                    "id": "activity_1",
                                    "time": "09:00",
                                    "title": "Beach Morning",
                                }
                            ],
                        }
                    ],
                }
            ]
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "itinerary_123",
                "days": [
                    {
                        "date": "2024-07-01",
                        "activities": [
                            {
                                "id": "activity_1",
                                "time": "10:00",
                                "title": "Beach Morning - Updated",
                            }
                        ],
                    }
                ],
            }
        )

        result = await itinerary_service.update_itinerary(
            trip_id="trip_123",
            day_index=0,
            activity_id="activity_1",
            updates={
                "time": "10:00",
                "title": "Beach Morning - Updated",
            },
        )

        assert result["days"][0]["activities"][0]["time"] == "10:00"
        mock_realtime_service.send_to_group.assert_called()

    @pytest.mark.asyncio
    async def test_generate_itinerary_trip_not_found(self, itinerary_service, mock_repository):
        """Test generating itinerary for non-existent trip."""
        mock_repository.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Trip not found"):
            await itinerary_service.generate_itinerary(trip_id="nonexistent", preferences={})
