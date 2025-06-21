"""
Final integration test for trip creation endpoint.
Tests that authentication, business logic, and response structure all work correctly.
"""

import pytest
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.core.security import TokenData


def test_trip_creation_end_to_end():
    """Test complete trip creation flow with authentication and business logic."""

    # Create a test user ID
    test_user_id = str(uuid4())

    # Create mock token data (this is what the authentication system uses)
    mock_token_data = TokenData(
        sub=test_user_id,
        email="integration@example.com",
        roles=["user"],
        permissions=["create:trips", "read:trips",
            "update:trips", "delete:trips"],
    )

    # Mock authentication
    with patch("app.core.zero_trust.verify_token", return_value=mock_token_data):
        with patch("app.core.security.verify_token", return_value=mock_token_data):

            client = TestClient(app)

            # Get CSRF token
            csrf_response = client.get("/health")
            csrf_token = csrf_response.headers.get("x-csrf-token")

            trip_data = {
                "name": "Integration Test Trip",
                "description": "A test trip created by integration test",
                "destination": "Integration Test Destination",
                "start_date": "2025-08-01",
                "end_date": "2025-08-15",
                "budget_total": 3000.00,
                "is_public": False,
            }

            headers = {
                "Authorization": "Bearer valid-integration-token",
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json",
            }

            response = client.post(
                "/api/v1/trips", json=trip_data, headers=headers)

            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")

            # Should succeed
            assert response.status_code in [200, 201]

            # Verify response structure
            response_data = response.json()
            assert "id" in response_data
            assert response_data["name"] == "Integration Test Trip"
            assert (
                response_data["description"]
                == "A test trip created by integration test"
            )
            assert response_data["destination"] == "Integration Test Destination"
            assert response_data["start_date"] == "2025-08-01"
            assert response_data["end_date"] == "2025-08-15"
            assert (
                response_data["budget_total"] is None
                or response_data["budget_total"] == 3000.0
            )
            assert response_data["is_public"] == False
            assert response_data["status"] == "planning"
            assert response_data["creator_id"] == test_user_id
            assert "created_at" in response_data
            assert "updated_at" in response_data
            assert (
                response_data["family_count"] == 0
            )  # New trip should have no families initially
            assert response_data["confirmed_families"] == 0


def test_trip_creation_without_auth():
    """Test that trip creation fails without proper authentication."""

    client = TestClient(app)

    # Get CSRF token
    csrf_response = client.get("/health")
    csrf_token = csrf_response.headers.get("x-csrf-token")

    trip_data = {
        "name": "Unauthorized Trip",
        "description": "This should fail",
        "destination": "Nowhere",
        "start_date": "2025-08-01",
        "end_date": "2025-08-15",
        "budget_total": 1000.00,
        "is_public": False,
    }

    headers = {
        "X-CSRF-Token": csrf_token,  # No Authorization header
        "Content-Type": "application/json",
    }

    response = client.post("/api/v1/trips", json=trip_data, headers=headers)

    print(f"Unauthorized response status: {response.status_code}")
    print(f"Unauthorized response content: {response.content}")

    # Should fail with authentication error
    assert response.status_code in [401, 403]


def test_trip_creation_with_invalid_data():
    """Test that trip creation fails with invalid data."""

    # Create a test user
    test_user_id = str(uuid4())
    mock_token_data = TokenData(
        sub=test_user_id,
        email="invalid@example.com",
        roles=["user"],
        permissions=["create:trips"],
    )

    # Mock authentication
    with patch("app.core.zero_trust.verify_token", return_value=mock_token_data):
        with patch("app.core.security.verify_token", return_value=mock_token_data):

            client = TestClient(app)

            # Get CSRF token
            csrf_response = client.get("/health")
            csrf_token = csrf_response.headers.get("x-csrf-token")

            # Invalid trip data (missing required fields)
            trip_data = {
                "name": "",  # Empty name should be invalid
                "destination": "",  # Empty destination should be invalid
                # Missing start_date and end_date
            }

            headers = {
                "Authorization": "Bearer valid-token",
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/json",
            }

            response = client.post(
                "/api/v1/trips", json=trip_data, headers=headers)

            print(f"Invalid data response status: {response.status_code}")
            print(f"Invalid data response content: {response.content}")

            # Should fail with validation error
            assert response.status_code == 422  # Unprocessable Entity
