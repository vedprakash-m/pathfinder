"""
Error Handling

Standardized error handling for the API.
Provides consistent error responses across all endpoints.
"""
import json
import logging
from enum import Enum
from typing import Any, Optional

import azure.functions as func

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # Authentication errors (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"

    # Authorization errors (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Resource errors (404)
    NOT_FOUND = "NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    TRIP_NOT_FOUND = "TRIP_NOT_FOUND"
    FAMILY_NOT_FOUND = "FAMILY_NOT_FOUND"

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_FIELD = "MISSING_FIELD"

    # Conflict errors (409)
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"

    # Rate limiting (429)
    RATE_LIMITED = "RATE_LIMITED"

    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


class APIError(Exception):
    """Custom API exception with structured error information."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {"error": {"code": self.code.value, "message": self.message, "details": self.details}}

    def to_response(self) -> func.HttpResponse:
        """Convert error to HTTP response."""
        return func.HttpResponse(json.dumps(self.to_dict()), status_code=self.status_code, mimetype="application/json")


def error_response(
    message: str, status_code: int = 500, code: Optional[ErrorCode] = None, details: Optional[dict[str, Any]] = None
) -> func.HttpResponse:
    """
    Create a standardized error response.

    Args:
        message: Human-readable error message
        status_code: HTTP status code
        code: Optional error code enum
        details: Optional additional details

    Returns:
        Azure Functions HTTP response with error JSON
    """
    # Determine error code from status if not provided
    if code is None:
        code_map = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.CONFLICT,
            429: ErrorCode.RATE_LIMITED,
            500: ErrorCode.INTERNAL_ERROR,
        }
        code = code_map.get(status_code, ErrorCode.INTERNAL_ERROR)

    error_body = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }

    if details:
        error_body["error"]["details"] = details

    # Log errors at appropriate levels
    if status_code >= 500:
        logger.error(f"API Error [{code.value}]: {message}", extra={"details": details})
    elif status_code >= 400:
        logger.warning(f"API Error [{code.value}]: {message}", extra={"details": details})

    return func.HttpResponse(json.dumps(error_body), status_code=status_code, mimetype="application/json")


def success_response(data: Any, status_code: int = 200) -> func.HttpResponse:
    """
    Create a standardized success response.

    Args:
        data: Response data (will be JSON serialized)
        status_code: HTTP status code (default 200)

    Returns:
        Azure Functions HTTP response
    """
    return func.HttpResponse(
        json.dumps(data) if not isinstance(data, str) else data, status_code=status_code, mimetype="application/json"
    )


def no_content_response() -> func.HttpResponse:
    """Create a 204 No Content response."""
    return func.HttpResponse(status_code=204)
