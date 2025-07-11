"""
AI Cost Management Middleware for Pathfinder
Implements cost controls, monitoring, and graceful degradation for AI services.
"""

import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional

from app.core.config import get_settings
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

settings = get_settings()
logger = logging.getLogger(__name__)


class AIUsageTracker:
    """Track AI usage and costs across the application."""

    def __init__(self):
        self.usage_data = {}
        self.cost_thresholds = {
            "daily_limit": 50.0,  # $50 daily limit
            "user_limit": 10.0,  # $10 per user daily
            "request_limit": 2.0,  # $2 per request
        }
        self.model_costs = {
            "gpt-4": 0.03,  # $0.03 per 1K tokens
            "gpt-3.5-turbo": 0.002,  # $0.002 per 1K tokens
            "claude-3": 0.025,  # $0.025 per 1K tokens
        }

    def track_usage(
        self, user_id: str, endpoint: str, model: str, tokens: int
    ) -> Dict[str, Any]:
        """Track AI usage and calculate costs."""
        cost = (tokens / 1000) * self.model_costs.get(model, 0.01)

        today = datetime.now().date().isoformat()

        if today not in self.usage_data:
            self.usage_data[today] = {}

        if user_id not in self.usage_data[today]:
            self.usage_data[today][user_id] = {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0,
                "endpoints": {},
            }

        user_data = self.usage_data[today][user_id]
        user_data["requests"] += 1
        user_data["tokens"] += tokens
        user_data["cost"] += cost

        if endpoint not in user_data["endpoints"]:
            user_data["endpoints"][endpoint] = {"requests": 0, "cost": 0.0}

        user_data["endpoints"][endpoint]["requests"] += 1
        user_data["endpoints"][endpoint]["cost"] += cost

        return {
            "user_daily_cost": user_data["cost"],
            "request_cost": cost,
            "total_daily_cost": sum(
                user["cost"] for user in self.usage_data[today].values()
            ),
            "within_limits": self._check_limits(user_data["cost"], cost),
        }

    def _check_limits(
        self, user_daily_cost: float, request_cost: float
    ) -> Dict[str, bool]:
        """Check if usage is within cost limits."""
        today = datetime.now().date().isoformat()
        total_daily_cost = sum(
            user["cost"] for user in self.usage_data.get(today, {}).values()
        )

        return {
            "user_within_limit": user_daily_cost <= self.cost_thresholds["user_limit"],
            "request_within_limit": request_cost
            <= self.cost_thresholds["request_limit"],
            "daily_within_limit": total_daily_cost
            <= self.cost_thresholds["daily_limit"],
        }

    def get_usage_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage statistics."""
        today = datetime.now().date().isoformat()
        today_data = self.usage_data.get(today, {})

        if user_id and user_id in today_data:
            return {
                "user_stats": today_data[user_id],
                "limits": self.cost_thresholds,
                "remaining": {
                    "user_budget": max(
                        0,
                        self.cost_thresholds["user_limit"]
                        - today_data[user_id]["cost"],
                    )
                },
            }

        total_cost = sum(user["cost"] for user in today_data.values())
        return {
            "daily_stats": {
                "total_cost": total_cost,
                "total_requests": sum(user["requests"] for user in today_data.values()),
                "active_users": len(today_data),
            },
            "limits": self.cost_thresholds,
            "remaining": {
                "daily_budget": max(0, self.cost_thresholds["daily_limit"] - total_cost)
            },
        }


# Global usage tracker instance
usage_tracker = AIUsageTracker()


class AICostManagementMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce AI cost controls and monitoring."""

    def __init__(self, app, ai_endpoints: list = None):
        super().__init__(app)
        self.ai_endpoints = ai_endpoints or [
            "/api/assistant",
            "/api/polls",
            "/api/consensus",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with AI cost controls."""

        # Check if this is an AI endpoint
        if not any(endpoint in str(request.url) for endpoint in self.ai_endpoints):
            return await call_next(request)

        # Get user information
        user_id = getattr(request.state, "user_id", "anonymous")

        # Check cost limits before processing
        usage_stats = usage_tracker.get_usage_stats(user_id)

        if user_id != "anonymous" and "user_stats" in usage_stats:
            user_remaining = usage_stats["remaining"]["user_budget"]
            if user_remaining <= 0:
                logger.warning(f"User {user_id} exceeded daily AI budget")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "AI_BUDGET_EXCEEDED",
                        "message": "Daily AI usage budget exceeded. Please try again tomorrow.",
                        "remaining_budget": 0,
                        "reset_time": self._get_reset_time(),
                    },
                )

        # Check daily limits
        daily_remaining = usage_stats["remaining"]["daily_budget"]
        if daily_remaining <= 0:
            logger.warning("Daily AI budget exceeded for entire application")
            # Return graceful degradation response
            return self._graceful_degradation_response()

        # Process the request
        start_time = time.time()
        response = await call_next(request)
        processing_time = time.time() - start_time

        # Log AI usage for monitoring
        logger.info(
            f"AI request processed: {request.url} - User: {user_id} - Time: {processing_time:.2f}s"
        )

        return response

    def _get_reset_time(self) -> str:
        """Get the time when daily limits reset."""
        tomorrow = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        return tomorrow.isoformat()

    def _graceful_degradation_response(self) -> Response:
        """Return a graceful degradation response when AI budget is exceeded."""
        from starlette.responses import JSONResponse

        return JSONResponse(
            status_code=503,
            content={
                "error": "AI_SERVICE_UNAVAILABLE",
                "message": "AI services are temporarily unavailable due to budget limits. Basic functionality remains available.",
                "fallback_suggestions": [
                    "Try using manual trip planning features",
                    "Access saved trip templates",
                    "Use collaborative planning without AI assistance",
                ],
                "retry_after": self._get_reset_time(),
            },
        )


def ai_cost_control(model: str = "gpt-3.5-turbo", max_tokens: int = 1000):
    """Decorator for AI endpoint functions to enforce cost controls."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user information from kwargs
            user_id = "anonymous"
            if "current_user" in kwargs:
                user_data = kwargs["current_user"]
                user_id = (
                    user_data.get("id", "anonymous")
                    if isinstance(user_data, dict)
                    else getattr(user_data, "id", "anonymous")
                )

            # Pre-flight cost check
            estimated_cost = (max_tokens / 1000) * usage_tracker.model_costs.get(
                model, 0.01
            )
            usage_stats = usage_tracker.get_usage_stats(user_id)

            if user_id != "anonymous" and "remaining" in usage_stats:
                # Check if user_budget exists in remaining stats
                remaining = usage_stats["remaining"]
                user_budget = remaining.get(
                    "user_budget", remaining.get("daily_budget", 10.0)
                )  # fallback to daily or default

                if user_budget < estimated_cost:
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "INSUFFICIENT_AI_BUDGET",
                            "message": "Insufficient AI budget for this request",
                            "required": estimated_cost,
                            "available": user_budget,
                        },
                    )

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Track actual usage (would need to be implemented based on actual AI response)
                actual_tokens = getattr(result, "usage", {}).get(
                    "total_tokens", max_tokens // 2
                )
                endpoint = func.__name__

                tracking_result = usage_tracker.track_usage(
                    user_id, endpoint, model, actual_tokens
                )

                # Add usage information to response
                if isinstance(result, dict):
                    result["ai_usage"] = {
                        "cost": tracking_result["request_cost"],
                        "remaining_budget": usage_stats.get("remaining", {}).get(
                            "user_budget",
                            usage_stats.get("remaining", {}).get("daily_budget", 0),
                        ),
                        "tokens_used": actual_tokens,
                    }

                return result

            except Exception as e:
                logger.error(f"AI endpoint error in {func.__name__}: {str(e)}")

                # Return graceful degradation for AI errors
                if "AI" in str(e).upper() or "MODEL" in str(e).upper():
                    return {
                        "error": "AI_SERVICE_ERROR",
                        "message": "AI service temporarily unavailable. Please try again later.",
                        "fallback_available": True,
                    }

                raise e

        return wrapper

    return decorator


def get_ai_usage_stats(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get AI usage statistics for monitoring."""
    return usage_tracker.get_usage_stats(user_id)


def reset_daily_usage():
    """Reset daily usage counters (called by scheduled task)."""
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    if yesterday in usage_tracker.usage_data:
        del usage_tracker.usage_data[yesterday]
        logger.info(f"Reset AI usage data for {yesterday}")


class AICostTracker:
    """
    Advanced AI cost tracking with budget validation and graceful degradation.
    This class provides the interface expected by validation scripts and external systems.
    """

    def __init__(self):
        self.usage_tracker = usage_tracker
        self.model_costs = {
            "gpt-4o": 0.03,  # $0.03 per 1K tokens
            "gpt-4o-mini": 0.001,  # $0.001 per 1K tokens
            "gpt-3.5-turbo": 0.002,  # $0.002 per 1K tokens
        }
        self.budget_limits = {"daily": 50.0, "user": 10.0, "request": 2.0}

    def validate_request_budget(self, model: str, estimated_tokens: int) -> bool:
        """Validate if a request is within budget limits."""
        estimated_cost = (estimated_tokens / 1000) * self.model_costs.get(model, 0.01)

        # Check if request cost exceeds per-request limit
        if estimated_cost > self.budget_limits["request"]:
            return False

        # Check daily and user limits
        usage_stats = self.usage_tracker.get_usage_stats()
        daily_remaining = usage_stats.get("remaining", {}).get("daily_budget", 0)

        return daily_remaining >= estimated_cost

    def track_request(
        self, user_id: str, endpoint: str, model: str, tokens: int
    ) -> Dict[str, Any]:
        """Track an AI request and return usage metrics."""
        return self.usage_tracker.track_usage(user_id, endpoint, model, tokens)

    def get_budget_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current budget status for user or system."""
        return self.usage_tracker.get_usage_stats(user_id)

    def is_budget_exceeded(self, user_id: Optional[str] = None) -> bool:
        """Check if budget limits have been exceeded."""
        stats = self.get_budget_status(user_id)
        if user_id and "user_stats" in stats:
            return stats["user_stats"]["cost"] >= self.budget_limits["user"]

        daily_stats = stats.get("daily_stats", {})
        return daily_stats.get("total_cost", 0) >= self.budget_limits["daily"]

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Get detailed cost breakdown for monitoring."""
        today = datetime.now().date().isoformat()
        today_data = self.usage_tracker.usage_data.get(today, {})

        total_cost = sum(user["cost"] for user in today_data.values())
        total_requests = sum(user["requests"] for user in today_data.values())

        # Calculate cost by endpoint
        endpoint_costs = {}
        for user_data in today_data.values():
            for endpoint, endpoint_data in user_data.get("endpoints", {}).items():
                if endpoint not in endpoint_costs:
                    endpoint_costs[endpoint] = {"cost": 0, "requests": 0}
                endpoint_costs[endpoint]["cost"] += endpoint_data["cost"]
                endpoint_costs[endpoint]["requests"] += endpoint_data["requests"]

        return {
            "daily_total": total_cost,
            "daily_requests": total_requests,
            "daily_limit": self.budget_limits["daily"],
            "remaining_budget": max(0, self.budget_limits["daily"] - total_cost),
            "endpoint_breakdown": endpoint_costs,
            "active_users": len(today_data),
            "average_cost_per_request": total_cost / max(1, total_requests),
        }


# Create global AICostTracker instance for compatibility
ai_cost_tracker = AICostTracker()


# Export the middleware and utilities
__all__ = [
    "AICostManagementMiddleware",
    "ai_cost_control",
    "get_ai_usage_stats",
    "reset_daily_usage",
    "usage_tracker",
    "AICostTracker",
    "ai_cost_tracker",
]
