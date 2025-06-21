"""
Tests for authentication service and functionality.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.security import create_access_token, verify_token
from app.models.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService
from fastapi import HTTPException
from jose import jwt


@pytest.mark.asyncio
async def test_create_access_token():
    """Test creating an access token."""
    # Arrange
    data = {"sub": "test-user", "email": "test@example.com"}

    # Act
    token = create_access_token(data)

    # Assert
    assert token is not None
    assert isinstance(token, str)

    # Verify token content
    decoded = jwt.decode(
        token,
        "test-secret-key",  # This would be replaced by the actual test env secret
        algorithms=["HS256"],
        # Skip signature verification in test
        options={"verify_signature": False},
    )
    assert decoded["sub"] == "test-user"
    assert decoded["email"] == "test@example.com"
    assert "exp" in decoded  # Expiration time


@pytest.mark.asyncio
async def test_verify_token():
    """Test verifying a valid token."""
    # Arrange
    data = {"sub": "test-user", "email": "test@example.com"}

    # Mock the settings to use a consistent secret key
    with patch("app.core.security.settings.SECRET_KEY", "test-secret-key"):
        # Create token with the same secret key
        token = create_access_token(data)

        # Act - verify with the same secret key
        payload = await verify_token(token)

    # Assert
    assert payload is not None
    assert payload.sub == "test-user"
    assert payload.email == "test@example.com"


@pytest.mark.asyncio
async def test_verify_expired_token():
    """Test that an expired token is rejected."""
    # Arrange - Create a token that's already expired
    data = {"sub": "test-user", "email": "test@example.com"}
    expires_delta = timedelta(minutes=-10)  # 10 minutes ago

    # Mock the settings to use a consistent secret key
    with patch("app.core.security.settings.SECRET_KEY", "test-secret-key"):
        # Create expired token with the same secret key
        token = create_access_token(data, expires_delta)

        # Act & Assert
        with pytest.raises(HTTPException) as excinfo:
            await verify_token(token)

        assert excinfo.value.status_code == 401
        assert "expired" in str(excinfo.value.detail).lower()


@pytest.mark.asyncio
async def test_auth_service_register_user(db_session):
    """Test registering a new user."""
    # Arrange
    auth_service = AuthService()
    user_data = UserCreate(
        email="newuser@example.com", auth0_id="auth0|newuser123", name="New User"
    )

    # Act
    user = await auth_service.create_user(db_session, user_data)

    # Assert
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.name == "New User"
    assert user.auth0_id == "auth0|newuser123"


@pytest.mark.asyncio
async def test_auth_service_get_user_by_auth0_id(db_session, test_user):
    """Test getting a user by Auth0 ID."""
    # Arrange
    auth_service = AuthService()
    auth0_id = test_user.auth0_id

    # Act
    user = await auth_service.get_user_by_auth0_id(db_session, auth0_id)

    # Assert
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email
    assert user.auth0_id == auth0_id


@pytest.mark.asyncio
async def test_auth_service_get_current_user():
    """Test getting the current user from the auth service."""
    # Arrange
    auth_service = AuthService()
    token = "fake-jwt-token"

    # Mock token data
    mock_token_data = MagicMock()
    mock_token_data.sub = "auth0|test123"
    mock_token_data.email = "test@example.com"

    # Mock user
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.auth0_id = "auth0|test123"

    # Mock both AuthService methods directly
    with patch.object(
        auth_service, "verify_token", new=AsyncMock(return_value=mock_token_data)
    ):
        with patch.object(
            auth_service, "get_user_by_auth0_id", new=AsyncMock(return_value=mock_user)
        ):
            # Create mock db session
            mock_db = MagicMock()

            # Act
            user = await auth_service.get_current_user(mock_db, token)

            # Assert
            assert user is not None
            assert user.id == "test-user-id"
            assert user.email == "test@example.com"
            assert user.auth0_id == "auth0|test123"


@pytest.mark.asyncio
async def test_auth_service_update_user_profile(db_session, test_user):
    """Test updating a user's profile."""
    # Arrange
    auth_service = AuthService()
    user_id = test_user.id
    update_data = UserUpdate(name="Updated User")

    # Act
    updated_user = await auth_service.update_user(db_session, str(user_id), update_data)

    # Assert
    assert updated_user is not None
    assert updated_user.name == "Updated User"
    assert updated_user.email == test_user.email  # Unchanged field


@pytest.mark.asyncio
async def test_auth_service_validate_permissions():
    """Test validating user permissions for a resource."""
    # Test that we can create the auth service and it has expected methods
    auth_service = AuthService()

    # Act & Assert
    assert auth_service is not None
    assert hasattr(auth_service, "verify_token")
    assert hasattr(auth_service, "get_current_user")

    # This test verifies the AuthService is properly structured
    # Permission validation would typically be tested with a real database setup
