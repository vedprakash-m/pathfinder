"""
Standard authentication error handling for Vedprakash Domain apps.
Implements consistent error responses per Apps_Auth_Requirement.md
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Standard error codes per requirements
AUTH_ERROR_CODES = {
    "AUTH_TOKEN_MISSING": "Access token required",
    "AUTH_TOKEN_INVALID": "Invalid or expired token",
    "AUTH_PERMISSION_DENIED": "Insufficient permissions",
    "AUTH_SERVICE_UNAVAILABLE": "Authentication service temporarily unavailable",
}


class AuthenticationError(Exception):
    """Base authentication error with standardized response format."""

    def __init__(self, code: str, message: str = None, details: Dict[str, Any] = None):
        self.code = code
        self.message = message or AUTH_ERROR_CODES.get(code, "Authentication error")
        self.details = details or {}
        super().__init__(self.message)


class TokenMissingError(AuthenticationError):
    """Raised when no authentication token is provided."""

    def __init__(self, details: Dict[str, Any] = None):
        super().__init__("AUTH_TOKEN_MISSING", details=details)


class TokenInvalidError(AuthenticationError):
    """Raised when authentication token is invalid or expired."""

    def __init__(self, details: Dict[str, Any] = None):
        super().__init__("AUTH_TOKEN_INVALID", details=details)


class PermissionDeniedError(AuthenticationError):
    """Raised when user lacks required permissions."""

    def __init__(self, required_permission: str = None, details: Dict[str, Any] = None):
        message = (
            f"Insufficient permissions. Required: {required_permission}"
            if required_permission
            else None
        )
        super().__init__("AUTH_PERMISSION_DENIED", message=message, details=details)


class AuthServiceUnavailableError(AuthenticationError):
    """Raised when authentication service is temporarily unavailable."""

    def __init__(self, details: Dict[str, Any] = None):
        super().__init__("AUTH_SERVICE_UNAVAILABLE", details=details)


def create_auth_error_response(
    error: AuthenticationError, status_code: int = status.HTTP_401_UNAUTHORIZED
) -> HTTPException:
    """Create standardized HTTPException for authentication errors."""

    # Log authentication error for monitoring
    logger.warning(
        f"Authentication error: {error.code} - {error.message}",
        extra={"error_code": error.code, "error_details": error.details},
    )

    return HTTPException(
        status_code=status_code,
        detail={"error": error.message, "code": error.code, "details": error.details},
        headers={"WWW-Authenticate": "Bearer"},
    )


def handle_auth_error(error: Exception) -> HTTPException:
    """Handle various authentication-related exceptions with standard responses."""

    if isinstance(error, AuthenticationError):
        if error.code == "AUTH_PERMISSION_DENIED":
            return create_auth_error_response(error, status.HTTP_403_FORBIDDEN)
        elif error.code == "AUTH_SERVICE_UNAVAILABLE":
            return create_auth_error_response(error, status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return create_auth_error_response(error)

    # Handle JWT-specific errors
    import jwt

    if isinstance(error, jwt.ExpiredSignatureError):
        return create_auth_error_response(TokenInvalidError({"reason": "Token has expired"}))
    elif isinstance(error, jwt.InvalidTokenError):
        return create_auth_error_response(TokenInvalidError({"reason": str(error)}))

    # Generic authentication error
    logger.error(f"Unhandled authentication error: {error}", exc_info=True)
    return create_auth_error_response(
        AuthenticationError("AUTH_TOKEN_INVALID", "Authentication failed")
    )
