from __future__ import annotations
"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
Admin endpoints for managing the application.

These endpoints are accessible only to users with administrative privileges.
"""

from app.core.config import get_settings
from app.core.performance import get_performance_metrics
from app.core.security import require_role
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()


class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model."""

timestamp: str
endpoint_average_times: dict
query_average_times: dict
api_request_counts: dict
slowest_queries: list
memory_usage: float
cpu_percent: float


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_app_performance(
    current_user=Depends(require_role("admin")),
):  # noqa: B008
    """
    Get application performance metrics.

    Available only to administrators.
    """
    metrics = await get_performance_metrics()
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Performance metrics not available",
        )

    return metrics


@router.get("/config")
async def get_app_config(current_user=Depends(require_role("admin"))):  # noqa: B008
    """
    Get selected application configuration.

    Available only to administrators. Contains only safe configuration values.
    """
    # Return only safe config values, not sensitive ones like API keys
    safe_config = {
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "cosmos_db_enabled": settings.COSMOS_DB_ENABLED,
        "rate_limit_requests": settings.RATE_LIMIT_REQUESTS,
        "rate_limit_window": settings.RATE_LIMIT_WINDOW,
        "websocket_max_connections": settings.WEBSOCKET_MAX_CONNECTIONS,
        "ai_cost_tracking_enabled": settings.AI_COST_TRACKING_ENABLED,
        "performance_monitoring": {
            "slow_request_threshold": settings.SLOW_REQUEST_THRESHOLD,
            "slow_query_threshold": settings.SLOW_QUERY_THRESHOLD,
            "slow_function_threshold": settings.SLOW_FUNCTION_THRESHOLD,
            "metrics_rollup_interval": settings.METRICS_ROLLUP_INTERVAL,
        },
    }

    return safe_config
