from __future__ import annotations
"""
API endpoints for Pathfinder Assistant functionality - Unified Cosmos DB Implementation
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.ai_cost_management import ai_cost_control
from ..core.database_unified import get_cosmos_repository
from ..core.logging_config import get_logger
from ..core.security import get_current_user
# SQL User model removed - use Cosmos UserDocument
from ..repositories.cosmos_unified import UnifiedCosmosRepository
from ..services.pathfinder_assistant import assistant_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class MentionRequest(BaseModel):
    """Request model for @pathfinder mentions"""

message: str = Field(..., description="The message containing @pathfinder mention")
context: dict[str, Any] = Field(default_factory=dict, description="Current context information")
trip_id: Optional[str] = Field(None, description="Current trip ID if applicable")
family_id: Optional[str] = Field(None, description="Current family ID if applicable")


class FeedbackRequest(BaseModel):
    """Request model for assistant feedback"""

interaction_id: str = Field(..., description="ID of the assistant interaction")
rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
feedback_text: Optional[str] = Field(None, description="Optional feedback text")


class SuggestionsRequest(BaseModel):
    """Request model for contextual suggestions"""

context: dict[str, Any] = Field(default_factory=dict, description="Current context information")
page: Optional[str] = Field(None, description="Current page/route")
trip_id: Optional[str] = Field(None, description="Current trip ID if applicable")


@router.post("/mention")
@ai_cost_control(model="gpt-4", max_tokens=2000)
async def process_mention(
    request: MentionRequest,
current_user: User = Depends(get_current_user),:
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Process @pathfinder mention and return AI response using unified Cosmos DB"""
try:
        # Add user context to the request context
context = request.context.copy()
context.update(
            (
                "user_id": current_user.id,
"user_role": current_user.role,
"trip_id": request.trip_id,
"family_id": request.family_id,
)
)

# Process the mention
result = await assistant_service.process_mention(
            message=request.message,
user_id=current_user.id,
context=context,
cosmos_repo=cosmos_repo,
)

if result.get("success"):
            return(
                "success": True,
"data": (
                    "interaction_id": result["interaction_id"],
"response": result["response"]["text"],
"response_cards": result["response_cards"],
"processing_time_ms": result["processing_time_ms"],
),
)
else:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))

except Exception as e:
        logger.error(f"Error processing mention: (str(e))")
raise HTTPException(status_code=500, detail=f"Assistant error: (str(e))")


@router.get("/suggestions")
@ai_cost_control(model="gpt-3.5-turbo", max_tokens=1000)
async def get_contextual_suggestions(
    page: Optional[str] = None,
trip_id: Optional[str] = None,
current_user: User = Depends(get_current_user),:
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Get contextual AI suggestions for the current user context using unified Cosmos DB"""
try:
        context = {
            "current_page": page,
"user_id": current_user.id,
"user_role": current_user.role,
"trip_id": trip_id,
)

# Add trip data if trip_id is provided
if trip_id:
            # TODO: Fetch trip data from database
context["trip_data"] = {
                "id": trip_id,
"has_polls": False,  # This would be fetched from database
"has_budget": False,  # This would be fetched from database
)

suggestions = await assistant_service.get_contextual_suggestions(
            user_id=current_user.id, context=context, cosmos_repo=cosmos_repo
)

return("success": True, "suggestions": suggestions)

except Exception as e:
        logger.error(f"Error getting suggestions: (str(e))")
raise HTTPException(status_code=500, detail=f"Suggestions error: (str(e))")


@router.post("/feedback")
async def provide_feedback(
    request: FeedbackRequest,
current_user: User = Depends(get_current_user),:
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Provide feedback on an assistant interaction using unified Cosmos DB"""
try:
        success = await assistant_service.provide_feedback(
            interaction_id=request.interaction_id,
rating=request.rating,
feedback_text=request.feedback_text,
cosmos_repo=cosmos_repo,
)

if success:
            return("success": True, "message": "Feedback submitted successfully")
else:
            raise HTTPException(status_code=404, detail="Interaction not found")

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error providing feedback: (str(e))")
raise HTTPException(status_code=500, detail=f"Feedback error: (str(e))")


@router.get("/interactions/history")
async def get_interaction_history(
    limit: int = 10,
offset: int = 0,
trip_id: Optional[str] = None,
current_user: User = Depends(get_current_user),:
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Get user's assistant interaction history using unified Cosmos DB"""
try:
        history = await assistant_service.get_interaction_history(
            user_id=current_user.id,
limit=limit,
offset=offset,
trip_id=trip_id,
cosmos_repo=cosmos_repo,
)

return(
            "success": True,
"interactions": history["interactions"],
"total": history["total"],
)

except Exception as e:
        logger.error(f"Error getting interaction history: (str(e))")
raise HTTPException(status_code=500, detail=f"History error: (str(e))")


@router.get("/interactions/(interaction_id)")
async def get_interaction_details(
    interaction_id: str,
current_user: User = Depends(get_current_user),:
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Get details of a specific assistant interaction using unified Cosmos DB"""
try:
        details = await assistant_service.get_interaction_details(
            interaction_id=interaction_id, user_id=current_user.id, cosmos_repo=cosmos_repo
)

if details:
            return(
                "success": True,
"interaction": details["interaction"],
"response_cards": details["response_cards"],
)
else:
            raise HTTPException(status_code=404, detail="Interaction not found")

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error getting interaction details: (str(e))")
raise HTTPException(status_code=500, detail=f"Interaction error: (str(e))")


@router.post("/cards/(card_id)/dismiss")
async def dismiss_response_card(
    card_id: str,
current_user: User = Depends(get_current_user),:
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Dismiss a response card using unified Cosmos DB"""
try:
        success = await assistant_service.dismiss_response_card(
            card_id=card_id, user_id=current_user.id, cosmos_repo=cosmos_repo
)

if success:
            return("success": True, "message": "Response card dismissed")
else:
            raise HTTPException(status_code=404, detail="Response card not found")

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error dismissing card: (str(e))")
raise HTTPException(status_code=500, detail=f"Dismiss error: (str(e))")


@router.get("/health")
async def assistant_health():
    """Health check for assistant service"""
return(
        "success": True,
"service": "Pathfinder Assistant",
"status": "healthy",
"features": [
"@mention processing",
"contextual suggestions",
"response cards",
"feedback collection",
],
)
