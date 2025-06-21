"""
Rate limiting middleware for FastAPI.

This module provides middleware for API rate limiting to prevent abuse.
"""

import time
from typing import Dict, Optional, Tuple, Callable
import logging
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# Simple in-memory store for rate limiting
# In production, use Redis or another distributed cache
class RateLimitStore:
    def __init__(self, window_size: int = 60):
        self.window_size = window_size  # seconds
        self._store: Dict[str, Dict[str, float]] = {}
        self._last_cleanup = time.time()

    def add_request(self, key: str, endpoint: str) -> Tuple[int, int]:
        """
        Add a request to the store and return current request count and limit
        """
        now = time.time()

        # Clean up old entries periodically
        if now - self._last_cleanup > 60:
            self._cleanup()
            self._last_cleanup = now

        if key not in self._store:
            self._store[key] = {}

        # Remove old requests outside the window
        self._store[key] = {
            req_time: ts for req_time, ts in self._store[key].items() if now - ts < self.window_size
        }

        # Add current request
        request_id = f"{endpoint}_{now}"
        self._store[key][request_id] = now

        # Count requests in window
        count = len(self._store[key])

        return count

    def _cleanup(self):
        """Clean up old entries"""
        now = time.time()
        for key in list(self._store.keys()):
            self._store[key] = {
                req_id: ts for req_id, ts in self._store[key].items() if now - ts < self.window_size
            }

            # Remove empty entries
            if not self._store[key]:
                del self._store[key]


class RateLimiter(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        window_size: int = 60,
        default_limit: int = 100,
        api_limit: int = 1000,
        public_limit: int = 50,
        get_key: Optional[Callable[[Request], str]] = None,
        endpoint_limits: Optional[Dict[str, int]] = None,
    ):
        super().__init__(app)
        self.store = RateLimitStore(window_size)
        self.window_size = window_size
        self.default_limit = default_limit
        self.api_limit = api_limit
        self.public_limit = public_limit
        self.get_key = get_key or self._default_get_key
        self.endpoint_limits = endpoint_limits or {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for certain paths
        if self._should_skip(request):
            return await call_next(request)

        # Get client identifier
        client_key = await self.get_key(request)
        endpoint = self._get_endpoint_key(request)

        # Get limits based on path
        limit = self._get_limit(request)

        # Record request and check limits
        count = self.store.add_request(client_key, endpoint)

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - count)),
            "X-RateLimit-Reset": str(int(time.time() + self.window_size)),
        }

        # Check if rate limit exceeded
        if count > limit:
            logger.warning(f"Rate limit exceeded for {client_key} on {endpoint}: {count}/{limit}")

            # Add retry-after header
            headers["Retry-After"] = str(self.window_size)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for name, value in headers.items():
            response.headers[name] = value

        return response

    def _should_skip(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request"""
        # Skip rate limiting in testing environment
        from app.core.config import settings

        if settings.ENVIRONMENT == "testing":
            return True

        # Skip health checks and static files
        if request.url.path.startswith(("/health", "/static")):
            return True

        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return True

        # Skip for test client requests
        if (
            hasattr(request, "client")
            and request.client
            and (request.client.host in ("testclient", "testserver", "127.0.0.1"))
        ):
            return True

        return False

    async def _default_get_key(self, request: Request) -> str:
        """Default function to get client key for rate limiting"""
        # Try to get authenticated user ID
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state, "user", {}).get("id")

        # Use user ID if available, otherwise IP address
        if user_id:
            return f"user:{user_id}"

        # Get client IP, considering forwarded headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get first IP in case of multiple proxies
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host

        return f"ip:{client_ip}"

    def _get_endpoint_key(self, request: Request) -> str:
        """Get a key for the endpoint being requested"""
        return f"{request.method}:{request.url.path}"

    def _get_limit(self, request: Request) -> int:
        """Determine the rate limit for this request"""
        # Check for specific endpoint limits
        endpoint_key = self._get_endpoint_key(request)
        if endpoint_key in self.endpoint_limits:
            return self.endpoint_limits[endpoint_key]

        # Authenticated vs public endpoints
        is_authenticated = hasattr(request.state, "user")

        # API vs UI endpoints
        if request.url.path.startswith("/api/"):
            return self.api_limit if is_authenticated else self.public_limit

        return self.default_limit if is_authenticated else self.public_limit
