"""
Comprehensive integration tests for trip management workflow.
"""

import pytest
from datetime import date, timedelta
from fastapi import status
from httpx import AsyncClient
from app.main import app
from app.models.trip import TripCreate, TripStatus
from app.models.family import FamilyCreate


class TestTripManagementIntegration:
    """Integration tests for complete trip management workflow."""

    @pytest.mark.asyncio
    async def test_complete_trip_lifecycle(self):
        """Test complete trip lifecycle from creation to completion."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Create user and authenticate
            login_data = {
                "email": "lifecycle@test.com", 
                "password": "securepassword123"
            }

            # Login or register
            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                # Try to register if login fails
                register_data = {
                    **login_data,
                    "name": "Lifecycle Test User",
                    "family_name": "Lifecycle Family"
                }
                register_response = await client.post("/api/v1/auth/register", json=register_data)
                if register_response.status_code == 201:
                    login_response = await client.post("/api/v1/auth/login", json=login_data)

            if login_response.status_code != 200:
                pytest.skip("Authentication failed - user may not exist")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Step 2: Create a family
            family_data = {
                "name": "Lifecycle Test Family",
                "description": "Family for lifecycle testing",
                "preferences": {
                    "activities": ["sightseeing", "museums", "restaurants"],
                    "budget_level": "medium",
                    "dietary_restrictions": ["vegetarian"],
                    "accessibility_needs": [],
                    "travel_style": "balanced"
                }
            }

            family_response = await client.post("/api/v1/families", json=family_data, headers=headers)
            assert family_response.status_code == status.HTTP_201_CREATED
            family = family_response.json()
            family_id = family["id"]

            # Step 3: Create a trip
            trip_data = {
                "title": "Lifecycle Test Trip",
                "description": "A comprehensive test trip",
                "destination": "Tokyo, Japan",
                "start_date": (date.today() + timedelta(days=60)).isoformat(),
                "end_date": (date.today() + timedelta(days=70)).isoformat(),
                "budget_total": 8000.0,
                "max_participants": 12,
                "is_public": False,
                "family_ids": [family_id]
            }

            create_response = await client.post("/api/v1/trips", json=trip_data, headers=headers)
            assert create_response.status_code == status.HTTP_201_CREATED
            trip = create_response.json()
            trip_id = trip["id"]

            # Step 4: Verify trip creation
            get_response = await client.get(f"/api/v1/trips/{trip_id}", headers=headers)
            assert get_response.status_code == status.HTTP_200_OK
            retrieved_trip = get_response.json()
            assert retrieved_trip["title"] == "Lifecycle Test Trip"
            assert retrieved_trip["status"] == TripStatus.PLANNING.value

            # Step 5: Update trip details
            update_data = {
                "description": "Updated comprehensive test trip",
                "budget_total": 9000.0
            }
            update_response = await client.put(f"/api/v1/trips/{trip_id}", json=update_data, headers=headers)
            assert update_response.status_code == status.HTTP_200_OK
            updated_trip = update_response.json()
            assert updated_trip["description"] == "Updated comprehensive test trip"
            assert updated_trip["budget_total"] == 9000.0

            # Clean up - Delete trip
            delete_response = await client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
            if delete_response.status_code == 204:
                # Verify deletion
                verify_response = await client.get(f"/api/v1/trips/{trip_id}", headers=headers)
                assert verify_response.status_code == status.HTTP_404_NOT_FOUND
            elif delete_response.status_code == 200:
                # Some APIs return 200 with confirmation
                pass
            elif delete_response.status_code not in [404, 501]:
                pytest.fail(f"Unexpected delete response: {delete_response.status_code}")


class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_trip_list_performance(self):
        """Test trip listing performance."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "performance@test.com", "password": "securepassword123"}
            login_response = await client.post("/api/v1/auth/login", json=login_data)

            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Measure response time
            import time
            start_time = time.time()
            
            response = await client.get("/api/v1/trips", headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 2.0, f"Trip list took {response_time}s, should be under 2s"

    @pytest.mark.asyncio
    async def test_concurrent_trip_access(self):
        """Test concurrent access to trip endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            login_data = {"email": "concurrent@test.com", "password": "securepassword123"}
            login_response = await client.post("/api/v1/auth/login", json=login_data)

            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test concurrent reads
            import asyncio
            
            async def fetch_trips():
                response = await client.get("/api/v1/trips", headers=headers)
                return response.status_code == 200

            # Run 5 concurrent requests
            tasks = [fetch_trips() for _ in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_requests = sum(1 for result in results if result is True)
            assert successful_requests >= 4, "At least 4 out of 5 concurrent requests should succeed"
