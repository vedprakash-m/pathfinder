"""Unit tests for security module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from core.security import get_current_user_id, get_or_create_user, validate_token


class TestSecurityModule:
    """Test cases for security module."""

    @pytest.fixture
    def mock_jwks_client(self):
        """Create a mock JWKS client."""
        client = MagicMock()
        key = MagicMock()
        key.key = "mock-key"
        client.get_signing_key_from_jwt.return_value = key
        return client

    @pytest.fixture
    def valid_token_payload(self):
        """Create a valid token payload."""
        return {
            "oid": "user-object-id-123",
            "sub": "user-subject-123",
            "name": "John Doe",
            "preferred_username": "john@example.com",
            "email": "john@example.com",
            "aud": "test-client-id",
            "iss": "https://login.microsoftonline.com/vedid.onmicrosoft.com/v2.0",
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(UTC).timestamp()),
            "nbf": int(datetime.now(UTC).timestamp()),
        }

    @pytest.mark.asyncio
    async def test_validate_token_success(self, mock_jwks_client, valid_token_payload):
        """Test successful token validation."""
        with patch("core.security.jwt_client", mock_jwks_client), patch("core.security.jwt.decode") as mock_decode:
            mock_decode.return_value = valid_token_payload

            result = await validate_token("Bearer valid-token")

            assert result is not None
            assert result["oid"] == "user-object-id-123"

    @pytest.mark.asyncio
    async def test_validate_token_missing_bearer(self):
        """Test token validation with missing Bearer prefix."""
        result = await validate_token("invalid-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, mock_jwks_client):
        """Test token validation with expired token."""
        with patch("core.security.jwt_client", mock_jwks_client), patch("core.security.jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

            result = await validate_token("Bearer expired-token")

            assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, mock_jwks_client):
        """Test token validation with invalid token."""
        with patch("core.security.jwt_client", mock_jwks_client), patch("core.security.jwt.decode") as mock_decode:
            mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

            result = await validate_token("Bearer invalid-token")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self):
        """Test getting an existing user."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(
            return_value={
                "id": "user_123",
                "email": "john@example.com",
                "display_name": "John Doe",
            }
        )

        with patch("core.security.CosmosRepository", return_value=mock_repo):
            result = await get_or_create_user(
                {
                    "oid": "user_123",
                    "email": "john@example.com",
                    "name": "John Doe",
                }
            )

            assert result["id"] == "user_123"
            mock_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self):
        """Test creating a new user."""
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock(
            return_value={
                "id": "user_123",
                "email": "john@example.com",
                "display_name": "John Doe",
            }
        )

        with patch("core.security.CosmosRepository", return_value=mock_repo):
            result = await get_or_create_user(
                {
                    "oid": "user_123",
                    "email": "john@example.com",
                    "name": "John Doe",
                }
            )

            assert result["id"] == "user_123"
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_id_from_oid(self):
        """Test extracting user ID from OID claim."""
        claims = {"oid": "user-oid-123", "sub": "user-sub-456"}

        result = get_current_user_id(claims)

        assert result == "user-oid-123"

    @pytest.mark.asyncio
    async def test_get_current_user_id_from_sub(self):
        """Test extracting user ID from sub claim when OID is missing."""
        claims = {"sub": "user-sub-456"}

        result = get_current_user_id(claims)

        assert result == "user-sub-456"

    @pytest.mark.asyncio
    async def test_get_current_user_id_missing(self):
        """Test error when no user ID claim is present."""
        claims = {}

        with pytest.raises(ValueError, match="No user ID"):
            get_current_user_id(claims)
