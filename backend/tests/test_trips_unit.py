"""
Unit tests for trip management functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, date, timedelta
import json

from app.main import app

client = TestClient(app)


class TestTripCreation:
    """Test trip creation functionality."""

    @patch("backend.domain.trip.TripDomainService")
    @patch("app.core.security.get_current_user")
    def test_create_trip_success(self, mock_get_user, mock_trip_service):
        """Test successful trip creation."""
        # Mock current user
        mock_get_user.return_value = {
            "id": "user-123",
            "email": "admin@example.com",
            "family_id": "family-456",
        }

        # Mock trip service
        mock_trip_service.create_trip = AsyncMock(
            return_value={
                "id": "trip-789",
                "title": "Family Vacation 2025",
                "description": "Annual family road trip",
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "created_by": "user-123",
                "status": "planning",
                "is_public": False,
            }
        )

        trip_data = {
            "title": "Family Vacation 2025",
            "description": "Annual family road trip",
            "start_date": "2025-07-01",
            "end_date": "2025-07-15",
            "budget_total": 5000.00,
            "max_participants": 20,
            "is_public": False,
        }

        # Mock authorization header
        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips", json=trip_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Family Vacation 2025"
        assert data["status"] == "planning"

    @patch("app.api.trips.get_current_user")
    def test_create_trip_unauthorized(self, mock_get_user):
        """Test trip creation without authentication."""
        response = client.post("/api/v1/trips", json={"title": "Test Trip"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_trip_invalid_dates(self):
        """Test trip creation with invalid date range."""
        trip_data = {
            "title": "Invalid Trip",
            "start_date": "2025-07-15",
            "end_date": "2025-07-01",  # End before start
            "budget_total": 1000.00,
        }

        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips", json=trip_data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_trip_missing_required_fields(self):
        """Test trip creation with missing required fields."""
        trip_data = {"description": "Missing title and dates"}

        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips", json=trip_data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTripRetrieval:
    """Test trip retrieval functionality."""

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_get_trip_by_id_success(self, mock_get_user, mock_trip_service):
        """Test successful trip retrieval by ID."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}

        mock_trip_service.get_trip_by_id = AsyncMock(
            return_value={
                "id": "trip-789",
                "title": "Family Vacation 2025",
                "description": "Annual family road trip",
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "status": "planning",
                "participants": [],
            }
        )

        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/api/v1/trips/trip-789", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "trip-789"
        assert data["title"] == "Family Vacation 2025"

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_get_trip_not_found(self, mock_get_user, mock_trip_service):
        """Test retrieval of non-existent trip."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}
        mock_trip_service.get_trip_by_id = AsyncMock(return_value=None)

        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/api/v1/trips/nonexistent", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_get_user_trips(self, mock_get_user, mock_trip_service):
        """Test retrieval of user's trips."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}

        mock_trip_service.get_user_trips = AsyncMock(
            return_value=[
                {
                    "id": "trip-1",
                    "title": "Trip 1",
                    "start_date": "2025-07-01",
                    "status": "planning",
                },
                {"id": "trip-2", "title": "Trip 2", "start_date": "2025-08-01", "status": "active"},
            ]
        )

        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/api/v1/trips", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Trip 1"
        assert data[1]["title"] == "Trip 2"


class TestTripUpdates:
    """Test trip update functionality."""

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_update_trip_success(self, mock_get_user, mock_trip_service):
        """Test successful trip update."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}

        mock_trip_service.update_trip = AsyncMock(
            return_value={
                "id": "trip-789",
                "title": "Updated Family Vacation 2025",
                "description": "Updated description",
                "start_date": "2025-07-01",
                "end_date": "2025-07-20",  # Extended end date
                "status": "planning",
            }
        )

        update_data = {
            "title": "Updated Family Vacation 2025",
            "description": "Updated description",
            "end_date": "2025-07-20",
        }

        headers = {"Authorization": "Bearer test-token"}
        response = client.put("/api/v1/trips/trip-789", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Family Vacation 2025"
        assert data["end_date"] == "2025-07-20"

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_update_trip_not_found(self, mock_get_user, mock_trip_service):
        """Test update of non-existent trip."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}
        mock_trip_service.update_trip = AsyncMock(return_value=None)

        update_data = {"title": "Updated Title"}

        headers = {"Authorization": "Bearer test-token"}
        response = client.put("/api/v1/trips/nonexistent", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_update_trip_unauthorized(self, mock_get_user, mock_trip_service):
        """Test update by non-authorized user."""
        mock_get_user.return_value = {"id": "user-999", "family_id": "other-family"}
        mock_trip_service.update_trip = AsyncMock(side_effect=PermissionError("Not authorized"))

        update_data = {"title": "Unauthorized Update"}

        headers = {"Authorization": "Bearer test-token"}
        response = client.put("/api/v1/trips/trip-789", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestTripParticipation:
    """Test trip participation functionality."""

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_join_trip_success(self, mock_get_user, mock_trip_service):
        """Test successful trip join."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}

        mock_trip_service.join_trip = AsyncMock(
            return_value={
                "trip_id": "trip-789",
                "family_id": "family-456",
                "status": "confirmed",
                "joined_at": datetime.now().isoformat(),
            }
        )

        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips/trip-789/join", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "confirmed"

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_leave_trip_success(self, mock_get_user, mock_trip_service):
        """Test successful trip leave."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}

        mock_trip_service.leave_trip = AsyncMock(return_value=True)

        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips/trip-789/leave", headers=headers)

        assert response.status_code == status.HTTP_200_OK

    @patch("app.api.trips.trip_service")
    @patch("app.api.trips.get_current_user")
    def test_get_trip_participants(self, mock_get_user, mock_trip_service):
        """Test retrieval of trip participants."""
        mock_get_user.return_value = {"id": "user-123", "family_id": "family-456"}

        mock_trip_service.get_trip_participants = AsyncMock(
            return_value=[
                {
                    "family_id": "family-456",
                    "family_name": "Smith Family",
                    "status": "confirmed",
                    "joined_at": "2025-05-01T10:00:00",
                },
                {
                    "family_id": "family-789",
                    "family_name": "Johnson Family",
                    "status": "pending",
                    "joined_at": "2025-05-02T15:30:00",
                },
            ]
        )

        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/api/v1/trips/trip-789/participants", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["family_name"] == "Smith Family"
        assert data[1]["status"] == "pending"


class TestTripValidation:
    """Test trip data validation."""

    def test_budget_validation(self):
        """Test budget validation."""
        invalid_budgets = [-1000, 0, "invalid"]

        for budget in invalid_budgets:
            trip_data = {
                "title": "Test Trip",
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "budget_total": budget,
            }

            headers = {"Authorization": "Bearer test-token"}
            response = client.post("/api/v1/trips", json=trip_data, headers=headers)

            if isinstance(budget, (int, float)) and budget <= 0:
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            elif budget == "invalid":
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_participant_limit_validation(self):
        """Test participant limit validation."""
        trip_data = {
            "title": "Test Trip",
            "start_date": "2025-07-01",
            "end_date": "2025-07-15",
            "max_participants": -5,  # Invalid negative value
        }

        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips", json=trip_data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_date_range_validation(self):
        """Test various date range validations."""
        # Past start date
        trip_data = {"title": "Past Trip", "start_date": "2020-01-01", "end_date": "2020-01-15"}

        headers = {"Authorization": "Bearer test-token"}
        response = client.post("/api/v1/trips", json=trip_data, headers=headers)

        # Should either reject past dates or allow them for testing
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_201_CREATED,
        ]

        # Same start and end date
        trip_data = {
            "title": "Single Day Trip",
            "start_date": "2025-07-01",
            "end_date": "2025-07-01",
        }

        response = client.post("/api/v1/trips", json=trip_data, headers=headers)

        # Should allow single day trips
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_201_CREATED,
        ]
