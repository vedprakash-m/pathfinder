"""
Unit tests for authentication endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from app.main import app
from fastapi import status
from fastapi.testclient import TestClient

client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @patch("app.api.auth.AuthService")
    def test_register_user_success(self, mock_auth_service_class):
        """Test successful user registration."""
        # Create a mock user object that behaves like the User model
        # SQL User model removed - use Cosmos UserDocument

        mock_user = User(
            id="test-user-id",  # String instead of UUID
            email="test@example.com",
            name="Test User",
            auth0_id="auth0|test123",
            role="family_admin",
            is_active=True,
            is_verified=True,  # Add this required field
            created_at=datetime.utcnow(),
        )

        # Mock the auth service instance
        mock_auth_service = AsyncMock()
        mock_auth_service.create_user = AsyncMock(return_value=mock_user)
        mock_auth_service_class.return_value = mock_auth_service

        # Test data - match UserCreate model schema
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "auth0_id": "auth0|test123",
        }

        # Make request
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    @patch("app.api.auth.AuthService")
    def test_register_user_duplicate_email(self, mock_auth_service_class):
        """Test registration with duplicate email."""
        # Mock the auth service to raise ValueError for duplicate email
        mock_auth_service = AsyncMock()
        mock_auth_service.create_user = AsyncMock(
            side_effect=ValueError("User with this email already exists")
        )
        mock_auth_service_class.return_value = mock_auth_service

        user_data = {
            "email": "existing@example.com",
            "name": "Test User",
            "auth0_id": "auth0|test123",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_invalid_data(self):
        """Test registration with invalid data."""
        # Test with missing required field (email)
        invalid_data = {"name": "Test User"}  # Missing required email field

        response = client.post("/api/v1/auth/register", json=invalid_data)

        # FastAPI should return 422 for Pydantic validation errors
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "email" in str(response.json())

    def test_register_user_invalid_email_format(self):
        """Test registration with invalid email format."""
        # Test with invalid email format
        invalid_data = {"email": "not-an-email"}  # Invalid email format

        response = client.post("/api/v1/auth/register", json=invalid_data)

        # FastAPI should return 422 for Pydantic validation errors
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "email" in str(response.json())

    def test_validate_token_success(self):
        """Test successful token validation."""
        # Skip this test for now as it requires complex auth setup
        # TODO: Implement proper auth mocking for validation endpoint
        pytest.skip("Validation endpoint requires complex auth setup - skip for now")

    @patch("app.api.auth.AuthService")
    def test_logout_success(self, mock_auth_service_class):
        """Test successful logout."""
        # Skip this test for now as it requires complex auth setup
        # TODO: Implement proper auth mocking for logout endpoint
        pytest.skip("Logout endpoint requires complex auth setup - skip for now")

    def test_register_invalid_format(self):
        """Test registration with invalid email format."""
        invalid_data = {"email": "invalid-email", "name": "Test User"}

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPasswordValidation:
    """Test password validation rules."""

    def test_password_too_short(self):
        """Test password that is too short."""
        # Skip password validation tests as current auth uses Auth0
        pytest.skip("Password validation handled by Auth0")

    def test_password_no_complexity(self):
        """Test password with no complexity requirements."""
        # Skip password validation tests as current auth uses Auth0
        pytest.skip("Password validation handled by Auth0")


class TestEmailValidation:
    """Test email validation."""

    def test_invalid_email_formats(self):
        """Test invalid email formats."""
        invalid_emails = [
            "plainaddress",
            "@missingdomain.com",
            "missing@.com",
            "missing.domain@.com",
            "",
        ]

        for email in invalid_emails:
            user_data = {
                "email": email,
                "name": "Test User",
                "auth0_id": "auth0|test123",
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.api.auth.AuthService")
    def test_valid_email_formats(self, mock_auth_service_class):
        """Test valid email formats."""
        valid_emails = [
            "user@domain.com",
            "user.name@domain.com",
            "user+tag@domain.co.uk",
            "user123@domain123.com",
        ]

        for email in valid_emails:
            # Create a mock user object that behaves like the User model
            # SQL User model removed - use Cosmos UserDocument

            mock_user = User(
                id="test-user-id",
                email=email,
                name="Test User",
                auth0_id="auth0|test123",
                role="family_admin",
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
            )

            # Mock the auth service instance
            mock_auth_service = AsyncMock()
            mock_auth_service.create_user = AsyncMock(return_value=mock_user)
            mock_auth_service_class.return_value = mock_auth_service

            user_data = {
                "email": email,
                "name": "Test User",
                "auth0_id": "auth0|test123",
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_201_CREATED
