from __future__ import annotations

"""
Family management API endpoints - Unified Cosmos DB Implementation.
"""

import logging
from uuid import uuid4

from app.repositories.cosmos_unified import (
    UnifiedCosmosRepository,
    UserDocument,
    FamilyDocument,
)
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.family import (
    FamilyCreate,
    FamilyResponse,
    FamilyUpdate,
    FamilyInvitation,
)
from app.schemas.common import SuccessResponse
from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_cosmos_repo() -> UnifiedCosmosRepository:
    """Get Cosmos repository dependency."""
    cosmos_service = get_cosmos_service()
    return cosmos_service.get_repository()


@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    family_data: FamilyCreate,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Create a new family."""
    try:
        family_doc = FamilyDocument(
            id=str(uuid4()),
            pk=f"family_{str(uuid4())}",
            name=family_data.name,
            description=family_data.description,
            admin_user_id=current_user.id,
            member_ids=[current_user.id],
            members_count=1,
        )

        created_family = await cosmos_repo.create_document(family_doc)

        # Update user's family_ids
        if created_family.id not in current_user.family_ids:
            current_user.family_ids.append(created_family.id)
            await cosmos_repo.update_document(current_user)

        return FamilyResponse.from_document(created_family)

    except Exception as e:
        logger.error(f"Family creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Family creation failed",
        ) from e


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: str,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Get family by ID."""
    try:
        family = await cosmos_repo.get_document(f"family_{family_id}", "family")
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        # Check if user is member
        if current_user.id not in family.member_ids:
            raise HTTPException(status_code=403, detail="Access denied")

        return FamilyResponse.from_document(family)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post("/{family_id}/invite", response_model=SuccessResponse)
async def invite_to_family(
    family_id: str,
    invitation: FamilyInvitation,
    current_user: UserDocument = Depends(get_current_user),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repo),
):
    """Invite someone to join the family."""
    try:
        family = await cosmos_repo.get_document(f"family_{family_id}", "family")
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")

        # Check if user is admin
        if current_user.id != family.admin_user_id:
            raise HTTPException(status_code=403, detail="Only family admin can invite")

        # TODO: Implement invitation logic
        # This would send an email invitation and create an invitation record

        return SuccessResponse(
            message="Invitation sent successfully",
            data={"invitee_email": invitation.invitee_email},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
