"""
Security Headers Middleware for Pathfinder.
Implements comprehensive security headers per Apps_Auth_Requirement.md.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware implementing production security standards.

    Implements all required security headers:
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - Permissions-Policy
    - Referrer-Policy
    """

    def __init__(self, app, csp_policy: str = None):
        super().__init__(app)
        self.csp_policy = csp_policy or self._get_default_csp()

    def _get_default_csp(self) -> str:
        """Get default Content Security Policy for Pathfinder."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://login.microsoftonline.com "
            "https://graph.microsoft.com "
            "https://js.monitor.azure.com "
            "https://az416426.vo.msecnd.net; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; "
            "font-src 'self' "
            "https://fonts.gstatic.com; "
            "img-src 'self' data: "
            "https://graph.microsoft.com "
            "https://login.microsoftonline.com "
            "https://*.tile.openstreetmap.org; "
            "connect-src 'self' "
            "https://login.microsoftonline.com "
            "https://graph.microsoft.com "
            "https://pathfinder-api.vedprakash.net "
            "wss://pathfinder-api.vedprakash.net "
            "https://js.monitor.azure.com; "
            "frame-src 'self' "
            "https://login.microsoftonline.com; "
            "worker-src 'self' blob:; "
            "child-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self' "
            "https://login.microsoftonline.com; "
            "frame-ancestors 'self'; "
            "upgrade-insecure-requests"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply security headers to all responses."""
        try:
            response = await call_next(request)

            # Apply security headers
            self._apply_security_headers(response, request)

            # Log security header application for monitoring
            logger.debug(f"Security headers applied to {request.method} {request.url.path}")

            return response

        except Exception as e:
            logger.error(f"Security headers middleware error: {e}")
            # Return a secure error response
            return self._create_secure_error_response()

    def _apply_security_headers(self, response: Response, request: Request) -> None:
        """Apply all required security headers to the response."""

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # HTTP Strict Transport Security (HSTS)
        # Only apply in production over HTTPS
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # X-Frame-Options - Prevent clickjacking
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # X-Content-Type-Options - Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection - Enable XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (Feature Policy replacement)
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(self), "
            "payment=(), "
            "usb=(), "
            "bluetooth=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "clipboard-write=(self)"
        )

        # Cross-Origin Resource Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"

        # Cross-Origin Embedder Policy
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Cross-Origin Opener Policy
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # Server header removal for security
        response.headers.pop("Server", None)

        # Cache control for sensitive pages
        if self._is_sensitive_path(request.url.path):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

    def _is_sensitive_path(self, path: str) -> bool:
        """Check if the path contains sensitive information."""
        sensitive_paths = ["/api/auth/", "/api/me", "/api/admin/", "/api/families/", "/api/trips/"]
        return any(path.startswith(sensitive) for sensitive in sensitive_paths)

    def _create_secure_error_response(self) -> JSONResponse:
        """Create a secure error response with proper headers."""
        response = JSONResponse(status_code=500, content={"error": "Internal server error"})

        # Apply minimal security headers even for error responses
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cache-Control"] = "no-store"

        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    CORS middleware with security considerations.
    Implements secure CORS policy for cross-domain requests.
    """

    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or [
            "https://pathfinder.vedprakash.net",
            "https://pathfinder-staging.vedprakash.net",
            "http://localhost:3000",  # Development only
            "http://localhost:5173",  # Vite dev server
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply CORS headers with security validation."""
        origin = request.headers.get("origin")

        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)

        # Apply CORS headers only for allowed origins
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With, Accept, "
                "Cache-Control, Pragma, X-CSRFToken"
            )
            response.headers["Access-Control-Max-Age"] = "3600"

        return response

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if the origin is in the allowed list."""
        return origin in self.allowed_origins


def setup_security_middleware(app):
    """Setup all security middleware for the application."""

    # Add CORS middleware first
    app.add_middleware(CORSSecurityMiddleware)

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    logger.info("Security middleware configured successfully")

    return app


# Security monitoring functions
def get_security_metrics() -> dict:
    """Get security-related metrics for monitoring."""
    return {
        "security_headers_enabled": True,
        "csp_policy_active": True,
        "hsts_enabled": True,
        "cors_configured": True,
        "sensitive_path_protection": True,
    }


def validate_security_configuration() -> bool:
    """Validate that all security configurations are properly set."""
    try:
        # Check if all required security components are available
        middleware = SecurityHeadersMiddleware(app=None)
        csp_policy = middleware._get_default_csp()

        # Validate CSP policy has required directives
        required_directives = [
            "default-src",
            "script-src",
            "style-src",
            "img-src",
            "connect-src",
            "frame-src",
            "object-src",
            "base-uri",
        ]

        for directive in required_directives:
            if directive not in csp_policy:
                logger.error(f"Missing CSP directive: {directive}")
                return False

        logger.info("Security configuration validation passed")
        return True

    except Exception as e:
        logger.error(f"Security configuration validation failed: {e}")
        return False
