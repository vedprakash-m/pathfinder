"""
Analytics API endpoints for tracking user interactions and business metrics.
Provides comprehensive analytics functionality for the Pathfinder application.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.security import get_current_user
from app.services.analytics_service import AnalyticsService, EventType

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize analytics service
analytics_service = AnalyticsService()


@router.post("/onboarding-complete")
async def track_onboarding_completion(
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
            detail=f"Failed to track onboarding completion: {str(e)}",
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
            detail=f"Failed to track onboarding skip: {str(e)}",
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for analytics service."""
    return {"status": "healthy", "service": "analytics"}
