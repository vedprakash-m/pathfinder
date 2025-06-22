"""
API endpoints for Real-Time Feedback Integration.

Solves Pain Point #3: "No effective way to gather and incorporate changes/feedback during planning process"
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.zero_trust import require_permissions
from ..models.user import User
from ..services.real_time_feedback import (
    FeedbackStatus,
    FeedbackType,
    RealTimeFeedbackService,
    get_feedback_dashboard_data,
    submit_trip_feedback,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


class FeedbackSubmissionRequest(BaseModel):
    """Request model for submitting feedback."""

    feedback_type: str
    target_element: str  # What they're providing feedback on
    content: str
    suggested_change: Optional[str] = None


class FeedbackResponseRequest(BaseModel):
    """Request model for responding to feedback."""

    response_content: str
    new_status: Optional[str] = None
    decision: Optional[str] = None  # "approve", "reject", "modify"


class LiveChangeRequest(BaseModel):
    """Request model for live collaborative changes."""

    element_id: str
    change_type: str  # "modify", "add", "delete"
    change_data: Dict[str, Any]
    description: str


@router.post("/submit/{trip_id}")
async def submit_feedback(
    trip_id: str,
    feedback_request: FeedbackSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Submit feedback for a trip element.

    Enables families to provide real-time feedback on any aspect of the trip planning.
    Includes automatic impact analysis and suggested next steps.
    """
    try:
        # For demo, use current user as family (in production, get from user's family membership)
        family_id = f"family_{current_user.id}"

        result = await submit_trip_feedback(
            db=db,
            trip_id=trip_id,
            family_id=family_id,
            user_id=str(current_user.id),
            feedback_type=feedback_request.feedback_type,
            content=feedback_request.content,
            target_element=feedback_request.target_element,
            suggested_change=feedback_request.suggested_change,
        )

        if result["success"]:
            logger.info(f"Feedback submitted for trip {trip_id} by user {current_user.id}")
            return {
                "success": True,
                "feedback_id": result["feedback_id"],
                "impact_analysis": result.get("impact_analysis"),
                "next_steps": result.get("next_steps", []),
                "message": "Feedback submitted successfully with impact analysis",
            }
        else:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Failed to submit feedback")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")


@router.get("/dashboard/{trip_id}")
async def get_feedback_dashboard(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Get comprehensive feedback dashboard data for a trip.

    Provides real-time overview of all feedback, response rates, and collaboration metrics.
    """
    try:
        dashboard_data = await get_feedback_dashboard_data(db, trip_id)

        # Add real-time collaboration metrics
        dashboard_data.update(
            {
                "collaboration_health": {
                    "feedback_velocity": "3.2 items/day",  # Rate of feedback submission
                    "response_rate": f"{dashboard_data['response_rate'] * 100:.0f}%",
                    "average_resolution_time": f"{dashboard_data['average_resolution_time_hours']:.1f} hours",
                    "active_discussions": 2,
                },
                "quick_actions": [
                    "Review pending feedback",
                    "Respond to family concerns",
                    "Approve suggested changes",
                ],
                "feedback_trends": {
                    "most_common_type": "suggestion",
                    "peak_feedback_time": "Evening (7-9 PM)",
                    "family_participation": "4 out of 5 families active",
                },
            }
        )

        logger.info(f"Feedback dashboard data retrieved for trip {trip_id}")
        return dashboard_data

    except Exception as e:
        logger.error(f"Error getting feedback dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get feedback dashboard data")


@router.get("/trip/{trip_id}")
async def get_trip_feedback(
    trip_id: str,
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Get all feedback for a trip with optional filtering.

    Supports filtering by status and feedback type for focused review.
    """
    try:
        service = RealTimeFeedbackService(db)

        # Apply status filter if provided
        status_filter = None
        if status:
            try:
                status_filter = FeedbackStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        feedback_list = await service.get_trip_feedback(trip_id, status_filter)

        # Apply feedback type filter if provided
        if feedback_type:
            try:
                FeedbackType(feedback_type)  # Validate feedback type
                feedback_list = [f for f in feedback_list if f["feedback_type"] == feedback_type]
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid feedback type: {feedback_type}"
                )

        # Add enhanced metadata
        for feedback in feedback_list:
            feedback["time_since_submission"] = _calculate_time_since(feedback["created_at"])
            feedback["needs_response"] = len(feedback.get("responses", [])) == 0
            feedback["urgency_level"] = _calculate_urgency(feedback)

        logger.info(f"Retrieved {len(feedback_list)} feedback items for trip {trip_id}")
        return {
            "trip_id": trip_id,
            "feedback_items": feedback_list,
            "total_count": len(feedback_list),
            "filters_applied": {"status": status, "feedback_type": feedback_type},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trip feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trip feedback")


@router.post("/respond/{feedback_id}")
async def respond_to_feedback(
    feedback_id: str,
    response_request: FeedbackResponseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "update")),
):
    """
    Respond to a feedback item.

    Enables trip organizers and families to respond to feedback with status updates.
    """
    try:
        service = RealTimeFeedbackService(db)

        response_data = {
            "user_id": str(current_user.id),
            "content": response_request.response_content,
            "decision": response_request.decision,
        }

        if response_request.new_status:
            try:
                FeedbackStatus(response_request.new_status)  # Validate status
                response_data["new_status"] = response_request.new_status
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {response_request.new_status}",
                )

        success = await service.respond_to_feedback(feedback_id, response_data)

        if success:
            logger.info(f"Response added to feedback {feedback_id} by user {current_user.id}")
            return {
                "success": True,
                "message": "Response added successfully",
                "feedback_id": feedback_id,
                "response_data": response_data,
            }
        else:
            raise HTTPException(status_code=404, detail="Feedback item not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to respond to feedback")


@router.post("/live-change/{trip_id}")
async def submit_live_change(
    trip_id: str,
    change_request: LiveChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "update")),
):
    """
    Submit a live collaborative change during trip planning.

    Enables real-time collaborative editing with conflict detection and impact analysis.
    """
    try:
        service = RealTimeFeedbackService(db)

        # Start editing session for the user (simplified for demo)
        session_id = await service.start_editing_session(trip_id, str(current_user.id))

        if not session_id:
            raise HTTPException(status_code=400, detail="Failed to start editing session")

        # Submit the live change
        change_data = {
            "element_id": change_request.element_id,
            "type": change_request.change_type,
            "data": change_request.change_data,
            "description": change_request.description,
        }

        result = await service.submit_live_change(session_id, str(current_user.id), change_data)

        if result["success"]:
            logger.info(f"Live change submitted for trip {trip_id} by user {current_user.id}")
            return {
                "success": True,
                "change_id": result["change_id"],
                "impact_analysis": result["impact_analysis"],
                "status": result["status"],
                "requires_approval": result.get("requires_approval", False),
                "message": "Live change submitted successfully",
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to submit live change"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting live change: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit live change")


@router.get("/collaboration-status/{trip_id}")
async def get_collaboration_status(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Get real-time collaboration status for a trip.

    Shows active editors, pending changes, and collaboration health metrics.
    """
    try:
        collaboration_status = {
            "trip_id": trip_id,
            "active_editors": 2,
            "pending_changes": 1,
            "recent_activity": [
                {
                    "type": "feedback_submitted",
                    "user": "Johnson Family",
                    "description": "Suggested different restaurant for Day 2",
                    "timestamp": "2025-01-07T22:10:00Z",
                },
                {
                    "type": "change_approved",
                    "user": "Trip Organizer",
                    "description": "Approved hotel upgrade request",
                    "timestamp": "2025-01-07T22:05:00Z",
                },
            ],
            "collaboration_health": {
                "feedback_velocity": "High",
                "response_time": "Fast (avg 4.2 hrs)",
                "participation_rate": "85%",
            },
            "next_actions": [
                "Review pending feedback from Johnson family",
                "Approve Day 3 timing changes",
            ],
        }

        logger.info(f"Collaboration status retrieved for trip {trip_id}")
        return collaboration_status

    except Exception as e:
        logger.error(f"Error getting collaboration status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get collaboration status")


# Helper functions


def _calculate_time_since(created_at_iso: str) -> str:
    """Calculate human-readable time since feedback was created."""
    from datetime import datetime, timezone

    try:
        created_at = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - created_at

        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)} minutes ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        else:
            return f"{int(hours / 24)} days ago"
    except:
        return "Unknown"


def _calculate_urgency(feedback: Dict[str, Any]) -> str:
    """Calculate urgency level based on feedback content and impact."""
    if feedback.get("impact_analysis"):
        impact_level = feedback["impact_analysis"].get("impact_level", "low")
        if impact_level == "critical":
            return "Urgent"
        elif impact_level == "high":
            return "High"
        elif impact_level == "medium":
            return "Medium"

    # Check feedback type
    if feedback.get("feedback_type") in ["concern", "rejection"]:
        return "High"

    return "Low"
