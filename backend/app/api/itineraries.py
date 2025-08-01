from __future__ import annotations

"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
Itinerary management API endpoints.
Handles AI-generated itinerary creation, customization, and management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..core.database_unified import get_cosmos_repository
from ..core.logging_config import get_logger
from ..core.zero_trust import require_permissions

# SQL User model removed - use Cosmos UserDocument
from ..repositories.cosmos_unified import UnifiedCosmosRepository
from ..services.ai_service import AIService

router = APIRouter(tags=["itineraries"])
logger = get_logger(__name__)


from datetime import date, datetime
from enum import Enum

# Pydantic models for itinerary API
from pydantic import BaseModel


class ItineraryType(str, Enum):
    FULL_TRIP = "full_trip"


DAILY = "daily"
ACTIVITY = "activity"


class ItineraryRequest(BaseModel):
    trip_id: int


itinerary_type: ItineraryType = ItineraryType.FULL_TRIP
preferences: Optional[dict[str, Any]] = None
regenerate: bool = False


class ItineraryCustomization(BaseModel):
    activity_preferences: Optional[list[str]] = None


budget_constraints: Optional[dict[str, float]] = None
accessibility_needs: Optional[list[str]] = None
dietary_restrictions: Optional[list[str]] = None
transportation_preferences: Optional[list[str]] = None
accommodation_preferences: Optional[list[str]] = None


class ItineraryDay(BaseModel):
    date: date


activities: list[dict[str, Any]]
estimated_cost: Optional[float] = None
transportation: Optional[dict[str, Any]] = None


class GeneratedItinerary(BaseModel):
    id: Optional[str] = None


trip_id: int
title: str
description: Optional[str] = None
days: list[ItineraryDay]
total_estimated_cost: Optional[float] = None
generated_at: datetime
customizations: Optional[ItineraryCustomization] = None
ai_confidence_score: Optional[float] = None


class ItineraryResponse(BaseModel):
    itinerary: GeneratedItinerary


alternatives: Optional[list[dict[str, Any]]] = None
optimization_suggestions: Optional[list[str]] = None


@router.post("/{trip_id}/generate", response_model=ItineraryResponse)
async def generate_itinerary(
    trip_id: int,
    request_data: ItineraryRequest,
    request: Request,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: dict = Depends(require_permissions("itineraries", "create")),
    ai_service: AIService = Depends(lambda: AIService()),  # noqa: B008
):
    """Generate an AI-powered itinerary for a trip."""
    try:
        # Verify trip exists and user has access
        trip = await cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )

        # Check if user has access to trip
        user_trips = await cosmos_repo.get_user_trips(current_user["id"])
        if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip",
            )

        # Calculate trip duration
        if trip.start_date and trip.end_date:
            duration_days = (trip.end_date - trip.start_date).days + 1
        else:
            duration_days = 3

        # Prepare families data for AI service
        families_data = []
        for p in trip.participations:
            if p.user:
                family_data = {
                    "user_id": str(p.user.id),
                    "family_size": 1,  # Could be enhanced to include actual family size
                    "preferences": (
                        p.user.preferences
                        if hasattr(p.user, "preferences") and p.user.preferences
                        else {}
                    ),
                    "budget_share": (
                        float(trip.budget_total or 0) / len(trip.participations)
                        if trip.budget_total
                        else None
                    ),
                }
                families_data.append(family_data)

        # Merge request preferences with trip preferences
        preferences = {}
        if hasattr(trip, "preferences") and trip.preferences:
            try:
                import json

                preferences.update(
                    json.loads(trip.preferences)
                    if isinstance(trip.preferences, str)
                    else trip.preferences
                )
            except (json.JSONDecodeError, TypeError):
                pass

        if request_data.preferences:
            preferences.update(request_data.preferences)

        # Add default preferences if none exist
        if not preferences:
            preferences = {
                "trip_type": "family road trip",
                "activity_level": "moderate",
                "accommodation_type": "hotel",
            }

        # Generate itinerary using AI service with correct parameters
        logger.info(
            f"Generating itinerary for trip {trip_id} by user {current_user['id']}"
        )
        itinerary_data = await ai_service.generate_itinerary(
            destination=str(trip.destination),
            duration_days=duration_days,
            families_data=families_data,
            preferences=preferences,
            budget_total=float(trip.budget_total) if trip.budget_total else None,
            user_id=str(current_user["id"]),
        )  # Create itinerary response
        itinerary = GeneratedItinerary(
            trip_id=trip_id,
            title=itinerary_data.get("title", f"Itinerary for {trip.destination}"),
            description=itinerary_data.get("description"),
            days=[
                ItineraryDay(
                    date=datetime.fromisoformat(day["date"]).date(),
                    activities=day["activities"],
                    estimated_cost=day.get("estimated_cost"),
                    transportation=day.get("transportation"),
                )
                for day in itinerary_data.get("days", [])
            ],
            total_estimated_cost=itinerary_data.get("total_estimated_cost"),
            generated_at=datetime.utcnow(),
            ai_confidence_score=itinerary_data.get("confidence_score"),
        )

        response = ItineraryResponse(
            itinerary=itinerary,
            alternatives=itinerary_data.get("alternatives"),
            optimization_suggestions=itinerary_data.get("optimization_suggestions"),
        )

        logger.info(f"Itinerary generated successfully for trip {trip_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating itinerary for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate itinerary",
        )


@router.post("/{trip_id}/customize", response_model=ItineraryResponse)
async def customize_itinerary(
    trip_id: int,
    customization: ItineraryCustomization,
    request: Request,
    base_itinerary: Optional[dict[str, Any]] = None,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("itineraries", "update")),
    ai_service: AIService = Depends(lambda: AIService()),  # noqa: B008
):
    """Customize an existing itinerary based on user preferences."""
    try:
        # Verify trip access
        trip = await cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )

        # Check if user has access to trip
        user_trips = await cosmos_repo.get_user_trips(current_user["id"])
        if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip",
            )

        # Prepare customization context
        customization_context = {
            "trip_id": trip_id,
            "destination": trip.destination,
            "customizations": customization.dict(exclude_none=True),
            "base_itinerary": base_itinerary,
        }

        # Generate customized itinerary
        logger.info(
            f"Customizing itinerary for trip {trip_id} by user {current_user['id']}"
        )
        itinerary_data = await ai_service.customize_itinerary(customization_context)

        # Create response
        itinerary = GeneratedItinerary(
            trip_id=trip_id,
            title=itinerary_data.get(
                "title", f"Customized Itinerary for {trip.destination}"
            ),
            description=itinerary_data.get("description"),
            days=[
                ItineraryDay(
                    date=datetime.fromisoformat(day["date"]).date(),
                    activities=day["activities"],
                    estimated_cost=day.get("estimated_cost"),
                    transportation=day.get("transportation"),
                )
                for day in itinerary_data.get("days", [])
            ],
            total_estimated_cost=itinerary_data.get("total_estimated_cost"),
            generated_at=datetime.utcnow(),
            customizations=customization,
            ai_confidence_score=itinerary_data.get("confidence_score"),
        )

        response = ItineraryResponse(
            itinerary=itinerary,
            alternatives=itinerary_data.get("alternatives"),
            optimization_suggestions=itinerary_data.get("optimization_suggestions"),
        )

        logger.info(f"Itinerary customized successfully for trip {trip_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error customizing itinerary for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to customize itinerary",
        )


@router.get("/{trip_id}/suggestions")
async def get_activity_suggestions(
    trip_id: int,
    request: Request,
    activity_type: Optional[str] = Query(
        None, description="Type of activity to suggest"
    ),
    location: Optional[str] = Query(
        None, description="Specific location within trip destination"
    ),
    budget_range: Optional[str] = Query(
        None, description="Budget range (low, medium, high)"
    ),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("itineraries", "read")),
    ai_service: AIService = Depends(lambda: AIService()),  # noqa: B008
):
    """Get AI-powered activity suggestions for a trip."""
    try:
        # Verify trip access
        trip = await cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )

        # Check if user has access to trip
        user_trips = await cosmos_repo.get_user_trips(current_user["id"])
        if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip",
            )

        # Prepare suggestion context
        suggestion_context = {
            "destination": trip.destination,
            "activity_type": activity_type,
            "location": location,
            "budget_range": budget_range,
            "participant_count": len(trip.participations),
        }

        # Get activity suggestions
        logger.info(f"Getting activity suggestions for trip {trip_id}")
        suggestions = await ai_service.get_activity_suggestions(suggestion_context)

        return {
            "trip_id": trip_id,
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity suggestions for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity suggestions",
        )


@router.post("/{trip_id}/optimize")
async def optimize_itinerary(
    trip_id: int,
    itinerary: dict[str, Any],
    request: Request,
    optimization_criteria: Optional[list[str]] = Query(
        None, description="Optimization criteria"
    ),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("itineraries", "update")),
    ai_service: AIService = Depends(lambda: AIService()),  # noqa: B008
):
    """Optimize an existing itinerary for better efficiency, cost, or experience."""
    try:
        # Verify trip access
        trip = await cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )

        # Check if user has access to trip
        user_trips = await cosmos_repo.get_user_trips(current_user["id"])
        if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip",
            )

        # Prepare optimization context
        optimization_context = {
            "trip_id": trip_id,
            "destination": trip.destination,
            "budget": trip.budget,
            "itinerary": itinerary,
            "optimization_criteria": optimization_criteria
            or ["cost", "time", "experience"],
        }

        # Optimize itinerary
        logger.info(
            f"Optimizing itinerary for trip {trip_id} by user {current_user['id']}"
        )
        optimized_data = await ai_service.optimize_itinerary(optimization_context)

        # Create response
        optimized_itinerary = GeneratedItinerary(
            trip_id=trip_id,
            title=optimized_data.get(
                "title", f"Optimized Itinerary for {trip.destination}"
            ),
            description=optimized_data.get("description"),
            days=[
                ItineraryDay(
                    date=datetime.fromisoformat(day["date"]).date(),
                    activities=day["activities"],
                    estimated_cost=day.get("estimated_cost"),
                    transportation=day.get("transportation"),
                )
                for day in optimized_data.get("days", [])
            ],
            total_estimated_cost=optimized_data.get("total_estimated_cost"),
            generated_at=datetime.utcnow(),
            ai_confidence_score=optimized_data.get("confidence_score"),
        )

        return {
            "original_itinerary": itinerary,
            "optimized_itinerary": optimized_itinerary,
            "optimization_summary": optimized_data.get("optimization_summary"),
            "improvements": optimized_data.get("improvements"),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing itinerary for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize itinerary",
        )


@router.get("/{trip_id}/alternatives")
async def get_itinerary_alternatives(
    trip_id: int,
    request: Request,
    current_itinerary: Optional[dict[str, Any]] = None,
    variation_type: Optional[str] = Query(
        "budget", description="Type of variation (budget, activity, timeline)"
    ),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("itineraries", "read")),
    ai_service: AIService = Depends(lambda: AIService()),  # noqa: B008
):
    """Get alternative itinerary options for a trip."""
    try:
        # Verify trip access
        trip = await cosmos_repo.get_trip_by_id(str(trip_id))
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )

        # Check if user has access to trip
        user_trips = await cosmos_repo.get_user_trips(current_user["id"])
        if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip",
            )

        # Prepare context for alternatives
        alternatives_context = {
            "trip_id": trip_id,
            "destination": trip.destination,
            "budget": trip.budget,
            "current_itinerary": current_itinerary,
            "variation_type": variation_type,
        }

        # Generate alternatives
        logger.info(f"Getting itinerary alternatives for trip {trip_id}")
        alternatives_data = await ai_service.generate_alternatives(alternatives_context)

        alternatives = []
        for alt in alternatives_data.get("alternatives", []):
            alternative = GeneratedItinerary(
                trip_id=trip_id,
                title=alt.get("title"),
                description=alt.get("description"),
                days=[
                    ItineraryDay(
                        date=datetime.fromisoformat(day["date"]).date(),
                        activities=day["activities"],
                        estimated_cost=day.get("estimated_cost"),
                        transportation=day.get("transportation"),
                    )
                    for day in alt.get("days", [])
                ],
                total_estimated_cost=alt.get("total_estimated_cost"),
                generated_at=datetime.utcnow(),
                ai_confidence_score=alt.get("confidence_score"),
            )
            alternatives.append(alternative)

        return {
            "trip_id": trip_id,
            "variation_type": variation_type,
            "alternatives": alternatives,
            "comparison_summary": alternatives_data.get("comparison_summary"),
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting itinerary alternatives for trip {trip_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get itinerary alternatives",
        )
