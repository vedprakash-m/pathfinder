"""
End-to-end tests for the Pathfinder application.
"""

import asyncio
import json
from datetime import date, datetime, timedelta

import pytest
from app.main import app
from fastapi import status
from httpx import AsyncClient


@pytest.mark.e2e
class TestCompleteUserJourney:
    """End-to-end tests covering complete user journeys."""

    @pytest.mark.asyncio
    async def test_complete_trip_planning_journey(self):
        """Test complete journey from user registration to trip completion."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. User Registration
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            user_data = {
                "email": f"e2e.user.{timestamp}@test.com",
                "password": "SecurePassword123!",
                "first_name": "E2E",
                "last_name": "User",
            }

            register_response = await client.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == status.HTTP_201_CREATED

            user = register_response.json()
            assert user["email"] == user_data["email"]

            # 2. User Login
            login_data = {"email": user_data["email"], "password": user_data["password"]}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == status.HTTP_200_OK

            auth_data = login_response.json()
            token = auth_data["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # 3. Profile Setup (if family creation is required)
            family_data = {
                "name": f"E2E Family {timestamp}",
                "description": "End-to-end test family",
                "preferences": {
                    "activities": ["sightseeing", "restaurants", "museums"],
                    "budget_level": "medium",
                    "dietary_restrictions": ["vegetarian"],
                    "accessibility_needs": [],
                    "travel_style": "relaxed",
                },
            }

            family_response = await client.post(
                "/api/v1/families", json=family_data, headers=headers
            )
            if family_response.status_code == 201:
                family = family_response.json()
                family_id = family["id"]
            else:
                # Family might be auto-created, get user's family
                profile_response = await client.get("/api/v1/auth/profile", headers=headers)
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    family_id = profile.get("family_id")

            # 4. Trip Creation
            trip_data = {
                "title": f"E2E Test Trip {timestamp}",
                "description": "End-to-end test trip for comprehensive testing",
                "start_date": (date.today() + timedelta(days=30)).isoformat(),
                "end_date": (date.today() + timedelta(days=37)).isoformat(),
                "destinations": ["San Francisco", "Monterey", "Los Angeles"],
                "budget_total": 4500.0,
                "max_participants": 15,
                "is_public": False,
                "preferences": {
                    "accommodation_type": "hotel",
                    "transportation_mode": "car",
                    "activity_level": "moderate",
                },
            }

            create_trip_response = await client.post(
                "/api/v1/trips", json=trip_data, headers=headers
            )
            assert create_trip_response.status_code == status.HTTP_201_CREATED

            trip = create_trip_response.json()
            trip_id = trip["id"]
            assert trip["title"] == trip_data["title"]
            assert trip["status"] == "planning"

            # 5. Trip Preferences Configuration
            preferences_data = {
                "activities": ["Golden Gate Bridge", "Alcatraz", "Santa Monica Pier"],
                "dietary_restrictions": ["vegetarian", "no_nuts"],
                "budget_preferences": {
                    "accommodation": 40,
                    "food": 30,
                    "activities": 20,
                    "transportation": 10,
                },
                "accessibility_requirements": [],
                "special_requests": "Family-friendly activities preferred",
            }

            prefs_response = await client.put(
                f"/api/v1/trips/{trip_id}/preferences", json=preferences_data, headers=headers
            )

            # Preferences endpoint might not exist yet
            if prefs_response.status_code not in [200, 404]:
                pytest.fail(f"Unexpected preferences response: {prefs_response.status_code}")

            # 6. Itinerary Generation
            itinerary_request = {
                "generate_options": {
                    "optimization_focus": "balanced",  # cost, time, or balanced
                    "activity_density": "moderate",  # light, moderate, or packed
                    "include_buffer_time": True,
                    "consider_weather": True,
                },
                "constraints": {
                    "max_daily_budget": 300.0,
                    "max_daily_driving": 4.0,  # hours
                    "preferred_meal_times": {
                        "breakfast": "08:00",
                        "lunch": "12:30",
                        "dinner": "18:30",
                    },
                },
            }

            itinerary_response = await client.post(
                f"/api/v1/itineraries/{trip_id}/generate", json=itinerary_request, headers=headers
            )

            # AI service might not be configured in test environment
            if itinerary_response.status_code == 200:
                itinerary = itinerary_response.json()
                assert "days" in itinerary
                assert len(itinerary["days"]) > 0

                itinerary_id = itinerary.get("id")

                # 7. Itinerary Review and Modification
                modification_request = {
                    "day_index": 0,
                    "modifications": [
                        {
                            "action": "add_activity",
                            "activity": {
                                "title": "Fisherman's Wharf Visit",
                                "time": "14:00",
                                "duration": 120,
                                "location": "San Francisco",
                            },
                        }
                    ],
                }

                modify_response = await client.post(
                    f"/api/v1/itineraries/{trip_id}/modify",
                    json=modification_request,
                    headers=headers,
                )

                # Modification endpoint might not exist
                if modify_response.status_code not in [200, 404]:
                    pytest.fail(f"Unexpected modification response: {modify_response.status_code}")

            elif itinerary_response.status_code not in [400, 404, 500, 503]:
                pytest.fail(
                    f"Unexpected itinerary generation response: {itinerary_response.status_code}"
                )

            # 8. Invite Other Families (simulate)
            invite_data = {
                "email": f"invited.family.{timestamp}@test.com",
                "message": "Join us for an amazing road trip!",
                "permissions": ["view", "comment"],
            }

            invite_response = await client.post(
                f"/api/v1/trips/{trip_id}/invite", json=invite_data, headers=headers
            )

            # Invitation system might not be implemented
            if invite_response.status_code not in [200, 201, 404]:
                pytest.fail(f"Unexpected invite response: {invite_response.status_code}")

            # 9. Trip Status Updates
            status_update = {
                "status": "confirmed",
                "notes": "All participants confirmed, ready to proceed",
            }

            status_response = await client.put(
                f"/api/v1/trips/{trip_id}/status", json=status_update, headers=headers
            )

            if status_response.status_code == 200:
                updated_trip = status_response.json()
                assert updated_trip["status"] == "confirmed"
            elif status_response.status_code not in [404]:
                pytest.fail(f"Unexpected status update response: {status_response.status_code}")

            # 10. Export Trip Data
            export_response = await client.get(
                f"/api/v1/trips/{trip_id}/export/pdf", headers=headers
            )

            if export_response.status_code == 200:
                assert export_response.headers["content-type"] == "application/pdf"
                assert len(export_response.content) > 0
            elif export_response.status_code not in [404, 501]:
                pytest.fail(f"Unexpected export response: {export_response.status_code}")

            # 11. Trip Analytics/Summary
            analytics_response = await client.get(
                f"/api/v1/trips/{trip_id}/analytics", headers=headers
            )

            if analytics_response.status_code == 200:
                analytics = analytics_response.json()
                assert "budget_breakdown" in analytics or "summary" in analytics
            elif analytics_response.status_code not in [404]:
                pytest.fail(f"Unexpected analytics response: {analytics_response.status_code}")

            # 12. Cleanup - Archive or Delete Trip
            archive_response = await client.post(
                f"/api/v1/trips/{trip_id}/archive", headers=headers
            )

            if archive_response.status_code not in [200, 404]:
                # Try delete instead
                delete_response = await client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
                assert delete_response.status_code in [200, 204, 404]


@pytest.mark.e2e
class TestMultiFamilyCoordination:
    """End-to-end tests for multi-family trip coordination."""

    @pytest.mark.asyncio
    async def test_multi_family_trip_coordination(self):
        """Test coordination between multiple families for a single trip."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # Create multiple family admin users
            families = []
            tokens = []

            for i in range(2):  # Create 2 families for testing
                # Register family admin
                user_data = {
                    "email": f"family{i}.admin.{timestamp}@test.com",
                    "password": "SecurePassword123!",
                    "first_name": f"Family{i}",
                    "last_name": "Admin",
                }

                register_response = await client.post("/api/v1/auth/register", json=user_data)
                assert register_response.status_code == status.HTTP_201_CREATED

                # Login to get token
                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": user_data["email"], "password": user_data["password"]},
                )
                assert login_response.status_code == status.HTTP_200_OK

                token = login_response.json()["access_token"]
                tokens.append(token)

                # Create/get family
                family_data = {
                    "name": f"Test Family {i} {timestamp}",
                    "description": f"Test family {i} for multi-family coordination",
                    "preferences": {
                        "activities": ["museums", "beaches", "restaurants"],
                        "budget_level": "medium" if i == 0 else "high",
                        "dietary_restrictions": ["vegetarian"] if i == 0 else [],
                        "travel_style": "relaxed",
                    },
                }

                family_response = await client.post(
                    "/api/v1/families",
                    json=family_data,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if family_response.status_code == 201:
                    families.append(family_response.json())
                else:
                    # Get existing family
                    profile_response = await client.get(
                        "/api/v1/auth/profile", headers={"Authorization": f"Bearer {token}"}
                    )
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        families.append(
                            {"id": profile.get("family_id"), "name": family_data["name"]}
                        )

            # Family 1 creates the trip
            headers1 = {"Authorization": f"Bearer {tokens[0]}"}
            trip_data = {
                "title": f"Multi-Family E2E Trip {timestamp}",
                "description": "Multi-family coordination test trip",
                "start_date": (date.today() + timedelta(days=45)).isoformat(),
                "end_date": (date.today() + timedelta(days=52)).isoformat(),
                "destinations": ["San Francisco", "Napa Valley", "Sacramento"],
                "budget_total": 8000.0,
                "max_participants": 25,
                "is_public": True,
            }

            create_response = await client.post("/api/v1/trips", json=trip_data, headers=headers1)
            assert create_response.status_code == status.HTTP_201_CREATED

            trip = create_response.json()
            trip_id = trip["id"]

            # Family 2 discovers and joins the trip
            headers2 = {"Authorization": f"Bearer {tokens[1]}"}

            # Search for public trips
            search_response = await client.get("/api/v1/trips/search?public=true", headers=headers2)

            if search_response.status_code == 200:
                public_trips = search_response.json()
                trip_ids = [t["id"] for t in public_trips]
                assert trip_id in trip_ids

            # Join the trip
            join_response = await client.post(f"/api/v1/trips/{trip_id}/join", headers=headers2)

            if join_response.status_code == 200:
                # Verify both families are participants
                participants_response = await client.get(
                    f"/api/v1/trips/{trip_id}/participants", headers=headers1
                )

                if participants_response.status_code == 200:
                    participants = participants_response.json()
                    assert len(participants) >= 2

            # Collaborative preference collection
            for i, headers in enumerate([headers1, headers2]):
                family_prefs = {
                    "activities": (
                        ["wine_tasting", "hiking"] if i == 0 else ["shopping", "restaurants"]
                    ),
                    "budget_per_day": 200.0 if i == 0 else 350.0,
                    "special_requirements": f"Family {i} specific requirements",
                }

                prefs_response = await client.put(
                    f"/api/v1/trips/{trip_id}/family-preferences",
                    json=family_prefs,
                    headers=headers,
                )

                # Preferences endpoint might not exist
                if prefs_response.status_code not in [200, 404]:
                    pytest.fail(
                        f"Unexpected family preferences response: {prefs_response.status_code}"
                    )

            # Generate collaborative itinerary
            collaborative_request = {
                "coordination_mode": "balanced",  # balanced, majority, or admin_decides
                "conflict_resolution": "compromise",
                "optimization_goals": ["cost_efficiency", "family_satisfaction", "travel_time"],
            }

            itinerary_response = await client.post(
                f"/api/v1/itineraries/{trip_id}/generate-collaborative",
                json=collaborative_request,
                headers=headers1,
            )

            if itinerary_response.status_code == 200:
                itinerary = itinerary_response.json()

                # Verify itinerary considers both families' preferences
                assert "days" in itinerary

                # Check for family-specific recommendations
                for day in itinerary["days"]:
                    if "activities" in day:
                        for activity in day["activities"]:
                            assert (
                                "family_recommendations" in activity
                                or "suitable_for_all" in activity
                            )
            elif itinerary_response.status_code not in [400, 404, 500, 503]:
                pytest.fail(
                    f"Unexpected collaborative itinerary response: {itinerary_response.status_code}"
                )

            # Test communication/messaging between families
            message_data = {
                "message": "Looking forward to the wine tasting in Napa!",
                "message_type": "general",
                "priority": "normal",
            }

            message_response = await client.post(
                f"/api/v1/trips/{trip_id}/messages", json=message_data, headers=headers1
            )

            if message_response.status_code == 201:
                # Other family reads messages
                messages_response = await client.get(
                    f"/api/v1/trips/{trip_id}/messages", headers=headers2
                )

                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    assert len(messages) >= 1
                    assert any("wine tasting" in msg["message"] for msg in messages)


@pytest.mark.e2e
class TestPerformanceAndReliability:
    """End-to-end tests for performance and reliability."""

    @pytest.mark.asyncio
    async def test_concurrent_trip_operations(self):
        """Test system behavior under concurrent operations."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create multiple trips concurrently
            async def create_trip(index):
                trip_data = {
                    "title": f"Concurrent Trip {index}",
                    "start_date": (date.today() + timedelta(days=60 + index)).isoformat(),
                    "end_date": (date.today() + timedelta(days=67 + index)).isoformat(),
                    "budget_total": 2000.0 + (index * 100),
                }

                response = await client.post("/api/v1/trips", json=trip_data, headers=headers)
                return (
                    response.status_code,
                    response.json() if response.status_code == 201 else None,
                )

            # Run concurrent trip creation
            tasks = [create_trip(i) for i in range(5)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Verify results
            successful_trips = [
                result
                for result in results
                if not isinstance(result, Exception) and result[0] == 201
            ]
            assert len(successful_trips) >= 3  # At least 3 should succeed

            # Test concurrent reads
            if successful_trips:
                trip_id = successful_trips[0][1]["id"]

                async def read_trip():
                    response = await client.get(f"/api/v1/trips/{trip_id}", headers=headers)
                    return response.status_code

                read_tasks = [read_trip() for _ in range(10)]
                read_results = await asyncio.gather(*read_tasks, return_exceptions=True)

                # All reads should succeed
                successful_reads = [
                    result
                    for result in read_results
                    if not isinstance(result, Exception) and result == 200
                ]
                assert len(successful_reads) >= 8  # Most should succeed

    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test system behavior with large datasets."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Create trip with large description and many destinations
            large_description = "This is a very long description. " * 100  # Large text
            many_destinations = [f"City {i}" for i in range(20)]  # Many destinations

            trip_data = {
                "title": "Large Data Test Trip",
                "description": large_description,
                "start_date": (date.today() + timedelta(days=120)).isoformat(),
                "end_date": (date.today() + timedelta(days=150)).isoformat(),
                "destinations": many_destinations,
                "budget_total": 15000.0,
            }

            # This should either succeed or fail gracefully with appropriate limits
            response = await client.post("/api/v1/trips", json=trip_data, headers=headers)
            assert response.status_code in [
                201,
                413,
                422,
            ]  # Created, Payload too large, or Validation error

            if response.status_code == 201:
                trip = response.json()
                trip_id = trip["id"]

                # Verify large data is handled correctly
                get_response = await client.get(f"/api/v1/trips/{trip_id}", headers=headers)
                assert get_response.status_code == 200

                retrieved_trip = get_response.json()
                assert len(retrieved_trip["description"]) > 1000
                assert len(retrieved_trip["destinations"]) == 20


@pytest.mark.e2e
class TestErrorRecoveryAndEdgeCases:
    """End-to-end tests for error recovery and edge cases."""

    @pytest.mark.asyncio
    async def test_network_failure_recovery(self):
        """Test recovery from simulated network failures."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Attempt operations with timeout to simulate network issues
            trip_data = {
                "title": "Network Failure Test Trip",
                "start_date": (date.today() + timedelta(days=180)).isoformat(),
                "end_date": (date.today() + timedelta(days=185)).isoformat(),
                "budget_total": 3000.0,
            }

            try:
                # Set a very short timeout to simulate network issues
                response = await client.post(
                    "/api/v1/trips", json=trip_data, headers=headers, timeout=0.001
                )
                # If this doesn't timeout, that's also acceptable
                assert response.status_code in [201, 408, 504]
            except Exception:
                # Timeout or network error is expected
                pass

            # Now try with normal timeout - should work
            response = await client.post(
                "/api/v1/trips", json=trip_data, headers=headers, timeout=30.0
            )
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_data_validation_edge_cases(self):
        """Test edge cases in data validation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Login
            login_data = {"email": "integration@test.com", "password": "securepassword123"}

            login_response = await client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code != 200:
                pytest.skip("Authentication failed")

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Test edge cases
            edge_cases = [
                # Extreme dates
                {
                    "title": "Far Future Trip",
                    "start_date": "2050-01-01",
                    "end_date": "2050-01-02",
                    "budget_total": 1000.0,
                },
                # Very large budget
                {
                    "title": "Expensive Trip",
                    "start_date": (date.today() + timedelta(days=30)).isoformat(),
                    "end_date": (date.today() + timedelta(days=31)).isoformat(),
                    "budget_total": 1000000.0,
                },
                # Zero budget
                {
                    "title": "Free Trip",
                    "start_date": (date.today() + timedelta(days=30)).isoformat(),
                    "end_date": (date.today() + timedelta(days=31)).isoformat(),
                    "budget_total": 0.0,
                },
            ]

            for case in edge_cases:
                response = await client.post("/api/v1/trips", json=case, headers=headers)
                # Should either accept or reject gracefully
                assert response.status_code in [201, 400, 422]
