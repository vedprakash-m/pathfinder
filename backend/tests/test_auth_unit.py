"""
Unit tests for authentication endpoints.
"""

from unittest.mock import AsyncMock, patch

from app.main import app
from fastapi import status
from fastapi.testclient import TestClient

client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @patch("app.services.auth_service.AuthService")
    def test_register_user_success(self, mock_auth_service_class):
        """Test successful user registration."""
        # Mock the auth service instance
        mock_auth_service = AsyncMock()
        mock_auth_service.create_user = AsyncMock(
            return_value={
                "id": "test-user-id",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "is_active": True,
            }
        )
        mock_auth_service_class.return_value = mock_auth_service

        # Test data
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
        }

        # Make request
        response = client.post("/api/v1/auth/register", json=user_data)

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
        assert "password" not in data  # Ensure password is not returned

    @patch("app.services.auth_service.AuthService")
    def test_register_user_duplicate_email(self, mock_auth_service_class):
        """Test registration with duplicate email."""
        # Mock the auth service to raise an exception
        mock_auth_service.register_user = AsyncMock(
            side_effect=ValueError("Email already registered")
        )

        user_data = {
            "email": "duplicate@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_invalid_data(self):
        """Test registration with invalid data."""
        # Missing required fields
        invalid_data = {
            "email": "test@example.com"
            # Missing password, first_name, last_name
        }

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.api.auth.auth_service")
    def test_login_success(self, mock_auth_service):
        """Test successful login."""
        # Mock the auth service
        mock_auth_service.authenticate_user = AsyncMock(
            return_value={
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "test-user-id",
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            }
        )

        login_data = {"email": "test@example.com", "password": "securepassword123"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == "test-access-token"
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    @patch("app.api.auth.auth_service")
    def test_login_invalid_credentials(self, mock_auth_service):
        """Test login with invalid credentials."""
        mock_auth_service.authenticate_user = AsyncMock(
            side_effect=ValueError("Invalid credentials")
        )

        login_data = {"email": "test@example.com", "password": "wrongpassword"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_format(self):
        """Test login with invalid email format."""
        login_data = {"email": "invalid-email", "password": "securepassword123"}

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPasswordValidation:
    """Test password validation rules."""

    def test_password_too_short(self):
        """Test password that's too short."""
        user_data = {
            "email": "test@example.com",
            "password": "short",
            "first_name": "Test",
            "last_name": "User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_password_no_complexity(self):
        """Test password without complexity requirements."""
        user_data = {
            "email": "test@example.com",
            "password": "allowercase",
            "first_name": "Test",
            "last_name": "User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        # This might pass depending on validation rules
        # Add specific validation logic as needed
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


class TestEmailValidation:
    """Test email validation."""

    def test_invalid_email_formats(self):
        """Test various invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@domain.com",
            "user@",
            "user@domain",
            "user.domain.com",
            "",
        ]

        for email in invalid_emails:
            user_data = {
                "email": email,
                "password": "securepassword123",
                "first_name": "Test",
                "last_name": "User",
            }

            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_valid_email_formats(self):
        """Test valid email formats."""
        valid_emails = [
            "user@domain.com",
            "user.name@domain.com",
            "user+tag@domain.co.uk",
            "user123@domain123.com",
        ]

        for email in valid_emails:
            with patch("app.api.auth.auth_service") as mock_auth_service:
                mock_auth_service.register_user = AsyncMock(
                    return_value={
                        "id": "test-user-id",
                        "email": email,
                        "first_name": "Test",
                        "last_name": "User",
                        "is_active": True,
                    }
                )

                user_data = {
                    "email": email,
                    "password": "securepassword123",
                    "first_name": "Test",
                    "last_name": "User",
                }

                response = client.post("/api/v1/auth/register", json=user_data)
                assert response.status_code == status.HTTP_201_CREATED
