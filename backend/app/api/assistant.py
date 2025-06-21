"""
API endpoints for Pathfinder Assistant functionality
"""

import logging
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.pathfinder_assistant import assistant_service
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class MentionRequest(BaseModel):
    """Request model for @pathfinder mentions"""

    message: str = Field(...,
                         description="The message containing @pathfinder mention")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Current context information"
    )
    trip_id: Optional[str] = Field(
        None, description="Current trip ID if applicable")
    family_id: Optional[str] = Field(
        None, description="Current family ID if applicable"
    )


class FeedbackRequest(BaseModel):
    """Request model for assistant feedback"""

    interaction_id: str = Field(...,
                                description="ID of the assistant interaction")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    feedback_text: Optional[str] = Field(
        None, description="Optional feedback text")


class SuggestionsRequest(BaseModel):
    """Request model for contextual suggestions"""

    context: Dict[str, Any] = Field(
        default_factory=dict, description="Current context information"
    )
    page: Optional[str] = Field(None, description="Current page/route")
    trip_id: Optional[str] = Field(
        None, description="Current trip ID if applicable")


@router.post("/mention")
async def process_mention(
    request: MentionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process @pathfinder mention and return AI response"""
    try:
        # Add user context to the request context
        context = request.context.copy()
        context.update(
            {
                "user_id": current_user.id,
                "user_role": current_user.role,
                "trip_id": request.trip_id,
                "family_id": request.family_id,
            }
        )

        # Process the mention
        result = await assistant_service.process_mention(
            message=request.message, user_id=current_user.id, context=context, db=db
        )

        if result.get("success"):
            return {
                "success": True,
                "data": {
                    "interaction_id": result["interaction_id"],
                    "response": result["response"]["text"],
                    "response_cards": result["response_cards"],
                    "processing_time_ms": result["processing_time_ms"],
                },
            }
        else:
            raise HTTPException(
                status_code=400, detail=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Error processing mention: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Assistant error: {str(e)}")


@router.get("/suggestions")
async def get_contextual_suggestions(
    page: Optional[str] = None,
    trip_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get contextual AI suggestions for the current user context"""
    try:
        context = {
            "current_page": page,
            "user_id": current_user.id,
            "user_role": current_user.role,
            "trip_id": trip_id,
        }

        # Add trip data if trip_id is provided
        if trip_id:
            # TODO: Fetch trip data from database
            context["trip_data"] = {
                "id": trip_id,
                "has_polls": False,  # This would be fetched from database
                "has_budget": False,  # This would be fetched from database
            }

        suggestions = await assistant_service.get_contextual_suggestions(
            user_id=current_user.id, context=context, db=db
        )

        return {"success": True, "suggestions": suggestions}

    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Suggestions error: {str(e)}")


@router.post("/feedback")
async def provide_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Provide feedback on an assistant interaction"""
    try:
        success = await assistant_service.provide_feedback(
            interaction_id=request.interaction_id,
            rating=request.rating,
            feedback_text=request.feedback_text,
            db=db,
        )

        if success:
            return {"success": True, "message": "Feedback submitted successfully"}
        else:
            raise HTTPException(
                status_code=404, detail="Interaction not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error providing feedback: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Feedback error: {str(e)}")


@router.get("/interactions/history")
async def get_interaction_history(
    limit: int = 10,
    offset: int = 0,
    trip_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's assistant interaction history"""
    try:
        from app.models.ai_integration import AssistantInteraction

        query = db.query(AssistantInteraction).filter(
            AssistantInteraction.user_id == current_user.id
        )

        if trip_id:
            query = query.filter(AssistantInteraction.trip_id == trip_id)

        interactions = (
            query.order_by(AssistantInteraction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return {
            "success": True,
            "interactions": [interaction.to_dict() for interaction in interactions],
            "total": query.count(),
        }

    except Exception as e:
        logger.error(f"Error getting interaction history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History error: {str(e)}")


@router.get("/interactions/{interaction_id}")
async def get_interaction_details(
    interaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific assistant interaction"""
    try:
        from app.models.ai_integration import AIResponseCard, AssistantInteraction

        interaction = (
            db.query(AssistantInteraction)
            .filter(
                AssistantInteraction.id == interaction_id,
                AssistantInteraction.user_id == current_user.id,
            )
            .first()
        )

        if not interaction:
            raise HTTPException(
                status_code=404, detail="Interaction not found")

        # Get response cards
        response_cards = (
            db.query(AIResponseCard)
            .filter(AIResponseCard.interaction_id == interaction_id)
            .order_by(AIResponseCard.display_order)
            .all()
        )

        return {
            "success": True,
            "interaction": interaction.to_dict(),
            "response_cards": [card.to_dict() for card in response_cards],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interaction details: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Interaction error: {str(e)}")


@router.post("/cards/{card_id}/dismiss")
async def dismiss_response_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dismiss a response card"""
    try:
        from app.models.ai_integration import AIResponseCard, AssistantInteraction

        # Verify the card belongs to the current user
        card = (
            db.query(AIResponseCard)
            .join(AssistantInteraction)
            .filter(
                AIResponseCard.id == card_id,
                AssistantInteraction.user_id == current_user.id,
            )
            .first()
        )

        if not card:
            raise HTTPException(
                status_code=404, detail="Response card not found")

        card.is_dismissed = True
        db.commit()

        return {"success": True, "message": "Response card dismissed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dismiss error: {str(e)}")


@router.get("/health")
async def assistant_health():
    """Health check for assistant service"""
    return {
        "success": True,
        "service": "Pathfinder Assistant",
        "status": "healthy",
        "features": [
            "@mention processing",
            "contextual suggestions",
            "response cards",
            "feedback collection",
        ],
    }
