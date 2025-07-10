from __future__ import annotations
"""
API endpoints for AI Cost Management functionality
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..core.ai_cost_management import ai_cost_tracker, get_ai_usage_stats
from ..core.logging_config import get_logger
from ..core.security import get_current_user
# SQL User model removed - use Cosmos UserDocument
from ..services.ai_service import advanced_ai_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai-cost"])


class CostStatusResponse(BaseModel):
    """Response model for AI cost status"""

budgetUsed: float = Field(..., description="Amount of budget used today")
budgetLimit: float = Field(..., description="Daily budget limit")
remainingQuota: float = Field(..., description="Remaining budget quota")
currentTier: str = Field(..., description="Current usage tier")
gracefulMode: bool = Field(..., description="Whether in graceful degradation mode")
dailyRequests: int = Field(default=0, description="Number of requests today")
averageCostPerRequest: float = Field(default=0.0, description="Average cost per request")
modelUsage: dict[str, Any] = Field(default_factory=dict, description="Usage by model")


class UsageStatsResponse(BaseModel):
    """Response model for detailed usage statistics"""

daily_stats: dict[str, Any] = Field(default_factory=dict, description="Daily usage statistics")
user_stats: Optional[dict[str, Any]] = Field(None, description="User-specific statistics")
limits: dict[str, float] = Field(default_factory=dict, description="Cost limits")
remaining: dict[str, float] = Field(default_factory=dict, description="Remaining budget")
optimization_suggestions: list = Field(
        default_factory=list, description="Cost optimization suggestions"
)


@router.get("/cost/status", response_model=CostStatusResponse)
async def get_cost_status(current_user: User = Depends(get_current_user)  ):  # noqa: B008 -> CostStatusResponse:
    """
Get current AI cost status and budget information.
This endpoint provides the data expected by the frontend aiService."""
"""
try:
        # Get usage stats from the advanced AI service
cost_status = advanced_ai_service.get_cost_status()

# Determine current tier based on usage"""
budget_used_percent = (cost_status["daily_cost"] / cost_status["budget_limit"]) * 100

if budget_used_percent >= 90:
            current_tier = "critical"
elif budget_used_percent >= 70:
            current_tier = "warning"
elif budget_used_percent >= 50:
            current_tier = "moderate"
else:
            current_tier = "basic"

# Calculate average cost per request
avg_cost = (
            cost_status["daily_cost"] / max(1, cost_status["daily_requests"])
if cost_status["daily_requests"] > 0
else 0.0
)

return CostStatusResponse(
            budgetUsed=cost_status["daily_cost"],
budgetLimit=cost_status["budget_limit"],
remainingQuota=cost_status["budget_remaining"],
currentTier=current_tier,
gracefulMode=cost_status["graceful_mode"],
dailyRequests=cost_status["daily_requests"],
averageCostPerRequest=round(avg_cost, 4),
modelUsage={},  # Could be enhanced with model breakdown
)

except Exception as e:
        logger.error(f"Failed to get AI cost status: {e}")
# Return safe defaults if the cost tracking system fails
return CostStatusResponse(
            budgetUsed=0.0,
budgetLimit=50.0,
remainingQuota=50.0,
currentTier="basic",
gracefulMode=False,
dailyRequests=0,
averageCostPerRequest=0.0,
modelUsage={},
)


@router.get("/usage/stats", response_model=UsageStatsResponse)
async def get_usage_stats(current_user: User = Depends(get_current_user)  ):  # noqa: B008 -> UsageStatsResponse:
    """
Get detailed AI usage statistics for the current user."""
"""
try:"""
user_id = str(current_user.id) if hasattr(current_user, "id") else None

# Get usage stats from the cost tracker
usage_stats = get_ai_usage_stats(user_id)

# Get optimization suggestions
optimization_suggestions = advanced_ai_service.get_optimization_suggestions()

return UsageStatsResponse(
            daily_stats=usage_stats.get("daily_stats", {}),
user_stats=usage_stats.get("user_stats"),
limits=usage_stats.get("limits", {}),
remaining=usage_stats.get("remaining", {}),
optimization_suggestions=optimization_suggestions,
)

except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
raise HTTPException(status_code=500, detail="Failed to retrieve usage statistics")


@router.get("/budget/status")
async def get_budget_status(current_user: User = Depends(get_current_user)  ):  # noqa: B008 -> dict[str, Any]:
    """
Get budget status with detailed breakdown."""
"""
try:"""
user_id = str(current_user.id) if hasattr(current_user, "id") else None

# Get cost breakdown from AICostTracker
cost_breakdown = ai_cost_tracker.get_cost_breakdown()

# Check if budget is exceeded
budget_exceeded = ai_cost_tracker.is_budget_exceeded(user_id)

return {
            "budget_status": "exceeded" if budget_exceeded else "ok",
"cost_breakdown": cost_breakdown,
"can_make_requests": not budget_exceeded,
"daily_limit": cost_breakdown.get("daily_limit", 50.0),
"remaining_budget": cost_breakdown.get("remaining_budget", 0.0),
"endpoint_usage": cost_breakdown.get("endpoint_breakdown", {}),
"active_users": cost_breakdown.get("active_users", 0),
)}

except Exception as e:
        logger.error(f"Failed to get budget status: {e}")
raise HTTPException(status_code=500, detail="Failed to retrieve budget status")


@router.post("/budget/validate")
async def validate_request_budget(
    request_data: dict[str, Any], current_user: User = Depends(get_current_user)  # noqa: B008:
) -> dict[str, Any]:
    """
Validate if a request can be processed within budget limits."""
"""
try:"""
model = request_data.get("model", "gpt-4o-mini")
estimated_tokens = request_data.get("estimated_tokens", 1000)

# Validate budget using AICostTracker
is_valid = ai_cost_tracker.validate_request_budget(model, estimated_tokens)

# Get cost estimate
estimated_cost = (estimated_tokens / 1000) * ai_cost_tracker.model_costs.get(model, 0.001)

return {
            "valid": is_valid,
"estimated_cost": round(estimated_cost, 4),
"model": model,
"estimated_tokens": estimated_tokens,
"reason": "Budget limits exceeded" if not is_valid else "Request can be processed",
)}

except Exception as e:
        logger.error(f"Failed to validate request budget: {e}")
raise HTTPException(status_code=500, detail="Failed to validate request budget")


@router.get("/health")
async def get_ai_health() -> dict[str, Any]:
    """
Get AI service health status including cost management system."""
"""
try:
        # Check if cost tracking is working
usage_stats = get_ai_usage_stats()

# Check if advanced AI service is functional
budget_status = advanced_ai_service.get_cost_status()

return {"""
"status": "healthy",
"cost_tracking": "operational",
"budget_management": "operational",
"graceful_degradation": "available",
"last_check": usage_stats.get("daily_stats", {}).get("total_requests", 0) > 0,
"budget_remaining": budget_status.get("budget_remaining", 0),
"services": {
                "cost_tracker": "up",
"advanced_ai_service": "up",
"usage_analytics": "up",
},
)}

except Exception as e:
        logger.error(f"AI health check failed: {e}")
return {
            "status": "degraded",
"error": str(e),
"cost_tracking": "error",
"budget_management": "error",
"graceful_degradation": "available",
"services": {
                "cost_tracker": "down",
"advanced_ai_service": "down",
"usage_analytics": "down",
},
)}
