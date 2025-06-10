"""
API endpoints for Magic Polls functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.services.magic_polls import magic_polls_service
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.ai_integration import PollType
import logging

logger = logging.getLogger(__name__)

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
    poll_type: str = Field(..., description="Type of poll (destination_choice, activity_preference, etc.)")
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
async def create_poll(
    request: CreatePollRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Magic Poll"""
    try:
        # Validate poll type
        valid_poll_types = [pt.value for pt in PollType]
        if request.poll_type not in valid_poll_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid poll type. Must be one of: {', '.join(valid_poll_types)}"
            )
        
        # TODO: Verify user has access to the trip
        # This would involve checking if user is part of the trip or family
        
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
            db=db
        )
        
        if result.get("success"):
            return {
                "success": True,
                "data": result["poll"],
                "message": result["message"]
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
    db: Session = Depends(get_db)
):
    """Get all polls for a specific trip"""
    try:
        polls = await magic_polls_service.get_trip_polls(
            trip_id=trip_id,
            user_id=current_user.id,
            db=db
        )
        
        return {
            "success": True,
            "polls": polls,
            "count": len(polls)
        }
        
    except Exception as e:
        logger.error(f"Error getting trip polls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trip polls error: {str(e)}")


@router.get("/{poll_id}")
async def get_poll_details(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific poll"""
    try:
        result = await magic_polls_service.get_poll_results(
            poll_id=poll_id,
            user_id=current_user.id,
            db=db
        )
        
        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "poll": result["poll"],
                    "results": result["results"],
                    "ai_analysis": result["ai_analysis"],
                    "consensus_recommendation": result["consensus_recommendation"]
                }
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
    db: Session = Depends(get_db)
):
    """Submit a response to a Magic Poll"""
    try:
        result = await magic_polls_service.submit_response(
            poll_id=poll_id,
            user_id=current_user.id,
            response_data=request.response.dict(),
            db=db
        )
        
        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "poll": result["poll"],
                    "response_count": result["response_count"]
                },
                "message": "Response submitted successfully"
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
    db: Session = Depends(get_db)
):
    """Get current results of a poll"""
    try:
        result = await magic_polls_service.get_poll_results(
            poll_id=poll_id,
            user_id=current_user.id,
            db=db
        )
        
        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "results": result["results"],
                    "ai_analysis": result["ai_analysis"],
                    "consensus_recommendation": result["consensus_recommendation"]
                }
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
    db: Session = Depends(get_db)
):
    """Update poll status (only poll creator can do this)"""
    try:
        from app.models.ai_integration import MagicPoll, PollStatus
        
        # Validate status
        valid_statuses = [ps.value for ps in PollStatus]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get poll and verify ownership
        poll = db.query(MagicPoll).filter(MagicPoll.id == poll_id).first()
        
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        if poll.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only poll creator can update status")
        
        poll.status = status
        poll.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "data": poll.to_dict(),
            "message": f"Poll status updated to {status}"
        }
        
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
                PollType.CUSTOM: "Custom poll question"
            }.get(poll_type, "Custom poll type")
            
            poll_types.append({
                "value": poll_type.value,
                "label": poll_type.value.replace("_", " ").title(),
                "description": description
            })
        
        return {
            "success": True,
            "poll_types": poll_types
        }
        
    except Exception as e:
        logger.error(f"Error getting poll types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Poll types error: {str(e)}")


@router.get("/{poll_id}/analytics")
async def get_poll_analytics(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a poll (creator only)"""
    try:
        from app.models.ai_integration import MagicPoll
        
        # Get poll and verify ownership
        poll = db.query(MagicPoll).filter(MagicPoll.id == poll_id).first()
        
        if not poll:
            raise HTTPException(status_code=404, detail="Poll not found")
        
        if poll.creator_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only poll creator can view analytics")
        
        # Get detailed analytics
        responses = poll.responses.get("user_responses", []) if poll.responses else []
        
        analytics = {
            "total_responses": len(responses),
            "response_rate": len(responses),  # Would calculate based on invited users
            "time_to_respond": [],  # Average time from poll creation to response
            "consensus_metrics": {
                "consensus_level": poll.ai_analysis.get("consensus_level", 0) if poll.ai_analysis else 0,
                "conflicts_identified": len(poll.ai_analysis.get("conflicts", [])) if poll.ai_analysis else 0,
                "patterns_found": len(poll.ai_analysis.get("patterns", [])) if poll.ai_analysis else 0
            },
            "response_timeline": [
                {
                    "timestamp": response.get("timestamp"),
                    "user_id": response.get("user_id")[:8] + "...",  # Anonymized
                    "choice": response.get("response", {}).get("choice")
                }
                for response in responses
            ]
        }
        
        return {
            "success": True,
            "analytics": analytics
        }
        
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
            "real-time analytics"
        ]
    }
