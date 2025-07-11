"""
Authentication monitoring middleware for comprehensive tracking and metrics.
Implements monitoring requirements from Apps_Auth_Requirement.md
"""

import logging
import time
from typing import Any, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuthenticationMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor authentication events and performance."""

    def __init__(self, app):
        super().__init__(app)
        self.auth_metrics = {
            "total_requests": 0,
            "authenticated_requests": 0,
            "failed_auth_requests": 0,
            "token_missing_requests": 0,
            "token_invalid_requests": 0,
            "permission_denied_requests": 0,
            "avg_auth_duration": 0.0,
        }

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Check if this is an authenticated endpoint
        is_auth_endpoint = self._is_authenticated_endpoint(request)

        if is_auth_endpoint:
            self.auth_metrics["total_requests"] += 1

            # Check for authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                self.auth_metrics["token_missing_requests"] += 1
                logger.info(
                    "Authentication attempt without token",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "ip": request.client.host if request.client else "unknown",
                        "user_agent": request.headers.get("user-agent", "unknown"),
                    },
                )

        response = await call_next(request)

        if is_auth_endpoint:
            auth_duration = time.time() - start_time
            self._update_auth_metrics(response, auth_duration)

            # Log authentication result
            self._log_auth_result(request, response, auth_duration)

        return response

    def _is_authenticated_endpoint(self, request: Request) -> bool:
        """Check if the endpoint requires authentication."""
        path = request.url.path

        # Skip health checks and public endpoints
        public_endpoints = ["/health", "/docs", "/redoc", "/openapi.json"]

        if any(path.startswith(endpoint) for endpoint in public_endpoints):
            return False

        # Most API endpoints require authentication
        return path.startswith("/api/")

    def _update_auth_metrics(self, response: Response, duration: float):
        """Update authentication metrics based on response."""
        if response.status_code == 200:
            self.auth_metrics["authenticated_requests"] += 1
        elif response.status_code == 401:
            self.auth_metrics["failed_auth_requests"] += 1
            # Check error type from response
            if hasattr(response, "body"):
                try:
                    import json

                    body = json.loads(response.body)
                    error_code = body.get("detail", {}).get("code", "")

                    if error_code == "AUTH_TOKEN_MISSING":
                        # Already counted in dispatch
                        pass
                    elif error_code == "AUTH_TOKEN_INVALID":
                        self.auth_metrics["token_invalid_requests"] += 1
                except Exception:
                    pass
        elif response.status_code == 403:
            self.auth_metrics["permission_denied_requests"] += 1

        # Update average duration
        total_auth_requests = (
            self.auth_metrics["authenticated_requests"]
            + self.auth_metrics["failed_auth_requests"]
        )
        if total_auth_requests > 0:
            current_avg = self.auth_metrics["avg_auth_duration"]
            self.auth_metrics["avg_auth_duration"] = (
                current_avg * (total_auth_requests - 1) + duration
            ) / total_auth_requests

    def _log_auth_result(self, request: Request, response: Response, duration: float):
        """Log authentication result for monitoring."""
        log_data = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "ip": request.client.host if request.client else "unknown",
        }

        if response.status_code == 200:
            logger.info("Authentication successful", extra=log_data)
        elif response.status_code in [401, 403]:
            logger.warning("Authentication failed", extra=log_data)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current authentication metrics."""
        total_requests = self.auth_metrics["total_requests"]
        success_rate = (
            self.auth_metrics["authenticated_requests"] / max(total_requests, 1) * 100
        )

        return {
            **self.auth_metrics,
            "success_rate_percent": round(success_rate, 2),
            "failure_rate_percent": round(100 - success_rate, 2),
        }
