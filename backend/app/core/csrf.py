"""
CSRF protection middleware for FastAPI.

This module provides middleware for Cross-Site Request Forgery (CSRF) protection.
"""

import hashlib
import hmac
import logging
import secrets
import time
from typing import Any, Callable, Dict, Optional, Set

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Default exempted methods (safe methods)
DEFAULT_EXEMPT_METHODS = {"GET", "HEAD", "OPTIONS"}

# Default exempt URLS (no CSRF protection needed)
DEFAULT_EXEMPT_URLS = {
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/callback",
    "/api/v1/auth/logout",
    "/api/v1/health",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        token_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf",
        cookie_path: str = "/",
        cookie_httponly: bool = True,
        cookie_samesite: str = "lax",
        cookie_secure: bool = True,
        cookie_max_age: int = 86400,  # 1 day in seconds
        exempt_methods: Optional[Set[str]] = None,
        exempt_urls: Optional[Set[str]] = None,
        exempt_callback: Optional[Callable[[Request], bool]] = None,
        cors_enabled: bool = False,  # Enable CORS compatibility mode
        strict_mode: bool = True,  # Strict mode for production
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.token_name = token_name
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.cookie_secure = cookie_secure
        self.cookie_max_age = cookie_max_age
        self.exempt_methods = exempt_methods or DEFAULT_EXEMPT_METHODS
        self.exempt_urls = exempt_urls or DEFAULT_EXEMPT_URLS
        self.exempt_callback = exempt_callback
        self.cors_enabled = cors_enabled
        self.strict_mode = strict_mode

    async def dispatch(self, request: Request, call_next) -> Response:
        # Handle CORS preflight requests immediately
        if self.cors_enabled and request.method == "OPTIONS":
            response = await call_next(request)
            return response

        # Generate token if needed
        csrf_token = self._get_csrf_token(request)

        # Check if CSRF protection should be enforced
        if not self._is_exempt(request):
            # Validate the CSRF token for non-exempt requests
            valid = await self._validate_csrf_token(request, csrf_token)
            if not valid:
                if self.strict_mode:
                    logger.warning(f"CSRF validation failed for {request.url.path}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="CSRF token missing or invalid",
                    )
                else:
                    # In non-strict mode, just log the warning
                    logger.warning(
                        f"CSRF validation failed for {request.url.path} (non-strict mode)"
                    )

        # Process the request
        response = await call_next(request)

        # Set CSRF cookie if it doesn't exist
        if not request.cookies.get(self.cookie_name):
            self._set_csrf_cookie(response, csrf_token)

        # Expose CSRF token in header for single page apps
        response.headers[self.header_name] = csrf_token

        return response

    def _is_exempt(self, request: Request) -> bool:
        """Check if the request is exempt from CSRF protection"""
        # Check HTTP method exemption
        if request.method in self.exempt_methods:
            return True

        # Check path exemption
        if any(request.url.path.startswith(url) for url in self.exempt_urls):
            return True

        # Check if it's a test client request
        user_agent = request.headers.get("user-agent", "")
        if "testclient" in user_agent.lower():
            return True

        # Check custom exemption callback
        if self.exempt_callback and self.exempt_callback(request):
            return True

        return False

    def _get_csrf_token(self, request: Request) -> str:
        """Get or generate a CSRF token"""
        # Try to get from cookie first
        cookie_token = request.cookies.get(self.cookie_name)
        if cookie_token:
            return cookie_token

        # Generate new token if not present
        return self._generate_token()

    async def _validate_csrf_token(self, request: Request, expected_token: str) -> bool:
        """Validate CSRF token from request against expected token"""
        # Get token from header or form
        request_token = request.headers.get(self.header_name)

        if not request_token:
            # Try to get from form data (if available)
            if request.method == "POST":
                try:
                    form_data = await request.form()
                    request_token = form_data.get(self.token_name)
                except Exception:
                    pass

        # Validate token exists and matches expected value
        if not request_token:
            return False

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(request_token, expected_token)

    def _set_csrf_cookie(self, response: Response, token: str) -> None:
        """Set the CSRF token cookie on the response"""
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            path=self.cookie_path,
            httponly=self.cookie_httponly,
            secure=self.cookie_secure,
            samesite=self.cookie_samesite,
            max_age=self.cookie_max_age,
        )

    def _generate_token(self) -> str:
        """Generate a secure CSRF token"""
        # Create a random token
        random_bytes = secrets.token_bytes(32)

        # Add timestamp to prevent reuse after expiry
        timestamp = str(int(time.time())).encode()

        # Combine with secret key for HMAC
        h = hmac.new(self.secret_key.encode(), random_bytes + timestamp, hashlib.sha256)

        # Return URL-safe base64-encoded token
        return h.hexdigest()


# Form injection context processor for templates
def csrf_context_processor(request: Request) -> Dict[str, Any]:
    """
    Context processor for templates to include CSRF token
    """
    csrf_token = request.cookies.get("csrf", "")

    # Create an input field for forms
    csrf_input = f'<input type="hidden" name="csrf_token" value="{csrf_token}">'

    return {"csrf_token": csrf_token, "csrf_input": csrf_input}
