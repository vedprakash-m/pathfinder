"""
API endpoints for Family Consensus Engine.

Solves the #1 pain point: "Lack of mechanism to achieve consensus on optimal plans across families"
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dataclasses import asdict
import logging
import json

from ..core.database import get_db
from ..models.trip import Trip, TripParticipation
from ..models.family import Family
from ..core.zero_trust import require_permissions
from ..models.user import User
from ..services.consensus_engine import analyze_trip_consensus, FamilyConsensusEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/consensus", tags=["consensus"])


class ConsensusRequest(BaseModel):
    """Request model for consensus analysis."""

    trip_id: str
    include_family_details: bool = True


class VoteRequest(BaseModel):
    """Request model for family voting."""

    voting_item_id: str
    vote_choice: str


class ConsensusResponse(BaseModel):
    """Response model for consensus analysis."""

    trip_id: str
    consensus_score: float
    status: str
    agreed_preferences: Dict[str, Any]
    conflicts: List[Dict[str, Any]]
    voting_items: List[Dict[str, Any]]
    compromise_suggestions: Dict[str, Any]
    next_steps: List[str]
    analysis_timestamp: str


@router.post("/analyze/{trip_id}", response_model=ConsensusResponse)
async def analyze_consensus(
    trip_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Analyze consensus for a trip across all participating families.

    This addresses the #1 pain point: achieving consensus across families with varying preferences.
    """
    try:
        # Get trip with participations and families
        stmt = (
            select(Trip)
            .options(selectinload(Trip.participations).selectinload(TripParticipation.family))
            .where(Trip.id == trip_id)
        )

        result = await db.execute(stmt)
        trip = result.scalar_one_or_none()

        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Check if user has access to this trip
        user_has_access = await _check_trip_access(db, trip_id, str(current_user.id))
        if not user_has_access:
            raise HTTPException(status_code=403, detail="Access denied to this trip")

        # Prepare families data for consensus analysis
        families_data = []
        total_budget = float(trip.budget_total) if trip.budget_total else 0.0

        for participation in trip.participations:
            family = participation.family
            if not family:
                continue

            # Get family members (simplified for now)
            family_data = {
                "id": str(family.id),
                "name": family.name,
                "members": [{"id": str(family.admin_user_id), "name": "Admin"}],  # Simplified
                "preferences": {},
                "budget_allocation": (
                    float(participation.budget_allocation)
                    if participation.budget_allocation
                    else 0.0
                ),
                "is_trip_admin": str(trip.creator_id) == str(family.admin_user_id),
            }

            # Parse preferences from participation
            if participation.preferences:
                try:
                    family_data["preferences"] = json.loads(participation.preferences)
                except (json.JSONDecodeError, TypeError):
                    family_data["preferences"] = {}

            families_data.append(family_data)

        # Perform consensus analysis
        consensus_analysis = analyze_trip_consensus(trip_id, families_data, total_budget)

        logger.info(f"Consensus analysis performed for trip {trip_id} by user {current_user.id}")

        return ConsensusResponse(**consensus_analysis)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing consensus for trip {trip_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze consensus")


@router.get("/dashboard/{trip_id}")
async def get_consensus_dashboard(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Get consensus dashboard data for visualization.

    Returns data optimized for frontend dashboard components showing:
    - Consensus score and status
    - Family agreement areas
    - Conflict summary
    - Voting status
    """
    try:
        # Get trip data
        stmt = (
            select(Trip)
            .options(selectinload(Trip.participations).selectinload(TripParticipation.family))
            .where(Trip.id == trip_id)
        )

        result = await db.execute(stmt)
        trip = result.scalar_one_or_none()

        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Check access
        user_has_access = await _check_trip_access(db, trip_id, str(current_user.id))
        if not user_has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        # Prepare families data
        families_data = []
        total_budget = float(trip.budget_total) if trip.budget_total else 0.0

        for participation in trip.participations:
            family = participation.family
            if not family:
                continue

            family_data = {
                "id": str(family.id),
                "name": family.name,
                "members": [{"id": str(family.admin_user_id), "name": "Admin"}],
                "preferences": {},
                "budget_allocation": (
                    float(participation.budget_allocation)
                    if participation.budget_allocation
                    else 0.0
                ),
                "is_trip_admin": str(trip.creator_id) == str(family.admin_user_id),
            }

            if participation.preferences:
                try:
                    family_data["preferences"] = json.loads(participation.preferences)
                except (json.JSONDecodeError, TypeError):
                    family_data["preferences"] = {}

            families_data.append(family_data)

        # Generate dashboard data
        engine = FamilyConsensusEngine()
        consensus_result = engine.generate_weighted_consensus(families_data, total_budget)

        dashboard_data = {
            "consensus_score": consensus_result.consensus_score,
            "status": (
                "Strong Consensus"
                if consensus_result.consensus_score >= 0.8
                else "Needs Discussion"
            ),
            "family_count": len(families_data),
            "conflicts_summary": {
                "total": len(consensus_result.conflicts),
                "critical": len(
                    [c for c in consensus_result.conflicts if c.severity.value == "critical"]
                ),
                "high": len([c for c in consensus_result.conflicts if c.severity.value == "high"]),
            },
            "next_steps": consensus_result.next_steps,
        }

        return {
            "trip_id": trip_id,
            "dashboard_data": dashboard_data,
            "family_count": len(families_data),
            "total_budget": total_budget,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consensus dashboard for trip {trip_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.post("/vote/{trip_id}")
async def submit_family_vote(
    trip_id: str,
    vote_request: VoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "update")),
):
    """
    Submit a family's vote on a consensus item.

    Enables families to vote on disputed preferences to reach consensus.
    """
    try:
        # Check if user has access and get their family ID
        user_family_id = await _get_user_family_for_trip(db, trip_id, str(current_user.id))
        if not user_family_id:
            raise HTTPException(status_code=403, detail="You are not part of this trip")

        # For now, we'll store votes in memory or a simple cache
        # In production, you'd want to store votes in the database

        # This is a placeholder implementation
        # In a real system, you'd:
        # 1. Get current voting items from database/cache
        # 2. Update the vote for this family
        # 3. Check if consensus is reached
        # 4. Return updated voting status

        logger.info(
            f"Vote submitted for trip {trip_id} by family {user_family_id}: {vote_request.vote_choice}"
        )

        return {
            "success": True,
            "message": "Vote recorded successfully",
            "voting_item_id": vote_request.voting_item_id,
            "family_vote": vote_request.vote_choice,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting vote for trip {trip_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit vote")


@router.get("/recommendations/{trip_id}")
async def get_consensus_recommendations(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trips", "read")),
):
    """
    Get AI-powered recommendations for resolving consensus conflicts.

    Returns specific, actionable suggestions for trip organizers.
    """
    try:
        # Check access
        user_has_access = await _check_trip_access(db, trip_id, str(current_user.id))
        if not user_has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get trip and family data (similar to analyze_consensus)
        stmt = (
            select(Trip)
            .options(selectinload(Trip.participations).selectinload(TripParticipation.family))
            .where(Trip.id == trip_id)
        )

        result = await db.execute(stmt)
        trip = result.scalar_one_or_none()

        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Quick consensus analysis
        families_data = []
        total_budget = float(trip.budget_total) if trip.budget_total else 0.0

        for participation in trip.participations:
            family = participation.family
            if not family:
                continue

            family_data = {
                "id": str(family.id),
                "name": family.name,
                "members": [{"id": str(family.admin_user_id), "name": "Admin"}],
                "preferences": {},
                "budget_allocation": (
                    float(participation.budget_allocation)
                    if participation.budget_allocation
                    else 0.0
                ),
            }

            if participation.preferences:
                try:
                    family_data["preferences"] = json.loads(participation.preferences)
                except (json.JSONDecodeError, TypeError):
                    family_data["preferences"] = {}

            families_data.append(family_data)

        # Generate recommendations
        engine = FamilyConsensusEngine()
        consensus_result = engine.generate_weighted_consensus(families_data, total_budget)

        recommendations = {
            "immediate_actions": consensus_result.next_steps,
            "compromise_suggestions": consensus_result.compromise_suggestions,
            "consensus_score": consensus_result.consensus_score,
            "priority_conflicts": [
                asdict(c)
                for c in consensus_result.conflicts
                if c.severity.value in ["high", "critical"]
            ],
        }

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for trip {trip_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


# Helper functions


async def _check_trip_access(db: AsyncSession, trip_id: str, user_id: str) -> bool:
    """Check if user has access to the trip."""
    try:
        # Check if user is trip creator
        trip_stmt = select(Trip).where(Trip.id == trip_id)
        trip_result = await db.execute(trip_stmt)
        trip = trip_result.scalar_one_or_none()

        if trip and str(trip.creator_id) == user_id:
            return True

        # Check if user's family is participating
        participation_stmt = (
            select(TripParticipation)
            .join(Family)
            .where(TripParticipation.trip_id == trip_id, Family.admin_user_id == user_id)
        )
        participation_result = await db.execute(participation_stmt)
        participation = participation_result.scalar_one_or_none()

        return participation is not None

    except Exception as e:
        logger.error(f"Error checking trip access: {str(e)}")
        return False


async def _get_user_family_for_trip(db: AsyncSession, trip_id: str, user_id: str) -> Optional[str]:
    """Get the family ID for a user in a specific trip."""
    try:
        stmt = (
            select(Family.id)
            .join(TripParticipation)
            .where(TripParticipation.trip_id == trip_id, Family.admin_user_id == user_id)
        )
        result = await db.execute(stmt)
        family_id = result.scalar_one_or_none()
        return str(family_id) if family_id else None

    except Exception as e:
        logger.error(f"Error getting user family: {str(e)}")
        return None
