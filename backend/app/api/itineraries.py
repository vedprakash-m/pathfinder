"""
Itinerary management API endpoints.
Handles AI-generated itinerary creation, customization, and management.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.trip import Trip, TripParticipation
from ..services.ai_service import AIService
from ..core.logging_config import get_logger

router = APIRouter(tags=["itineraries"])
logger = get_logger(__name__)


# Pydantic models for itinerary API
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum


class ItineraryType(str, Enum):
    FULL_TRIP = "full_trip"
    DAILY = "daily"
    ACTIVITY = "activity"


class ItineraryRequest(BaseModel):
    trip_id: int
    itinerary_type: ItineraryType = ItineraryType.FULL_TRIP
    preferences: Optional[Dict[str, Any]] = None
    regenerate: bool = False


class ItineraryCustomization(BaseModel):
    activity_preferences: Optional[List[str]] = None
    budget_constraints: Optional[Dict[str, float]] = None
    accessibility_needs: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    transportation_preferences: Optional[List[str]] = None
    accommodation_preferences: Optional[List[str]] = None


class ItineraryDay(BaseModel):
    date: date
    activities: List[Dict[str, Any]]
    estimated_cost: Optional[float] = None
    transportation: Optional[Dict[str, Any]] = None


class GeneratedItinerary(BaseModel):
    id: Optional[str] = None
    trip_id: int
    title: str
    description: Optional[str] = None
    days: List[ItineraryDay]
    total_estimated_cost: Optional[float] = None
    generated_at: datetime
    customizations: Optional[ItineraryCustomization] = None
    ai_confidence_score: Optional[float] = None


class ItineraryResponse(BaseModel):
    itinerary: GeneratedItinerary
    alternatives: Optional[List[Dict[str, Any]]] = None
    optimization_suggestions: Optional[List[str]] = None


@router.post("/{trip_id}/generate", response_model=ItineraryResponse)
async def generate_itinerary(
    trip_id: int,
    request: ItineraryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService())
):
    """Generate an AI-powered itinerary for a trip."""
    try:
        # Verify trip exists and user has access
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        # Check if user is a participant
        participation = db.query(TripParticipation).filter(
            and_(
                TripParticipation.trip_id == trip_id,
                TripParticipation.user_id == current_user.id
            )
        ).first()
        
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip"
            )
        
        # Prepare trip context for AI
        trip_context = {
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat() if trip.start_date else None,
            "end_date": trip.end_date.isoformat() if trip.end_date else None,
            "budget": trip.budget,
            "participant_count": len(trip.participations),
            "trip_type": "family road trip",
            "preferences": request.preferences or {}
        }
        
        # Get participant preferences if available
        participant_preferences = []
        for p in trip.participations:
            if p.user and p.user.preferences:
                participant_preferences.append({
                    "user_id": p.user_id,
                    "preferences": p.user.preferences
                })
        
        trip_context["participant_preferences"] = participant_preferences
        
        # Generate itinerary using AI service
        logger.info(f"Generating itinerary for trip {trip_id} by user {current_user.id}")
        itinerary_data = await ai_service.generate_itinerary(
            trip_context=trip_context,
            itinerary_type=request.itinerary_type.value,
            regenerate=request.regenerate
        )
        
        # Create itinerary response
        itinerary = GeneratedItinerary(
            trip_id=trip_id,
            title=itinerary_data.get("title", f"Itinerary for {trip.destination}"),
            description=itinerary_data.get("description"),
            days=[
                ItineraryDay(
                    date=datetime.fromisoformat(day["date"]).date(),
                    activities=day["activities"],
                    estimated_cost=day.get("estimated_cost"),
                    transportation=day.get("transportation")
                )
                for day in itinerary_data.get("days", [])
            ],
            total_estimated_cost=itinerary_data.get("total_estimated_cost"),
            generated_at=datetime.utcnow(),
            ai_confidence_score=itinerary_data.get("confidence_score")
        )
        
        response = ItineraryResponse(
            itinerary=itinerary,
            alternatives=itinerary_data.get("alternatives"),
            optimization_suggestions=itinerary_data.get("optimization_suggestions")
        )
        
        logger.info(f"Itinerary generated successfully for trip {trip_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating itinerary for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate itinerary"
        )


@router.post("/{trip_id}/customize", response_model=ItineraryResponse)
async def customize_itinerary(
    trip_id: int,
    customization: ItineraryCustomization,
    base_itinerary: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService())
):
    """Customize an existing itinerary based on user preferences."""
    try:
        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        participation = db.query(TripParticipation).filter(
            and_(
                TripParticipation.trip_id == trip_id,
                TripParticipation.user_id == current_user.id
            )
        ).first()
        
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip"
            )
        
        # Prepare customization context
        customization_context = {
            "trip_id": trip_id,
            "destination": trip.destination,
            "customizations": customization.dict(exclude_none=True),
            "base_itinerary": base_itinerary
        }
        
        # Generate customized itinerary
        logger.info(f"Customizing itinerary for trip {trip_id} by user {current_user.id}")
        itinerary_data = await ai_service.customize_itinerary(customization_context)
        
        # Create response
        itinerary = GeneratedItinerary(
            trip_id=trip_id,
            title=itinerary_data.get("title", f"Customized Itinerary for {trip.destination}"),
            description=itinerary_data.get("description"),
            days=[
                ItineraryDay(
                    date=datetime.fromisoformat(day["date"]).date(),
                    activities=day["activities"],
                    estimated_cost=day.get("estimated_cost"),
                    transportation=day.get("transportation")
                )
                for day in itinerary_data.get("days", [])
            ],
            total_estimated_cost=itinerary_data.get("total_estimated_cost"),
            generated_at=datetime.utcnow(),
            customizations=customization,
            ai_confidence_score=itinerary_data.get("confidence_score")
        )
        
        response = ItineraryResponse(
            itinerary=itinerary,
            alternatives=itinerary_data.get("alternatives"),
            optimization_suggestions=itinerary_data.get("optimization_suggestions")
        )
        
        logger.info(f"Itinerary customized successfully for trip {trip_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error customizing itinerary for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to customize itinerary"
        )


@router.get("/{trip_id}/suggestions")
async def get_activity_suggestions(
    trip_id: int,
    activity_type: Optional[str] = Query(None, description="Type of activity to suggest"),
    location: Optional[str] = Query(None, description="Specific location within trip destination"),
    budget_range: Optional[str] = Query(None, description="Budget range (low, medium, high)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService())
):
    """Get AI-powered activity suggestions for a trip."""
    try:
        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        participation = db.query(TripParticipation).filter(
            and_(
                TripParticipation.trip_id == trip_id,
                TripParticipation.user_id == current_user.id
            )
        ).first()
        
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip"
            )
        
        # Prepare suggestion context
        suggestion_context = {
            "destination": trip.destination,
            "activity_type": activity_type,
            "location": location,
            "budget_range": budget_range,
            "participant_count": len(trip.participations)
        }
        
        # Get activity suggestions
        logger.info(f"Getting activity suggestions for trip {trip_id}")
        suggestions = await ai_service.get_activity_suggestions(suggestion_context)
        
        return {
            "trip_id": trip_id,
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity suggestions for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity suggestions"
        )


@router.post("/{trip_id}/optimize")
async def optimize_itinerary(
    trip_id: int,
    itinerary: Dict[str, Any],
    optimization_criteria: Optional[List[str]] = Query(None, description="Optimization criteria"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService())
):
    """Optimize an existing itinerary for better efficiency, cost, or experience."""
    try:
        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        participation = db.query(TripParticipation).filter(
            and_(
                TripParticipation.trip_id == trip_id,
                TripParticipation.user_id == current_user.id
            )
        ).first()
        
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip"
            )
        
        # Prepare optimization context
        optimization_context = {
            "trip_id": trip_id,
            "destination": trip.destination,
            "budget": trip.budget,
            "itinerary": itinerary,
            "optimization_criteria": optimization_criteria or ["cost", "time", "experience"]
        }
        
        # Optimize itinerary
        logger.info(f"Optimizing itinerary for trip {trip_id} by user {current_user.id}")
        optimized_data = await ai_service.optimize_itinerary(optimization_context)
        
        # Create response
        optimized_itinerary = GeneratedItinerary(
            trip_id=trip_id,
            title=optimized_data.get("title", f"Optimized Itinerary for {trip.destination}"),
            description=optimized_data.get("description"),
            days=[
                ItineraryDay(
                    date=datetime.fromisoformat(day["date"]).date(),
                    activities=day["activities"],
                    estimated_cost=day.get("estimated_cost"),
                    transportation=day.get("transportation")
                )
                for day in optimized_data.get("days", [])
            ],
            total_estimated_cost=optimized_data.get("total_estimated_cost"),
            generated_at=datetime.utcnow(),
            ai_confidence_score=optimized_data.get("confidence_score")
        )
        
        return {
            "original_itinerary": itinerary,
            "optimized_itinerary": optimized_itinerary,
            "optimization_summary": optimized_data.get("optimization_summary"),
            "improvements": optimized_data.get("improvements"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing itinerary for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize itinerary"
        )


@router.get("/{trip_id}/alternatives")
async def get_itinerary_alternatives(
    trip_id: int,
    current_itinerary: Optional[Dict[str, Any]] = None,
    variation_type: Optional[str] = Query("budget", description="Type of variation (budget, activity, timeline)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService())
):
    """Get alternative itinerary options for a trip."""
    try:
        # Verify trip access
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        participation = db.query(TripParticipation).filter(
            and_(
                TripParticipation.trip_id == trip_id,
                TripParticipation.user_id == current_user.id
            )
        ).first()
        
        if not participation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this trip"
            )
        
        # Prepare context for alternatives
        alternatives_context = {
            "trip_id": trip_id,
            "destination": trip.destination,
            "budget": trip.budget,
            "current_itinerary": current_itinerary,
            "variation_type": variation_type
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
                        transportation=day.get("transportation")
                    )
                    for day in alt.get("days", [])
                ],
                total_estimated_cost=alt.get("total_estimated_cost"),
                generated_at=datetime.utcnow(),
                ai_confidence_score=alt.get("confidence_score")
            )
            alternatives.append(alternative)
        
        return {
            "trip_id": trip_id,
            "variation_type": variation_type,
            "alternatives": alternatives,
            "comparison_summary": alternatives_data.get("comparison_summary"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting itinerary alternatives for trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get itinerary alternatives"
        )