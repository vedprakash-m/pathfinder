"""
Debug authentication issues for trip endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.main import app
from fastapi.testclient import TestClient
from app.core.security import VedUser
from uuid import uuid4


def test_debug_auth_response(mock_current_user):
    """Debug the actual authentication response."""

    # Create a mock user with all permissions
    test_user = VedUser(
        id=str(uuid4()),
        email="test@example.com",
        name="Test User",
        givenName="Test",
        familyName="User",
        permissions=[
            "read:trips",
            "create:trips",
            "update:trips",
            "delete:trips",
            "read:families",
            "create:families",
            "update:families",
            "delete:families",
            "read:itineraries",
            "create:itineraries",
            "update:itineraries",
            "delete:itineraries",
        ],
    )

    # Mock the entire zero_trust module
    with patch("app.core.zero_trust.require_permissions") as mock_require:

        def mock_permission_func(resource_type: str, action: str):
            async def permission_checker(*args, **kwargs):
                print(f"Mock permission checker called for {resource_type}:{action}")
                return test_user

            return permission_checker

        mock_require.side_effect = mock_permission_func

        # Also patch the imports in the trips module
        with patch("app.api.trips.require_permissions", side_effect=mock_permission_func):
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
            print(f"Response headers: {response.headers}")

            # Just check that we're not getting auth errors
            assert response.status_code != 401
            assert response.status_code != 403


def test_direct_zero_trust_bypass():
    """Test bypassing zero trust completely."""

    test_user = VedUser(
        id=str(uuid4()),
        email="test@example.com",
        name="Test User",
        givenName="Test", 
        familyName="User",
        permissions=["create:trips"],
    )

    # Patch everything related to zero trust
    with patch("app.core.zero_trust.zero_trust_security") as mock_zero_trust:
        mock_zero_trust.verify_access.return_value = True

        with patch("app.core.zero_trust.verify_token") as mock_verify_token:
            from app.core.security import TokenData

            mock_verify_token.return_value = TokenData(
                sub=test_user.id,
                email=test_user.email,
                roles=test_user.roles,
                permissions=test_user.permissions,
            )

            with patch("app.core.zero_trust.security") as mock_security:
                from fastapi.security import HTTPAuthorizationCredentials

                mock_security.return_value = HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials="mock-token"
                )

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

                # Add Authorization header
                headers = {"Authorization": "Bearer mock-token"}
                response = client.post("/api/v1/trips", json=trip_data, headers=headers)

                print(f"Bypass response status: {response.status_code}")
                print(f"Bypass response content: {response.content}")

                assert response.status_code != 401
                assert response.status_code != 403
