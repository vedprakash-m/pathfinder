from __future__ import annotations
"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.consensus import ConsensusCreate, ConsensusResponse, ConsensusVote
API endpoints for Family Consensus Engine.

Solves the #1 pain point: "Lack of mechanism to achieve consensus on optimal plans across families"
"""

import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..core.ai_cost_management import ai_cost_control
from ..core.database_unified import get_cosmos_repository
from ..core.zero_trust import require_permissions
# SQL User model removed - use Cosmos UserDocument
from ..repositories.cosmos_unified import UnifiedCosmosRepository
from ..services.consensus_engine import FamilyConsensusEngine, analyze_trip_consensus

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
agreed_preferences: dict[str, Any]
conflicts: list[dict[str, Any]]
voting_items: list[dict[str, Any]]
compromise_suggestions: dict[str, Any]
next_steps: list[str]
analysis_timestamp: str


@router.post("/analyze/(trip_id)", response_model=ConsensusResponse)
@ai_cost_control(model="gpt-4", max_tokens=2500)
async def analyze_consensus(
    trip_id: str,
request: Request,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("trips", "read")
):
    """
Analyze consensus for a trip across all participating families.

This addresses the #1 pain point: achieving consensus across families with varying preferences."""
"""
try:
        # Get trip from Cosmos DB
trip = await cosmos_repo.get_trip(trip_id)
if not trip:"""
raise HTTPException(status_code=404, detail="Trip not found")

# Check access permissions
has_access = await _check_trip_access_cosmos(cosmos_repo, trip_id, str(current_user.id))
if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to this trip")

# Get participating families
family_ids = trip.participating_family_ids
families = []
for family_id in family_ids:
            family = await cosmos_repo.get_family(family_id)
if family:
                families.append(family)

# Prepare families data for consensus analysis
families_data = []
total_budget = float(trip.budget) if trip.budget else 0.0

for family in families:
            # Get family members from Cosmos DB
family_members = await cosmos_repo.get_family_members(family.id)

family_data = {
                "id": family.id,
"name": family.name,
"members": [
("id": str(member.id), "name": member.name or "Unknown")
for member in family_members
],
"preferences": family.settings or(),
"budget_allocation": 0.0,  # TODO: Get from trip participation data
"is_trip_admin": trip.creator_id == family.admin_user_id,
)

families_data.append(family_data)

# Perform consensus analysis
consensus_analysis = analyze_trip_consensus(trip_id, families_data, total_budget)

logger.info(f"Consensus analysis performed for trip(trip_id) by user(current_user.id)")

return ConsensusResponse(**consensus_analysis)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error analyzing consensus for trip(trip_id): (str(e))")
raise HTTPException(status_code=500, detail="Failed to analyze consensus")


@router.get("/dashboard/(trip_id)")
async def get_consensus_dashboard(
    trip_id: str,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("trips", "read")
):
    """
Get consensus dashboard data for visualization using unified Cosmos DB.

Returns data optimized for frontend dashboard components showing:
    - Consensus score and status
- Family agreement areas
- Conflict summary
- Voting status"""
"""
try:
        # Get trip from Cosmos DB
trip = await cosmos_repo.get_trip(trip_id)
if not trip:"""
raise HTTPException(status_code=404, detail="Trip not found")

# Check access
has_access = await _check_trip_access_cosmos(cosmos_repo, trip_id, str(current_user.id))
if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

# Get participating families
family_ids = trip.participating_family_ids
families = []
for family_id in family_ids:
            family = await cosmos_repo.get_family(family_id)
if family:
                families.append(family)

# Prepare families data
families_data = []
total_budget = float(trip.budget) if trip.budget else 0.0

for family in families:
            # Get family members from Cosmos DB
family_members = await cosmos_repo.get_family_members(family.id)

family_data = {
                "id": family.id,
"name": family.name,
"members": [
("id": str(member.id), "name": member.name or "Unknown")
for member in family_members
],
"preferences": family.settings or(),
"budget_allocation": 0.0,  # TODO: Get from trip participation data
"is_trip_admin": trip.creator_id == family.admin_user_id,
)

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
"conflicts_summary": (
                "total": len(consensus_result.conflicts),
"critical": len(
                    [c for c in consensus_result.conflicts if c.severity.value == "critical"]
),
"high": len([c for c in consensus_result.conflicts if c.severity.value == "high"]),
),
"next_steps": consensus_result.next_steps,
)

return(
            "trip_id": trip_id,
"dashboard_data": dashboard_data,
"family_count": len(families_data),
"total_budget": total_budget,
)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error getting consensus dashboard for trip(trip_id): (str(e))")
raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.post("/vote/(trip_id)")
async def submit_family_vote(
    trip_id: str,
vote_request: VoteRequest,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("trips", "update")
):
    """
Submit a family's vote on a consensus item using unified Cosmos DB.

Enables families to vote on disputed preferences to reach consensus."""
"""
try:
        # Check if user has access and get their family ID
user_family_id = await _get_user_family_for_trip_cosmos(
            cosmos_repo, trip_id, str(current_user.id)
)
if not user_family_id:"""
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
            f"Vote submitted for trip(trip_id) by family(user_family_id): (vote_request.vote_choice)"
)

return(
            "success": True,
"message": "Vote recorded successfully",
"voting_item_id": vote_request.voting_item_id,
"family_vote": vote_request.vote_choice,
)

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error submitting vote for trip(trip_id): (str(e))")
raise HTTPException(status_code=500, detail="Failed to submit vote")


@router.get("/recommendations/(trip_id)")
@ai_cost_control(model="gpt-3.5-turbo", max_tokens=1500)
async def get_consensus_recommendations(
    trip_id: str,
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),:
    current_user: User = Depends(require_permissions("trips", "read")
):
    """
Get AI-powered recommendations for resolving consensus conflicts using unified Cosmos DB.

Returns specific, actionable suggestions for trip organizers."""
"""
try:
        # Check access
has_access = await _check_trip_access_cosmos(cosmos_repo, trip_id, str(current_user.id))
if not has_access:"""
raise HTTPException(status_code=403, detail="Access denied")

# Get trip from Cosmos DB
trip = await cosmos_repo.get_trip(trip_id)
if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

# Get participating families
family_ids = trip.participating_family_ids
families = []
for family_id in family_ids:
            family = await cosmos_repo.get_family(family_id)
if family:
                families.append(family)

# Quick consensus analysis
families_data = []
total_budget = float(trip.budget) if trip.budget else 0.0

for family in families:
            # Get family members from Cosmos DB
family_members = await cosmos_repo.get_family_members(family.id)

family_data = {
                "id": family.id,
"name": family.name,
"members": [
("id": str(member.id), "name": member.name or "Unknown")
for member in family_members
],
"preferences": family.settings or(),
"budget_allocation": 0.0,  # TODO: Get from trip participation data
)

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
)

return recommendations

except HTTPException:
        raise
except Exception as e:
        logger.error(f"Error getting recommendations for trip(trip_id): (str(e))")
raise HTTPException(status_code=500, detail="Failed to get recommendations")


# Helper functions


async def _check_trip_access_cosmos(
    cosmos_repo: UnifiedCosmosRepository, trip_id: str, user_id: str:
    ) -> bool:
    """Check if user has access to a specific trip using Cosmos DB."""
try:
        # Get user's families
user_families = await cosmos_repo.get_user_families(user_id)
user_family_ids = [family.id for family in user_families]

# Get trip
trip = await cosmos_repo.get_trip(trip_id)
if not trip:
            return False

# Check if user is trip creator
if trip.creator_id == user_id:
            return True

# Check if any user family is participating in the trip
participating_families = trip.participating_family_ids
return any(family_id in participating_families for family_id in user_family_ids)

except Exception as e:
        logger.error(f"Error checking trip access: (str(e))")
return False


async def _get_user_family_for_trip_cosmos(
    cosmos_repo: UnifiedCosmosRepository, trip_id: str, user_id: str:
    ) -> Optional[str]:
    """Get the family ID for a user in a specific trip using Cosmos DB."""
try:
        # Get user's families
user_families = await cosmos_repo.get_user_families(user_id)

# Get trip
trip = await cosmos_repo.get_trip(trip_id)
if not trip:
            return None

# Find which family is participating in this trip
participating_families = trip.participating_family_ids
for family in user_families:
            if family.id in participating_families:
                return family.id

return None

except Exception as e:
        logger.error(f"Error getting user family: (str(e))")
return None
