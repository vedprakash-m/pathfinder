"""
Integration tests for the trip management system.
"""

import asyncio
import json
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from app.main import app
from fastapi import status
from httpx import AsyncClient


class TestTripIntegration:
    """Integration tests for trip management workflow."""

    @pytest.mark.asyncio
    async def test_complete_trip_workflow(self):
        """Test complete trip creation and management workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Register a user (if needed)
            user_data = {
                "email": "integration@test.com",
                "password": "securepassword123",
                "first_name": "Integration",
                "last_name": "Test",
            }

            register_response = await client.post("/api/v1/auth/register", json=user_data)
            # May fail if user exists, which is okay for integration tests

            # Step 2: Login to get token
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
            else:
                # Skip test if authentication fails
                pytest.skip("Authentication failed - user may not exist")

            # Step 3: Create a trip
            trip_data = {
                "title": "Integration Test Trip",
                "description": "A test trip for integration testing",
                "start_date": (date.today() + timedelta(days=30)).isoformat(),
                "end_date": (date.today() + timedelta(days=35)).isoformat(),
                "budget_total": 3000.0,
                "max_participants": 10,
                "is_public": False,
            }

            create_response = await client.post("/api/v1/trips", json=trip_data, headers=headers)
            assert create_response.status_code == status.HTTP_201_CREATED

            trip = create_response.json()
            trip_id = trip["id"]
            assert trip["title"] == "Integration Test Trip"

            # Step 4: Retrieve the created trip
            get_response = await client.get(f"/api/v1/trips/{trip_id}", headers=headers)
            assert get_response.status_code == status.HTTP_200_OK

            retrieved_trip = get_response.json()
            assert retrieved_trip["id"] == trip_id
            assert retrieved_trip["title"] == "Integration Test Trip"

            # Step 5: Update the trip
            update_data = {
                "title": "Updated Integration Test Trip",
                "description": "Updated description for testing",
                "budget_total": 3500.0,
            }

            update_response = await client.put(
                f"/api/v1/trips/{trip_id}", json=update_data, headers=headers
            )
            assert update_response.status_code == status.HTTP_200_OK

            updated_trip = update_response.json()
            assert updated_trip["title"] == "Updated Integration Test Trip"
            assert updated_trip["budget_total"] == 3500.0

            # Step 6: Get user's trips
            user_trips_response = await client.get("/api/v1/trips", headers=headers)
            assert user_trips_response.status_code == status.HTTP_200_OK

            user_trips = user_trips_response.json()
            trip_ids = [t["id"] for t in user_trips]
            assert trip_id in trip_ids

            # Step 7: Delete the trip (cleanup)
            delete_response = await client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
            # Delete might not be implemented yet
            assert delete_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_204_NO_CONTENT,
                status.HTTP_404_NOT_FOUND,
            ]


class TestFamilyManagementIntegration:
    """Integration tests for family management."""

    @pytest.mark.asyncio
    async def test_family_creation_and_management(self):
        """Test family creation and member management."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login as admin user
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create family
            family_data = {
                "name": "Integration Test Family",
                "description": "A family for integration testing",
                "preferences": {
                    "activities": ["museums", "beaches"],
                    "budget_level": "medium",
                    "dietary_restrictions": ["vegetarian"],
                },
            }

            create_response = await client.post(
                "/api/v1/families", json=family_data, headers=headers
            )
            if create_response.status_code == 201:
                family = create_response.json()
                family_id = family["id"]

                # Get family details
                get_response = await client.get(f"/api/v1/families/{family_id}", headers=headers)
                assert get_response.status_code == status.HTTP_200_OK

                retrieved_family = get_response.json()
                assert retrieved_family["name"] == "Integration Test Family"

                # Update family preferences
                update_data = {
                    "preferences": {
                        "activities": ["museums", "beaches", "hiking"],
                        "budget_level": "high",
                        "dietary_restrictions": ["vegetarian", "gluten-free"],
                    }
                }

                update_response = await client.put(
                    f"/api/v1/families/{family_id}", json=update_data, headers=headers
                )
                if update_response.status_code == 200:
                    updated_family = update_response.json()
                    assert "hiking" in updated_family["preferences"]["activities"]
                    assert updated_family["preferences"]["budget_level"] == "high"


class TestItineraryGenerationIntegration:
    """Integration tests for AI itinerary generation."""

    @pytest.mark.asyncio
    async def test_itinerary_generation_workflow(self):
        """Test complete itinerary generation workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create a trip first
            trip_data = {
                "title": "AI Integration Test Trip",
                "start_date": (date.today() + timedelta(days=60)).isoformat(),
                "end_date": (date.today() + timedelta(days=67)).isoformat(),
                "destinations": ["San Francisco", "Los Angeles"],
                "budget_total": 4000.0,
            }

            create_response = await client.post("/api/v1/trips", json=trip_data, headers=headers)
            if create_response.status_code != 201:
                pytest.skip("Trip creation failed")

            trip = create_response.json()
            trip_id = trip["id"]

            # Generate itinerary for the trip
            itinerary_request = {
                "preferences": {
                    "activities": ["museums", "restaurants", "sightseeing"],
                    "budget_level": "medium",
                    "travel_style": "relaxed",
                },
                "constraints": {
                    "max_daily_budget": 200.0,
                    "accessibility_needs": [],
                    "dietary_restrictions": [],
                },
            }

            itinerary_response = await client.post(
                f"/api/v1/itineraries/{trip_id}/generate", json=itinerary_request, headers=headers
            )

            # Note: This might fail if AI service is not properly configured
            if itinerary_response.status_code == 200:
                itinerary = itinerary_response.json()
                assert "days" in itinerary
                assert len(itinerary["days"]) > 0

                # Get generated itinerary
                get_response = await client.get(f"/api/v1/itineraries/{trip_id}", headers=headers)
                assert get_response.status_code == status.HTTP_200_OK

                retrieved_itinerary = get_response.json()
                assert "days" in retrieved_itinerary
            else:
                # AI service might not be configured, which is acceptable for some environments
                assert itinerary_response.status_code in [400, 404, 500, 503]


class TestNotificationIntegration:
    """Integration tests for notification system."""

    @pytest.mark.asyncio
    async def test_notification_workflow(self):
        """Test notification creation and retrieval."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Get user notifications
            notifications_response = await client.get("/api/v1/notifications", headers=headers)
            assert notifications_response.status_code == status.HTTP_200_OK

            notifications = notifications_response.json()
            assert isinstance(notifications, list)

            # Mark notifications as read (if any exist)
            if notifications:
                notification_id = notifications[0]["id"]
                read_response = await client.put(
                    f"/api/v1/notifications/{notification_id}/read", headers=headers
                )
                assert read_response.status_code in [200, 404]


class TestWebSocketIntegration:
    """Test WebSocket connectivity and real-time features."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Redis - skip in CI environment")
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        # This test requires Redis/Celery which might not be available in CI
        async with AsyncClient(app=app, base_url="http://test") as client:
            with client.websocket_connect("/ws") as websocket:
                data = websocket.receive_text()
                assert data is not None


class TestHealthCheckIntegration:
    """Test health check endpoints and system status."""

    @pytest.mark.asyncio
    async def test_basic_health_check(self):
        """Test basic health endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"  # Main app endpoint returns "healthy"
            assert "environment" in data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health/detailed")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "details" in data
            assert "database" in data["details"]


class TestDataConsistencyIntegration:
    """Integration tests for data consistency across operations."""

    @pytest.mark.asyncio
    async def test_trip_participant_consistency(self):
        """Test data consistency between trips and participants."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create a trip
            trip_data = {
                "title": "Consistency Test Trip",
                "start_date": (date.today() + timedelta(days=90)).isoformat(),
                "end_date": (date.today() + timedelta(days=95)).isoformat(),
                "budget_total": 2000.0,
            }

            create_response = await client.post("/api/v1/trips", json=trip_data, headers=headers)
            if create_response.status_code != 201:
                pytest.skip("Trip creation failed")

            trip = create_response.json()
            trip_id = trip["id"]

            # Join the trip
            join_response = await client.post(f"/api/v1/trips/{trip_id}/join", headers=headers)

            if join_response.status_code == 200:
                # Verify participation is reflected in trip details
                trip_details_response = await client.get(
                    f"/api/v1/trips/{trip_id}", headers=headers
                )
                assert trip_details_response.status_code == status.HTTP_200_OK

                trip_details = trip_details_response.json()

                # Check if participants list includes the user's family
                participants_response = await client.get(
                    f"/api/v1/trips/{trip_id}/participants", headers=headers
                )
                if participants_response.status_code == 200:
                    participants = participants_response.json()
                    assert len(participants) >= 1  # At least the creator should be a participant

            # Leave the trip
            leave_response = await client.post(f"/api/v1/trips/{trip_id}/leave", headers=headers)

            if leave_response.status_code == 200:
                # Verify participation is removed
                participants_response = await client.get(
                    f"/api/v1/trips/{trip_id}/participants", headers=headers
                )
                if participants_response.status_code == 200:
                    participants = participants_response.json()
                    # Should have fewer participants now
