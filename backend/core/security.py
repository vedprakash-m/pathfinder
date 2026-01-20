"""
Security Module

Handles JWT token validation and user authentication via Microsoft Entra ID.
"""
import logging
from typing import Any, Optional

import azure.functions as func
import jwt
from jwt import PyJWKClient

from models.documents import UserDocument
from repositories.cosmos_repository import cosmos_repo

logger = logging.getLogger(__name__)

# Cache JWKS client
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> PyJWKClient:
    """Get cached JWKS client for token validation."""
    global _jwks_client
    if _jwks_client is None:
        import os

        tenant_id = os.environ.get("ENTRA_TENANT_ID", "vedid.onmicrosoft.com")
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def extract_token(req: func.HttpRequest) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.

    Args:
        req: Azure Functions HTTP request

    Returns:
        Token string if present, None otherwise
    """
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def validate_token(token: str) -> Optional[dict[str, Any]]:
    """
    Validate JWT token and return claims.

    Args:
        token: JWT token string

    Returns:
        Token claims dictionary if valid, None otherwise
    """
    import os

    try:
        # Get signing key from JWKS
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Get configuration
        client_id = os.environ.get("ENTRA_CLIENT_ID")
        tenant_id = os.environ.get("ENTRA_TENANT_ID", "vedid.onmicrosoft.com")

        # Validate token
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            options={"verify_exp": True},
        )

        return claims

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.exception(f"Token validation error: {e}")
        return None


async def get_or_create_user(claims: dict[str, Any]) -> UserDocument:
    """
    Get existing user or create new one from token claims.

    Args:
        claims: Validated JWT token claims

    Returns:
        UserDocument for the authenticated user
    """
    # Extract user identity from claims
    entra_id = claims.get("sub") or claims.get("oid")
    email = claims.get("email") or claims.get("preferred_username", "")
    name = claims.get("name", "")

    if not entra_id:
        raise ValueError("Token missing user identifier (sub or oid)")

    # Try to find existing user by Entra ID
    query = "SELECT * FROM c WHERE c.entity_type = 'user' AND c.entra_id = @entraId"
    users = await cosmos_repo.query(
        query=query, parameters=[{"name": "@entraId", "value": entra_id}], model_class=UserDocument
    )

    if users:
        user = users[0]
        # Update name/email if changed
        if user.email != email or user.name != name:
            user.email = email
            user.name = name
            user = await cosmos_repo.update(user)
        return user

    # Create new user
    user = UserDocument(
        pk=f"user_{entra_id}",
        entra_id=entra_id,
        email=email,
        name=name,
        role="family_admin",  # Default role per PRD
    )

    logger.info(f"Creating new user: {email}")
    return await cosmos_repo.create(user)


async def get_user_from_request(req: func.HttpRequest) -> Optional[UserDocument]:
    """
    Extract and validate user from HTTP request.

    This is the main authentication function used by all protected endpoints.

    Args:
        req: Azure Functions HTTP request

    Returns:
        UserDocument if authenticated, None otherwise
    """
    token = extract_token(req)
    if not token:
        logger.debug("No authorization token provided")
        return None

    claims = await validate_token(token)
    if not claims:
        logger.debug("Token validation failed")
        return None

    try:
        return await get_or_create_user(claims)
    except Exception as e:
        logger.exception(f"Failed to get/create user: {e}")
        return None


def require_auth(
    req: func.HttpRequest,
) -> tuple[Optional[UserDocument], Optional[func.HttpResponse]]:
    """
    Synchronous auth check that returns user or error response.

    This is a helper for simple auth checks.
    For async endpoints, use get_user_from_request directly.

    Returns:
        Tuple of (user, error_response). One will always be None.
    """
    import asyncio

    from core.errors import error_response

    try:
        loop = asyncio.get_event_loop()
        user = loop.run_until_complete(get_user_from_request(req))

        if not user:
            return None, error_response("Unauthorized", 401)

        return user, None
    except Exception as e:
        logger.exception(f"Auth check failed: {e}")
        return None, error_response("Authentication failed", 401)
