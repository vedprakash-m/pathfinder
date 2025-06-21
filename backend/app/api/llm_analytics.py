"""
LLM Analytics API endpoints
Provides monitoring and analytics for LLM usage and orchestration service
"""

from typing import Any, Dict, Optional

from app.core.logging_config import create_logger
from app.core.security import get_current_user
from app.services.ai_service import ai_service
from app.services.llm_orchestration_client import (
    LLMOrchestrationClient,
    get_llm_orchestration_client,
)
from fastapi import APIRouter, Depends, HTTPException, status

logger = create_logger(__name__)
router = APIRouter(prefix="/api/v1/llm", tags=["LLM Analytics"])


@router.get("/health")
async def get_llm_health(
    current_user: dict = Depends(get_current_user),
    llm_client: LLMOrchestrationClient = Depends(get_llm_orchestration_client),
) -> Dict[str, Any]:
    """Get LLM orchestration service health status."""

    try:
        # Check if orchestration service is enabled and healthy
        orchestration_healthy = await llm_client.is_healthy()

        # Get AI service usage stats
        usage_stats = ai_service.get_usage_stats()

        return {
            "status": "healthy" if orchestration_healthy else "degraded",
            "orchestration_service": {
                "enabled": llm_client.enabled,
                "url": llm_client.base_url if llm_client.enabled else None,
                "healthy": orchestration_healthy,
                "fallback_mode": not orchestration_healthy and llm_client.enabled,
            },
            "usage_stats": usage_stats,
            "services": {
                "direct_openai": "available",
                "llm_orchestration": "available" if orchestration_healthy else "unavailable",
            },
        }

    except Exception as e:
        logger.error(f"Error checking LLM health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check LLM health: {str(e)}",
        )


@router.get("/analytics")
async def get_llm_analytics(
    hours: int = 24,
    current_user: dict = Depends(get_current_user),
    llm_client: LLMOrchestrationClient = Depends(get_llm_orchestration_client),
) -> Dict[str, Any]:
    """Get LLM usage analytics for the specified time period."""

    try:
        # Get analytics from orchestration service if available
        orchestration_analytics = {}
        if llm_client.enabled:
            orchestration_analytics = await llm_client.get_analytics(hours=hours)

        # Get local usage stats
        usage_stats = ai_service.get_usage_stats()

        # Get cost optimization suggestions
        cost_suggestions = ai_service.cost_tracker.get_optimization_suggestions()

        return {
            "time_period_hours": hours,
            "orchestration_analytics": orchestration_analytics,
            "local_usage": usage_stats,
            "optimization_suggestions": cost_suggestions,
            "summary": {
                "total_requests": usage_stats.get("today", {}).get("requests", 0),
                "total_cost": usage_stats.get("today", {}).get("cost", 0.0),
                "budget_remaining": usage_stats.get("budget_remaining", 0.0),
                "orchestration_enabled": llm_client.enabled,
            },
        }

    except Exception as e:
        logger.error(f"Error getting LLM analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM analytics: {str(e)}",
        )


@router.get("/budget")
async def get_budget_status(
    current_user: dict = Depends(get_current_user),
    llm_client: LLMOrchestrationClient = Depends(get_llm_orchestration_client),
) -> Dict[str, Any]:
    """Get current budget status from orchestration service and local tracking."""

    try:
        # Get budget status from orchestration service if available
        orchestration_budget = {}
        if llm_client.enabled:
            orchestration_budget = await llm_client.get_budget_status()

        # Get local usage stats for budget tracking
        usage_stats = ai_service.get_usage_stats()

        return {
            "orchestration_budget": orchestration_budget,
            "local_budget": {
                "daily_limit": usage_stats.get("budget_limit", 0.0),
                "daily_used": usage_stats.get("today", {}).get("cost", 0.0),
                "daily_remaining": usage_stats.get("budget_remaining", 0.0),
                "requests_today": usage_stats.get("today", {}).get("requests", 0),
            },
            "recommendations": ai_service.cost_tracker.get_optimization_suggestions(),
        }

    except Exception as e:
        logger.error(f"Error getting budget status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget status: {str(e)}",
        )


@router.post("/test-generation")
async def test_llm_generation(
    prompt: str = "Generate a brief test response for API health check",
    current_user: dict = Depends(get_current_user),
    llm_client: LLMOrchestrationClient = Depends(get_llm_orchestration_client),
) -> Dict[str, Any]:
    """Test LLM generation capabilities for diagnostics."""

    try:
        # Test orchestration service if enabled
        if llm_client.enabled:
            try:
                response = await llm_client.generate_text(
                    prompt=prompt,
                    task_type="test",
                    user_id=current_user.get("sub"),
                    max_tokens=100,
                    temperature=0.5,
                )

                return {
                    "success": True,
                    "service_used": "llm_orchestration",
                    "response": response,
                    "test_prompt": prompt,
                }

            except Exception as e:
                logger.warning(f"LLM Orchestration test failed: {e}")
                # Fall through to local test

        # Test local AI service as fallback
        try:
            response = await ai_service._make_api_call(
                model="gpt-4o-mini",
                prompt=prompt,
                input_tokens=ai_service.count_tokens(prompt),
                task_type="test",
                user_id=current_user.get("sub"),
            )

            return {
                "success": True,
                "service_used": "direct_openai",
                "response": {
                    "text": response.get("content", ""),
                    "model_used": response.get("model"),
                    "cost": response.get("cost", 0.0),
                    "source": response.get("source"),
                },
                "test_prompt": prompt,
            }

        except Exception as e:
            logger.error(f"Direct OpenAI test failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Both LLM services failed: {str(e)}",
            )

    except Exception as e:
        logger.error(f"Error testing LLM generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test LLM generation: {str(e)}",
        )
