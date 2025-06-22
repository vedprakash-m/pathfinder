"""
Test trip endpoints with minimal authentication bypass for unit testing.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app
from app.core.security import User
from uuid import uuid4


@pytest.fixture
def simple_client():
    """Create a test client with minimal setup."""
    return TestClient(app)


def test_trips_with_minimal_auth_mock(simple_client):
    """Test trip creation with full authentication bypass."""

    # Create a test user
    test_user = User(
        id=str(uuid4()),
        email="test@example.com",
        roles=["user"],
        permissions=["create:trips", "read:trips", "update:trips", "delete:trips"],
    )

    # Mock the entire require_permissions to return our test user
    async def mock_permission_func(*args, **kwargs):
        return test_user

    # Patch everything at once
    with patch("app.core.zero_trust.require_permissions") as mock_require:
        # Make require_permissions return a function that returns our test user
        mock_require.return_value = mock_permission_func

        # Also patch the direct import in trips
        with patch("app.api.trips.require_permissions", return_value=mock_permission_func):

            trip_data = {
                "name": "Test Trip",
                "description": "Test description",
                "destination": "Test Destination",
                "start_date": "2025-07-01",
                "end_date": "2025-07-15",
                "budget_total": 5000.00,
                "is_public": False,
            }

            response = simple_client.post("/api/v1/trips", json=trip_data)

            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")

            # Should not be an auth error
            assert response.status_code not in [401, 403]


def test_trips_with_direct_endpoint_mock():
    """Test by mocking the trip creation function directly."""

    from app.application.trip_use_cases import CreateTripUseCase
    from app.models.trip import TripResponse
    from datetime import date

    # Create mock response
    mock_trip_response = TripResponse(
        id="trip-123",
        name="Test Trip",
        description="Test description",
        destination="Test Destination",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 15),
        budget_total=5000.0,
        is_public=False,
        creator_id="user-123",
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
    )

    # Mock the use case
    with patch.object(CreateTripUseCase, "__call__", new_callable=AsyncMock) as mock_use_case:
        mock_use_case.return_value = mock_trip_response

        # Mock the authentication completely
        test_user = User(
            id="user-123",
            email="test@example.com",
            roles=["user"],
            permissions=["create:trips"],
        )

        async def mock_auth(*args, **kwargs):
            return test_user

        with patch("app.core.zero_trust.require_permissions", return_value=mock_auth):
            with patch("app.api.trips.require_permissions", return_value=mock_auth):

                client = TestClient(app)

                trip_data = {
                    "name": "Test Trip",
                    "description": "Test description",
                    "destination": "Test Destination",
                    "start_date": "2025-07-01",
                    "end_date": "2025-07-15",
                    "budget_total": 5000.00,
                    "is_public": False,
                }

                response = client.post("/api/v1/trips", json=trip_data)

                print(f"Direct mock response status: {response.status_code}")
                print(f"Direct mock response content: {response.content}")

                # Should succeed if use case was called
                if mock_use_case.called:
                    print("✅ Use case was called - authentication bypassed successfully!")
                    assert response.status_code == 200 or response.status_code == 201
                else:
                    print("❌ Use case not called - authentication still blocking")
                    assert response.status_code not in [
                        401,
                        403,
                    ], "Auth should be bypassed"


def test_check_auth_dependency_override():
    """Test using FastAPI's dependency override system."""

    from app.core.zero_trust import require_permissions

    test_user = User(
        id="user-123",
        email="test@example.com",
        roles=["user"],
        permissions=["create:trips"],
    )

    async def get_test_user():
        return test_user

    # Override the dependency
    app.dependency_overrides[require_permissions("trips", "create")] = get_test_user

    try:
        client = TestClient(app)

        trip_data = {
            "name": "Test Trip",
            "description": "Test description",
            "destination": "Test Destination",
            "start_date": "2025-07-01",
            "end_date": "2025-07-15",
            "budget_total": 5000.00,
            "is_public": False,
        }

        response = client.post("/api/v1/trips", json=trip_data)

        print(f"Dependency override response status: {response.status_code}")
        print(f"Dependency override response content: {response.content}")

        # Should not get auth errors
        assert response.status_code not in [401, 403]

    finally:
        # Clean up
        app.dependency_overrides.clear()
