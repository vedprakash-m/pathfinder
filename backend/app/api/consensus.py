from __future__ import annotations

"""
API endpoints for Family Consensus Engine.

Solves the #1 pain point: "Lack of mechanism to achieve consensus on optimal plans across families"
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.security import get_current_user
from app.models.cosmos.user import UserDocument
from app.models.cosmos.enums import UserRole, TripStatus
from app.services.cosmos_service import CosmosService
from app.schemas.common import SuccessResponse, ErrorResponse, PaginationRequest
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.core.database_unified import get_cosmos_service
from app.schemas.consensus import ConsensusCreate, ConsensusResponse, ConsensusVote

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_cosmos_repo() -> UnifiedCosmosRepository:
    """Get Cosmos repository dependency."""
    cosmos_service = get_cosmos_service()
    return cosmos_service.get_repository()


@router.post("/", response_model=ConsensusResponse)
async def create_consensus(
    consensus_data: ConsensusCreate,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Create a new consensus poll for a trip."""
    try:
        # Create consensus document
        consensus_doc = {
            "id": f"consensus_{consensus_data.trip_id}_{datetime.now().timestamp()}",
            "trip_id": consensus_data.trip_id,
            "title": consensus_data.title,
            "description": consensus_data.description,
            "options": consensus_data.options,
            "responses": {},
            "status": "active",
            "created_by": current_user.id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Save to Cosmos DB
        await cosmos_repo.create_document(consensus_doc)

        return ConsensusResponse(**consensus_doc)

    except Exception as e:
        logger.error(f"Error creating consensus: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to create consensus: {str(e)}"
        )


@router.get("/trip/{trip_id}", response_model=List[ConsensusResponse])
async def get_trip_consensus(
    trip_id: str,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Get all consensus polls for a trip."""
    try:
        # Query consensus documents for trip
        consensus_docs = await cosmos_repo.query_documents(
            f"SELECT * FROM c WHERE c.trip_id = '{trip_id}' AND c.type = 'consensus'"
        )

        return [ConsensusResponse(**doc) for doc in consensus_docs]

    except Exception as e:
        logger.error(f"Error getting trip consensus: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to get consensus: {str(e)}"
        )


@router.post("/{consensus_id}/vote", response_model=SuccessResponse)
async def vote_consensus(
    consensus_id: str,
    vote_data: ConsensusVote,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Vote on a consensus poll."""
    try:
        # Get consensus document
        consensus_doc = await cosmos_repo.get_document(consensus_id)
        if not consensus_doc:
            raise HTTPException(status_code=404, detail="Consensus not found")

        # Add vote
        consensus_doc["responses"][current_user.id] = {
            "option_index": vote_data.option_index,
            "weight": vote_data.weight,
            "comment": vote_data.comment,
            "voted_at": datetime.now(),
        }

        # Update document
        await cosmos_repo.update_document(consensus_id, consensus_doc)

        return SuccessResponse(message="Vote recorded successfully")

    except Exception as e:
        logger.error(f"Error voting on consensus: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to vote: {str(e)}")


@router.get("/{consensus_id}/results", response_model=Dict[str, Any])
async def get_consensus_results(
    consensus_id: str,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Get consensus results and analysis."""
    try:
        # Get consensus document
        consensus_doc = await cosmos_repo.get_document(consensus_id)
        if not consensus_doc:
            raise HTTPException(status_code=404, detail="Consensus not found")

        # Calculate results
        results = {
            "consensus_id": consensus_id,
            "total_votes": len(consensus_doc["responses"]),
            "options": consensus_doc["options"],
            "vote_distribution": {},
            "analysis": {
                "status": "active",
                "consensus_score": 0.0,
                "recommendations": [],
            },
        }

        # Calculate vote distribution
        for option_idx, option in enumerate(consensus_doc["options"]):
            vote_count = sum(
                1
                for vote in consensus_doc["responses"].values()
                if vote["option_index"] == option_idx
            )
            results["vote_distribution"][option] = vote_count

        return results

    except Exception as e:
        logger.error(f"Error getting consensus results: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get results: {str(e)}")
