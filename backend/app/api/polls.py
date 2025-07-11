from __future__ import annotations

"""
API endpoints for Magic Polls system.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.security import get_current_user
from app.models.cosmos.user import UserDocument
from app.services.cosmos_service import CosmosService
from app.schemas.common import SuccessResponse, ErrorResponse
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.core.database_unified import get_cosmos_service
from app.schemas.poll import PollCreate, PollResponse, PollVote

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_cosmos_repo() -> UnifiedCosmosRepository:
    """Get Cosmos repository dependency."""
    cosmos_service = get_cosmos_service()
    return cosmos_service.get_repository()


@router.post("/", response_model=PollResponse)
async def create_poll(
    poll_data: PollCreate,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Create a new poll for a trip."""
    try:
        # Create poll document
        poll_doc = {
            "id": f"poll_{poll_data.trip_id}_{datetime.now().timestamp()}",
            "trip_id": poll_data.trip_id,
            "creator_id": current_user.id,
            "title": poll_data.title,
            "description": poll_data.description,
            "poll_type": poll_data.poll_type,
            "options": poll_data.options,
            "votes": {},
            "expires_at": poll_data.expires_at,
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Save to Cosmos DB
        await cosmos_repo.create_document(poll_doc)

        return PollResponse(**poll_doc)

    except Exception as e:
        logger.error(f"Error creating poll: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to create poll: {str(e)}")


@router.get("/trip/{trip_id}", response_model=List[PollResponse])
async def get_trip_polls(
    trip_id: str,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Get all polls for a trip."""
    try:
        # Query poll documents for trip
        poll_docs = await cosmos_repo.query_documents(
            f"SELECT * FROM c WHERE c.trip_id = '{trip_id}' AND c.type = 'poll'"
        )

        return [PollResponse(**doc) for doc in poll_docs]

    except Exception as e:
        logger.error(f"Error getting trip polls: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get polls: {str(e)}")


@router.post("/{poll_id}/vote", response_model=SuccessResponse)
async def vote_poll(
    poll_id: str,
    vote_data: PollVote,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Vote on a poll."""
    try:
        # Get poll document
        poll_doc = await cosmos_repo.get_document(poll_id)
        if not poll_doc:
            raise HTTPException(status_code=404, detail="Poll not found")

        # Add vote
        poll_doc["votes"][current_user.id] = {
            "option_indices": vote_data.option_indices,
            "voted_at": datetime.now(),
        }

        # Update document
        await cosmos_repo.update_document(poll_id, poll_doc)

        return SuccessResponse(message="Vote recorded successfully")

    except Exception as e:
        logger.error(f"Error voting on poll: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to vote: {str(e)}")


@router.get("/{poll_id}/results", response_model=Dict[str, Any])
async def get_poll_results(
    poll_id: str,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Get poll results."""
    try:
        # Get poll document
        poll_doc = await cosmos_repo.get_document(poll_id)
        if not poll_doc:
            raise HTTPException(status_code=404, detail="Poll not found")

        # Calculate results
        results = {
            "poll_id": poll_id,
            "total_votes": len(poll_doc["votes"]),
            "options": poll_doc["options"],
            "vote_distribution": {},
            "status": poll_doc["status"],
        }

        # Calculate vote distribution
        for option_idx, option in enumerate(poll_doc["options"]):
            vote_count = sum(
                1
                for vote in poll_doc["votes"].values()
                if option_idx in vote["option_indices"]
            )
            results["vote_distribution"][option] = vote_count

        return results

    except Exception as e:
        logger.error(f"Error getting poll results: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to get results: {str(e)}")
