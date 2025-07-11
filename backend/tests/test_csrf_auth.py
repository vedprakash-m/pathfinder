"""
Test trip endpoints with proper CSRF and auth handling.
"""

import os
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.core.security import VedUser
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def testing_env():
    """Set environment to testing to disable CSRF."""
    original_env = os.environ.get("ENVIRONMENT", "development")
    os.environ["ENVIRONMENT"] = "testing"

    # Clear any cached settings
    from app.core.config import get_settings

    get_settings.cache_clear()

    yield

    # Restore original environment
    os.environ["ENVIRONMENT"] = original_env
    get_settings.cache_clear()


@pytest.mark.skip(reason="Complex auth mocking - requires more investigation")
def test_trips_with_testing_env(testing_env):
    """Test trip creation with testing environment (no CSRF)."""

    from app.core.config import get_settings

    settings = get_settings()

    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Is testing: {settings.is_testing}")

    # Confirm we're in testing mode
    assert settings.is_testing is True

    # Create a test user
    test_user = VedUser(
        id=str(uuid4()),
        email="test@example.com",
        name="Test User",
        givenName="Test",
        familyName="User",
        permissions=["create:trips", "read:trips", "update:trips", "delete:trips"],
    )

    # Mock the authentication dependency function
    async def mock_permission_checker(*args, **kwargs):
        return test_user

    with patch("app.api.trips.require_permissions") as mock_require:
        mock_require.return_value = mock_permission_checker
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

        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")

        # Should not be an auth error
        assert response.status_code not in [401, 403]


def test_trips_with_csrf_token():
    """Test trip creation with proper CSRF token."""

    # First get a CSRF token
    client = TestClient(app)

    # Get CSRF token from a GET request
    csrf_response = client.get("/health")
    csrf_token = csrf_response.headers.get("x-csrf-token")

    print(f"CSRF token: {csrf_token}")

    if csrf_token:
        # Create a test user
        test_user = VedUser(
            id=str(uuid4()),
            email="test@example.com",
            name="Test User",
            givenName="Test",
            familyName="User",
            permissions=["create:trips"],
        )

        # Mock the authentication
        async def mock_auth(*args, **kwargs):
            return test_user

        with patch("app.core.zero_trust.require_permissions", return_value=mock_auth):
            with patch("app.api.trips.require_permissions", return_value=mock_auth):
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
                    "X-CSRF-Token": csrf_token,
                    "Authorization": "Bearer mock-token",
                }

                response = client.post("/api/v1/trips", json=trip_data, headers=headers)

                print(f"CSRF response status: {response.status_code}")
                print(f"CSRF response content: {response.content}")

                # Should not be an auth error
                assert response.status_code not in [401, 403]
    else:
        pytest.skip("No CSRF token available")


def test_health_endpoint_works():
    """Verify that health endpoint works and provides CSRF token."""
    client = TestClient(app)

    response = client.get("/health")

    print(f"Health status: {response.status_code}")
    print(f"Health headers: {dict(response.headers)}")

    assert response.status_code == 200
    assert "x-csrf-token" in response.headers
