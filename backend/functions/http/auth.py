"""
Authentication HTTP Functions

Handles user authentication with Microsoft Entra ID.
"""

import logging
from datetime import UTC, datetime

import azure.functions as func

from core.config import get_settings
from core.errors import APIError, ErrorCode, error_response, success_response
from core.security import get_user_from_request, validate_token
from models.schemas import UserResponse
from repositories.cosmos_repository import cosmos_repo

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


@bp.route(route="auth/me", methods=["GET"])
async def get_current_user(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get the current authenticated user's profile.

    Requires: Valid JWT token in Authorization header
    Returns: User profile data
    """
    try:
        user = await get_user_from_request(req)

        if not user:
            return error_response(
                error=APIError(code=ErrorCode.AUTHENTICATION_ERROR, message="Not authenticated"), status_code=401
            )

        user_response = UserResponse.from_document(user)
        return success_response(user_response.model_dump())

    except APIError as e:
        return error_response(e)
    except Exception:
        logger.exception("Error getting current user")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get user profile"), status_code=500
        )


@bp.route(route="auth/validate", methods=["POST"])
async def validate_auth_token(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validate an authentication token.

    Used by frontend to check if token is still valid.

    Body: {"token": "jwt_token"}
    Returns: {"valid": true/false, "expires_at": "ISO timestamp"}
    """
    try:
        body = req.get_json()
        token = body.get("token")

        if not token:
            return error_response(
                APIError(code=ErrorCode.VALIDATION_ERROR, message="Token is required"), status_code=400
            )

        claims = await validate_token(token)

        if claims:
            exp = claims.get("exp", 0)
            return success_response(
                {
                    "valid": True,
                    "expires_at": datetime.fromtimestamp(exp, tz=UTC).isoformat(),
                    "user_id": claims.get("oid"),
                    "email": claims.get("preferred_username"),
                }
            )
        else:
            return success_response({"valid": False, "message": "Token is invalid or expired"})

    except Exception:
        logger.exception("Error validating token")
        return success_response({"valid": False, "message": "Token validation failed"})


@bp.route(route="auth/refresh", methods=["POST"])
async def refresh_token_info(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get information about token refresh.

    Note: Actual token refresh is handled by MSAL on the frontend.
    This endpoint provides the Entra ID configuration for the frontend.
    """
    try:
        settings = get_settings()

        return success_response(
            {
                "tenant_id": settings.ENTRA_TENANT_ID,
                "client_id": settings.ENTRA_CLIENT_ID,
                "authority": f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}",
                "scopes": [f"api://{settings.ENTRA_CLIENT_ID}/access_as_user"],
            }
        )

    except Exception:
        logger.exception("Error getting auth config")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get authentication configuration"),
            status_code=500,
        )


@bp.route(route="auth/logout", methods=["POST"])
async def logout(req: func.HttpRequest) -> func.HttpResponse:
    """
    Log out the current user.

    This is primarily a client-side operation, but we can use this
    to perform any server-side cleanup if needed.
    """
    try:
        user = await get_user_from_request(req)

        if user:
            logger.info(f"User logged out: {user.id}")

            # Update last_login timestamp
            user.updated_at = utc_now()
            await cosmos_repo.update(user)

        return success_response({"message": "Logged out successfully"})

    except Exception:
        logger.exception("Error during logout")
        # Still return success - logout should always "succeed" from client perspective
        return success_response({"message": "Logged out"})


@bp.route(route="auth/config", methods=["GET"])
async def get_auth_config(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get public authentication configuration.

    Used by frontend to configure MSAL.
    """
    try:
        settings = get_settings()

        return success_response(
            {
                "authority": f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}",
                "clientId": settings.ENTRA_CLIENT_ID,
                "redirectUri": settings.FRONTEND_URL,
                "postLogoutRedirectUri": settings.FRONTEND_URL,
                "scopes": [f"api://{settings.ENTRA_CLIENT_ID}/access_as_user", "openid", "profile", "email"],
            }
        )

    except Exception:
        logger.exception("Error getting auth config")
        return error_response(
            APIError(code=ErrorCode.INTERNAL_ERROR, message="Failed to get authentication configuration"),
            status_code=500,
        )
