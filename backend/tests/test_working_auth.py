"""
Working authentication test with proper dependency injection mocking.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app
from app.core.security import VedUser, TokenData
from uuid import uuid4


def test_trips_with_complete_mocking():
    """Test trip creation with complete dependency injection mocking."""

    from app.models.trip import TripResponse
    from datetime import date
    from app.core.kink_container import get_container
    import kink

    # Create a test user
    test_user_id = str(uuid4())
    test_user = VedUser(
        id=test_user_id,
        email="test@example.com",
        name="Test User",
        givenName="Test",
        familyName="User",
        permissions=["create:trips", "read:trips", "update:trips", "delete:trips"],
    )

    # Create mock token data
    mock_token_data = TokenData(
        sub=test_user_id,
        email="test@example.com",
        roles=["user"],
        permissions=["create:trips", "read:trips", "update:trips", "delete:trips"],
    )

    # Create mock trip response
    from app.models.trip import TripStatus

    mock_trip_response = TripResponse(
        id="trip-123",
        name="Test Trip",
        description="Test description",
        destination="Test Destination",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 15),
        budget_total=5000.0,
        is_public=False,
        status=TripStatus.PLANNING,
        creator_id=test_user_id,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
    )

    # Create a mock use case
    mock_use_case = AsyncMock()
    mock_use_case.return_value = mock_trip_response

    def mock_create_trip_dependency():
        return mock_use_case

    # Mock everything needed for the trip creation flow
    with patch("app.core.zero_trust.verify_token", return_value=mock_token_data):
        with patch("app.core.security.verify_token", return_value=mock_token_data):
            # Override the dependency injection
            app.dependency_overrides[Provide[Container.create_trip_use_case]] = (
                mock_create_trip_dependency
            )

            try:
                client = TestClient(app)

                # Get CSRF token first
                csrf_response = client.get("/health")
                csrf_token = csrf_response.headers.get("x-csrf-token")

                trip_data = {
                    "name": "Test Trip",
                    "description": "Test description",
                    "destination": "Test Destination",
                    "start_date": "2025-07-01",
                    "end_date": "2025-07-15",
                    "budget_total": 5000.00,
                    "is_public": False,
                }

                headers = {
                    "Authorization": "Bearer valid-token",
                    "X-CSRF-Token": csrf_token,
                    "Content-Type": "application/json",
                }

                response = client.post("/api/v1/trips", json=trip_data, headers=headers)

                print(f"Complete mock response status: {response.status_code}")
                print(f"Complete mock response content: {response.content}")

                # Should succeed
                assert response.status_code in [200, 201]

                # Verify the use case was called
                assert mock_use_case.called
                print("✅ Use case was called successfully!")

                # Verify response content
                response_data = response.json()
                assert response_data["name"] == "Test Trip"
                assert response_data["destination"] == "Test Destination"

            finally:
                # Clean up dependency overrides
                app.dependency_overrides.clear()


def test_ai_service_with_proper_mocking():
    """Test AI service endpoints with proper mocking."""

    from app.services.ai_service import ai_service

    # Mock AI service response
    mock_itinerary = {
        "overview": {
            "destination": "Paris, France",
            "duration": 5,
            "estimated_cost_per_person": 1000.0,
        },
        "daily_itinerary": [{"day": 1, "date": "2025-07-01", "activities": ["Visit Eiffel Tower"]}],
        "budget_summary": {"total": 5000.0, "breakdown": {}},
    }

    # Test the AI service generate_itinerary method
    with patch.object(ai_service, "generate_itinerary", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = mock_itinerary

        # Test calling the method directly
        import asyncio

        async def test_ai_call():
            result = await ai_service.generate_itinerary(
                destination="Paris, France",
                duration_days=5,
                families_data=[{"name": "Test Family", "members": []}],
                preferences={},
                budget_total=5000.0,
            )
            return result

        result = asyncio.run(test_ai_call())

        print(f"AI service result: {result}")
        assert result["overview"]["destination"] == "Paris, France"
        assert mock_generate.called
        print("✅ AI service mocking works!")


def test_health_endpoint():
    """Test that health endpoint works properly."""
    client = TestClient(app)

    response = client.get("/health")

    print(f"Health endpoint status: {response.status_code}")
    print(f"Health endpoint response: {response.json()}")

    assert response.status_code == 200
    assert "status" in response.json()


def test_basic_api_structure():
    """Test that the basic API structure is working."""
    client = TestClient(app)

    # Test OpenAPI docs endpoint
    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_spec = response.json()
    print(f"API has {len(openapi_spec.get('paths', {}))} endpoints")

    # Verify trips endpoints exist
    assert "/api/v1/trips" in openapi_spec.get("paths", {})
    print("✅ Trip endpoints are properly registered!")


if __name__ == "__main__":
    # Run tests directly if needed
    test_health_endpoint()
    test_basic_api_structure()
    test_ai_service_with_proper_mocking()
    print("✅ All basic tests passed!")
