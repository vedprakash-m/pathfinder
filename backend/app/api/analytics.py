"""
Analytics API endpoints for monitoring user behavior and feature adoption
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.core.security import get_current_user
from app.core.logging_config import create_logger
from app.services.analytics_service import analytics_service, EventType

logger = create_logger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.post("/track/feature")
async def track_feature_usage(
    feature: str,
    context: Optional[Dict[str, Any]] = None,
    request: Request = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
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

        return {"success": True, "message": f"Feature usage tracked: {feature}"}

    except Exception as e:
        logger.error(f"Failed to track feature usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track feature usage: {str(e)}",
        )


@router.post("/track/business-metric")
async def track_business_metric(
    metric: str,
    value: Any,
    properties: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Track business metrics like time saved, user satisfaction, etc."""

    try:
        await analytics_service.track_business_metric(
            metric=metric, value=value, user_id=current_user.get("sub"), properties=properties
        )

        return {"success": True, "message": f"Business metric tracked: {metric}"}

    except Exception as e:
        logger.error(f"Failed to track business metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track business metric: {str(e)}",
        )


@router.get("/features/adoption")
async def get_feature_adoption_metrics(
    hours: int = 168,  # 1 week default
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get feature adoption metrics (admin only)."""

    # Check if user has admin permissions
    user_roles = current_user.get("https://pathfinder.com/roles", [])
    if "admin" not in user_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    try:
        metrics = await analytics_service.get_feature_adoption_metrics(hours=hours)
        return metrics

    except Exception as e:
        logger.error(f"Failed to get feature adoption metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get adoption metrics: {str(e)}",
        )


@router.get("/dashboard/summary")
async def get_analytics_dashboard_summary(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics dashboard summary for the current user."""

    try:
        # Get feature adoption metrics (last 7 days)
        feature_metrics = await analytics_service.get_feature_adoption_metrics(hours=168)

        # Calculate user-specific insights
        user_features = []
        if "features" in feature_metrics:
            for feature, data in feature_metrics["features"].items():
                user_features.append(
                    {
                        "feature": feature,
                        "usage_count": data.get("usage_count", 0),
                        "adoption_rate": data.get("adoption_rate", 0),
                    }
                )

        # Sort by usage count
        user_features.sort(key=lambda x: x["usage_count"], reverse=True)

        return {
            "summary": {
                "total_users": feature_metrics.get("total_unique_users", 0),
                "features_tracked": len(user_features),
                "most_popular_features": user_features[:5],  # Top 5
            },
            "feature_adoption": feature_metrics,
        }

    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics dashboard: {str(e)}",
        )


# Onboarding analytics endpoints
@router.post("/onboarding-start")
async def track_onboarding_start(
    data: dict, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
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

        logger.info(f"Tracked onboarding start for user {data.get('userId')}")
        return {"success": True, "event": "onboarding_start"}

    except Exception as e:
        logger.error(f"Failed to track onboarding start: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track onboarding start",
        )


@router.post("/onboarding-complete")
async def track_onboarding_complete(
    data: dict, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
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
            f"Tracked onboarding completion for user {data.get('userId')} in {data.get('completionTime')}ms"
        )
        return {"success": True, "event": "onboarding_complete"}

    except Exception as e:
        logger.error(f"Failed to track onboarding completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track onboarding completion",
        )


@router.post("/onboarding-skip")
async def track_onboarding_skip(
    data: dict, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
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
            f"Tracked onboarding skip for user {data.get('userId')} at step {data.get('skipStep')}"
        )
        return {"success": True, "event": "onboarding_skip"}

    except Exception as e:
        logger.error(f"Failed to track onboarding skip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track onboarding skip",
        )
