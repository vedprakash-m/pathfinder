"""
Test endpoints for validating AI service functionality.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..core.logging_config import get_logger
from ..core.zero_trust import require_permissions
from ..models.user import User
from ..services.ai_service import AIService

router = APIRouter(prefix="/test", tags=["testing"])
logger = get_logger(__name__)


class AITestRequest(BaseModel):
    destination: str
    duration_days: int = 3
    budget: Optional[float] = 1000.0


class AITestResponse(BaseModel):
    status: str
    message: str
    test_passed: bool
    details: Optional[Dict[str, Any]] = None


@router.post("/ai", response_model=AITestResponse)
async def test_ai_service(
    request: AITestRequest,
    current_user: User = Depends(require_permissions("test", "execute")),
):
    """Test the AI service with a simple itinerary generation request."""
    try:
        ai_service = AIService()

        # Test data
        families_data = [
            {
                "user_id": "test-user",
                "family_size": 2,
                "preferences": {"activity_level": "moderate"},
                "budget_share": request.budget,
            }
        ]

        preferences = {
            "trip_type": "family vacation",
            "activity_level": "moderate",
            "accommodation_type": "hotel",
        }

        # Test AI service
        logger.info(f"Testing AI service for destination: {request.destination}")

        result = await ai_service.generate_itinerary(
            destination=request.destination,
            duration_days=request.duration_days,
            families_data=families_data,
            preferences=preferences,
            budget_total=request.budget,
            user_id="test-user",
        )

        return AITestResponse(
            status="success",
            message="AI service is working correctly",
            test_passed=True,
            details={
                "destination": request.destination,
                "duration_days": request.duration_days,
                "generated_title": result.get("title", "Generated Itinerary"),
                "days_count": len(result.get("days", [])),
                "confidence_score": result.get("confidence_score"),
            },
        )

    except Exception as e:
        logger.error(f"AI service test failed: {str(e)}")
        return AITestResponse(
            status="error",
            message=f"AI service test failed: {str(e)}",
            test_passed=False,
            details={"error": str(e)},
        )


@router.get("/health")
async def test_health():
    """Simple health check for testing endpoints."""
    return {
        "status": "ok",
        "message": "Test endpoints are available",
        "endpoints": ["/api/v1/test/ai - Test AI service", "/api/v1/test/health - This endpoint"],
    }
