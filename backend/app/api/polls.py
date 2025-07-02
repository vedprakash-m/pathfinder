"""
API endpoints for Magic Polls functionality - Unified Cosmos DB Implementation
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..core.ai_cost_management import ai_cost_control
from ..core.database_unified import get_cosmos_repository
from ..core.logging_config import get_logger
from ..core.security import get_current_user
from ..models.ai_integration import PollType
from ..models.user import User
from ..repositories.cosmos_unified import UnifiedCosmosRepository
from ..services.magic_polls import magic_polls_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/polls", tags=["magic-polls"])


class PollOption(BaseModel):
    """Model for poll option"""

    value: str = Field(..., description="The option value")
    label: Optional[str] = Field(None, description="Display label for the option")
    description: Optional[str] = Field(None, description="Optional description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CreatePollRequest(BaseModel):
    """Request model for creating a Magic Poll"""

    trip_id: str = Field(..., description="ID of the trip this poll belongs to")
    title: str = Field(..., min_length=1, max_length=255, description="Poll title")
    description: Optional[str] = Field(None, description="Optional poll description")
    poll_type: str = Field(
        ..., description="Type of poll (destination_choice, activity_preference, etc.)"
    )
    options: List[PollOption] = Field(..., min_items=2, description="Poll options")
    expires_hours: int = Field(72, ge=1, le=168, description="Hours until poll expires (1-168)")


class PollResponse(BaseModel):
    """Model for poll response"""

    choice: str = Field(..., description="Selected choice")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences")
    comments: Optional[str] = Field(None, description="Optional comments")


class SubmitResponseRequest(BaseModel):
    """Request model for submitting poll response"""

    response: PollResponse = Field(..., description="The poll response")


@router.post("")
@ai_cost_control(model="gpt-4", max_tokens=1500)
async def create_poll(
    request: CreatePollRequest,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Create a new Magic Poll using unified Cosmos DB"""
    try:
        # Validate poll type
        valid_poll_types = [pt.value for pt in PollType]
        if request.poll_type not in valid_poll_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid poll type. Must be one of: {', '.join(valid_poll_types)}",
            )

        # Verify user has access to the trip
        trip = await cosmos_repo.get_trip_by_id(request.trip_id)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Check if user is part of trip's family or trip organizer
        user_families = await cosmos_repo.get_user_families(str(current_user.id))
        user_family_ids = [f.id for f in user_families]

        has_access = trip.organizer_user_id == str(current_user.id) or any(
            family_id in trip.participating_family_ids for family_id in user_family_ids
        )

        if not has_access:
            raise HTTPException(status_code=403, detail="No access to this trip")

        # Convert options to dict format
        options_dict = [option.dict() for option in request.options]

        result = await magic_polls_service.create_poll(
            trip_id=request.trip_id,
            creator_id=current_user.id,
            title=request.title,
            poll_type=request.poll_type,
            options=options_dict,
            description=request.description,
            expires_hours=request.expires_hours,
            cosmos_repo=cosmos_repo,
        )

        if result.get("success"):
            return {
                "success": True,
                "data": result["poll"],
                "message": result["message"],
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating poll: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Poll creation error: {str(e)}")


@router.get("/trip/{trip_id}")
async def get_trip_polls(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get all polls for a specific trip using unified Cosmos DB"""
    try:
        polls = await magic_polls_service.get_trip_polls(
            trip_id=trip_id, user_id=current_user.id, cosmos_repo=cosmos_repo
        )

        return {"success": True, "polls": polls, "count": len(polls)}

    except Exception as e:
        logger.error(f"Error getting trip polls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trip polls error: {str(e)}")


@router.get("/{poll_id}")
async def get_poll_details(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get details of a specific poll using unified Cosmos DB"""
    try:
        result = await magic_polls_service.get_poll_results(
            poll_id=poll_id, user_id=current_user.id, cosmos_repo=cosmos_repo
        )

        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "poll": result["poll"],
                    "results": result["results"],
                    "ai_analysis": result["ai_analysis"],
                    "consensus_recommendation": result["consensus_recommendation"],
                },
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Poll not found"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Poll details error: {str(e)}")


@router.post("/{poll_id}/respond")
async def submit_poll_response(
    poll_id: str,
    request: SubmitResponseRequest,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Submit a response to a Magic Poll using unified Cosmos DB"""
    try:
        result = await magic_polls_service.submit_response(
            poll_id=poll_id,
            user_id=current_user.id,
            response_data=request.response.dict(),
            cosmos_repo=cosmos_repo,
        )

        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "poll": result["poll"],
                    "response_count": result["response_count"],
                },
                "message": "Response submitted successfully",
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting poll response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Response error: {str(e)}")


@router.get("/{poll_id}/results")
async def get_poll_results(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get current results of a poll using unified Cosmos DB"""
    try:
        result = await magic_polls_service.get_poll_results(
            poll_id=poll_id, user_id=current_user.id, cosmos_repo=cosmos_repo
        )

        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "results": result["results"],
                    "ai_analysis": result["ai_analysis"],
                    "consensus_recommendation": result["consensus_recommendation"],
                },
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "Poll not found"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Results error: {str(e)}")


@router.put("/{poll_id}/status")
async def update_poll_status(
    poll_id: str,
    status: str = Query(..., description="New poll status (active, completed, cancelled)"),
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Update poll status (only poll creator can do this) using unified Cosmos DB"""
    try:
        # Validate status
        valid_statuses = ["active", "completed", "cancelled"]  # Simplified for now
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        result = await magic_polls_service.update_poll_status(
            poll_id=poll_id,
            user_id=current_user.id,
            new_status=status,
            cosmos_repo=cosmos_repo,
        )

        if result.get("success"):
            return {
                "success": True,
                "data": result["poll"],
                "message": f"Poll status updated to {status}",
            }
        else:
            raise HTTPException(
                status_code=result.get("status_code", 400),
                detail=result.get("error", "Failed to update poll status"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating poll status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status update error: {str(e)}")


@router.get("/types/available")
async def get_available_poll_types():
    """Get available poll types with descriptions"""
    try:
        poll_types = []

        for poll_type in PollType:
            description = {
                PollType.DESTINATION_CHOICE: "Choose between destination options",
                PollType.ACTIVITY_PREFERENCE: "Select preferred activities",
                PollType.BUDGET_RANGE: "Agree on budget range",
                PollType.DATE_SELECTION: "Pick travel dates",
                PollType.ACCOMMODATION_TYPE: "Choose accommodation type",
                PollType.MEAL_PREFERENCE: "Select meal preferences",
                PollType.TRANSPORTATION: "Choose transportation method",
                PollType.CUSTOM: "Custom poll question",
            }.get(poll_type, "Custom poll type")

            poll_types.append(
                {
                    "value": poll_type.value,
                    "label": poll_type.value.replace("_", " ").title(),
                    "description": description,
                }
            )

        return {"success": True, "poll_types": poll_types}

    except Exception as e:
        logger.error(f"Error getting poll types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Poll types error: {str(e)}")


@router.get("/{poll_id}/analytics")
async def get_poll_analytics(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get detailed analytics for a poll (creator only) using unified Cosmos DB"""
    try:
        result = await magic_polls_service.get_poll_analytics(
            poll_id=poll_id,
            user_id=current_user.id,
            cosmos_repo=cosmos_repo,
        )

        if result.get("success"):
            return {"success": True, "analytics": result["analytics"]}
        else:
            raise HTTPException(
                status_code=result.get("status_code", 404),
                detail=result.get("error", "Analytics not found"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting poll analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/health")
async def polls_health():
    """Health check for Magic Polls service"""
    return {
        "success": True,
        "service": "Magic Polls",
        "status": "healthy",
        "features": [
            "AI-enhanced poll creation",
            "intelligent preference aggregation",
            "consensus recommendation",
            "conflict resolution",
            "real-time analytics",
        ],
    }
