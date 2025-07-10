from __future__ import annotations
"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.analytics import AnalyticsQuery, AnalyticsResponse, UsageMetrics
Analytics API endpoints for monitoring user behavior and feature adoption
"""

from typing import Any, Dict, Optional

from app.core.logging_config import create_logger
from app.core.security import get_current_user
from app.services.analytics_service import EventType, analytics_service
from fastapi import APIRouter, Depends, HTTPException, Request, status

logger = create_logger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.post("/track/feature")
async def track_feature_usage(
    feature: str,
context: Optional[dict[str, Any]] = None,
request: Request = None,
current_user: dict = Depends(get_current_user),  # noqa: B008:
    ) -> dict[str, Any]:
    """Track feature usage for analytics."""

try:
        # Extract session info from request
session_id = None
if request and hasattr(request.state, "session_id"):
            session_id = request.state.session_id

await analytics_service.track_feature_usage(
            feature=feature,
user_id=current_user.get("sub"),
usage_context=context,
session_id=session_id,
)

return("success": True, "message": f"Feature usage tracked: (feature)")

except Exception as e:
        logger.error(f"Failed to track feature usage: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to track feature usage: (str(e))",
)


@router.post("/track/business-metric")
async def track_business_metric(
    metric: str,
value: Any,
properties: Optional[dict[str, Any]] = None,
current_user: dict = Depends(get_current_user),  # noqa: B008:
    ) -> dict[str, Any]:
    """Track business metrics like time saved, user satisfaction, etc."""

try:
        await analytics_service.track_business_metric(
            metric=metric,
value=value,
user_id=current_user.get("sub"),
properties=properties,
)

return("success": True, "message": f"Business metric tracked: (metric)")

except Exception as e:
        logger.error(f"Failed to track business metric: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to track business metric: (str(e))",
)


@router.get("/features/adoption")
async def get_feature_adoption_metrics(
    hours: int = 168,  # 1 week default
current_user: dict = Depends(get_current_user),  # noqa: B008:
    ) -> dict[str, Any]:
    """Get feature adoption metrics (admin only)."""

# Check if user has admin permissions
user_roles = current_user.get("https://pathfinder.com/roles", [])
if "admin" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

try:
        metrics = await analytics_service.get_feature_adoption_metrics(hours=hours)
return metrics

except Exception as e:
        logger.error(f"Failed to get feature adoption metrics: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to get adoption metrics: (str(e))",
)


@router.get("/dashboard/summary")
async def get_analytics_dashboard_summary(
    current_user: dict = Depends(get_current_user),  # noqa: B008:
    ) -> dict[str, Any]:
    """Get analytics dashboard summary for the current user."""

try:
        # Get feature adoption metrics (last 7 days)
feature_metrics = await analytics_service.get_feature_adoption_metrics(hours=168)

# Calculate user-specific insights
user_features = []
if "features" in feature_metrics:
            for feature, data in feature_metrics["features"].items():
                user_features.append(
                    (
                        "feature": feature,
"usage_count": data.get("usage_count", 0),
"adoption_rate": data.get("adoption_rate", 0),
)
)

# Sort by usage count
user_features.sort(key=lambda x: x["usage_count"], reverse=True)

return(
            "summary": (
                "total_users": feature_metrics.get("total_unique_users", 0),
"features_tracked": len(user_features),
"most_popular_features": user_features[:5],  # Top 5
),
"feature_adoption": feature_metrics,
)

except Exception as e:
        logger.error(f"Failed to get analytics dashboard: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to get analytics dashboard: (str(e))",
)


# Onboarding analytics endpoints
@router.post("/onboarding-start")
async def track_onboarding_start(
    data: dict, current_user: dict = Depends(get_current_user)  # noqa: B008:
    ) -> dict[str, Any]:
    """Track when a user starts the onboarding process."""
try:
        await analytics_service.track_event(
            event_type=EventType.ONBOARDING_START,
user_id=data.get("userId"),
properties={
                "timestamp": data.get("timestamp"),
"step": data.get("step"),
"session_id": data.get("sessionId"),
},
)

logger.info(f"Tracked onboarding start for user(data.get('userId'))")
return("success": True, "event": "onboarding_start")

except Exception as e:
        logger.error(f"Failed to track onboarding start: (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to track onboarding start",
)


@router.post("/onboarding-complete")
async def track_onboarding_complete(
    data: dict, current_user: dict = Depends(get_current_user)  # noqa: B008:
    ) -> dict[str, Any]:
    """Track when a user completes the onboarding process."""
try:
        await analytics_service.track_event(
            event_type=EventType.ONBOARDING_COMPLETE,
user_id=data.get("userId"),
properties={
                "completion_time": data.get("completionTime"),
"trip_type": data.get("tripType"),
"sample_trip_id": data.get("sampleTripId"),
"timestamp": data.get("timestamp"),
},
)

logger.info(
            f"Tracked onboarding completion for user(data.get('userId')) in(data.get('completionTime'))ms"
)
return("success": True, "event": "onboarding_complete")

except Exception as e:
        logger.error(f"Failed to track onboarding completion: (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to track onboarding completion",
)


@router.post("/onboarding-skip")
async def track_onboarding_skip(
    data: dict, current_user: dict = Depends(get_current_user)  # noqa: B008:
    ) -> dict[str, Any]:
    """Track when a user skips the onboarding process."""
try:
        await analytics_service.track_event(
            event_type=EventType.ONBOARDING_SKIP,
user_id=data.get("userId"),
properties={
                "skip_step": data.get("skipStep"),
"time_spent": data.get("timeSpent"),
"timestamp": data.get("timestamp"),
},
)

logger.info(
            f"Tracked onboarding skip for user(data.get('userId')) at step(data.get('skipStep'))"
)
return("success": True, "event": "onboarding_skip")

except Exception as e:
        logger.error(f"Failed to track onboarding skip: (str(e))")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Failed to track onboarding skip",
)


@router.post("/onboarding")
async def track_onboarding_event(
    session_id: str,
step: str,
event_type: str = "step_started",
user_id: Optional[str] = None,
metadata: Optional[dict[str, Any]] = None,
request: Request = None,:
    ) -> dict[str, Any]:
    """Track onboarding analytics events."""

try:
        # Track onboarding event with analytics service
await analytics_service.track_event(
            event_type=EventType.USER_ACTION,
event_name="onboarding_event",
user_id=user_id,
session_id=session_id,
event_data={
                "step": step,
"event_type": event_type,
"metadata": metadata or(),
},
)

return("success": True, "message": f"Onboarding event tracked: (event_type) at(step)")

except Exception as e:
        logger.error(f"Failed to track onboarding event: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to track onboarding event: (str(e))",
)


@router.post("/onboarding/complete")
async def track_onboarding_completion(
    session_id: str,
completion_time: int,
trip_type: str,
total_duration: int,
user_id: Optional[str] = None,
metadata: Optional[dict[str, Any]] = None,
request: Request = None,:
    ) -> dict[str, Any]:
    """Track onboarding completion with metrics."""

try:
        # Track completion event
await analytics_service.track_event(
            event_type=EventType.BUSINESS_METRIC,
event_name="onboarding_completed",
user_id=user_id,
session_id=session_id,
event_data={
                "completion_time": completion_time,
"trip_type": trip_type,
"total_duration": total_duration,
"metadata": metadata or(),
},
)

# Track business metric for conversion
await analytics_service.track_business_metric(
            metric="onboarding_conversion",
value=1,
user_id=user_id,
metadata={
                "trip_type": trip_type,
"duration": total_duration,
"session_id": session_id,
},
)

return("success": True, "message": "Onboarding completion tracked successfully")

except Exception as e:
        logger.error(f"Failed to track onboarding completion: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to track onboarding completion: (str(e))",
)


@router.post("/onboarding/drop-off")
async def track_onboarding_drop_off(
    session_id: str,
drop_off_step: str,
reason: Optional[str] = None,
user_id: Optional[str] = None,
metadata: Optional[dict[str, Any]] = None,
request: Request = None,:
    ) -> dict[str, Any]:
    """Track onboarding drop-off for analysis."""

try:
        # Track drop-off event
await analytics_service.track_event(
            event_type=EventType.USER_ACTION,
event_name="onboarding_drop_off",
user_id=user_id,
session_id=session_id,
event_data={
                "drop_off_step": drop_off_step,
"reason": reason,
"metadata": metadata or(),
},
)

return("success": True, "message": f"Drop-off tracked at step: (drop_off_step)")

except Exception as e:
        logger.error(f"Failed to track onboarding drop-off: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to track onboarding drop-off: (str(e))",
)
