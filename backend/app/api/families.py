"""
Family management API endpoints - Unified Cosmos DB Implementation.
Handles family creation, member management, and family-related operations.
"""

import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..core.database_unified import get_cosmos_repository
from ..core.logging_config import get_logger
from ..core.security import get_current_user
from ..core.zero_trust import require_permissions
from ..repositories.cosmos_unified import UnifiedCosmosRepository
from ..models.family import (
    Family,
    FamilyCreate,
    FamilyInvitationCreate,
    FamilyInvitationModel,
    FamilyInvitationResponse,
    FamilyMember,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    FamilyResponse,
    FamilyRole,
    FamilyUpdate,
    InvitationStatus,
)
from ..models.user import User

router = APIRouter(tags=["families"])
logger = get_logger(__name__)


@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    request: Request,
    family_data: FamilyCreate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "create")),
):
    """Create a new family using unified Cosmos DB."""
    try:
        # Check if user already has a family with the same name
        user_families = await cosmos_repo.get_user_families(str(current_user.id))
        existing_family = next(
            (f for f in user_families if f.name == family_data.name), None
        )

        if existing_family:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Family with this name already exists for user",
            )

        # Create family document
        family_data_dict = family_data.dict()
        family_data_dict.update({
            "admin_user_id": str(current_user.id),
            "member_ids": [str(current_user.id)]  # Creator is first member
        })
        
        family_doc = await cosmos_repo.create_family(family_data_dict)
        
        # Add user to family's member list
        await cosmos_repo.add_user_to_family(str(current_user.id), family_doc.id)

        logger.info(f"Family created: {family_doc.id} by user: {current_user.id}")
        
        # Convert Cosmos document to response model
        return FamilyResponse(
            id=family_doc.id,
            name=family_doc.name,
            description=family_doc.description,
            admin_user_id=family_doc.admin_user_id,
            members_count=family_doc.members_count,
            created_at=family_doc.created_at,
            updated_at=family_doc.updated_at
        )

    except Exception as e:
        logger.error(f"Error creating family: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create family",
        )


@router.get("/", response_model=List[FamilyResponse])
async def get_user_families(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get all families for the current user."""
    try:
        families = await cosmos_repo.get_user_families(str(current_user.id))
        
        # Apply pagination
        paginated_families = families[skip:skip + limit] if limit > 0 else families[skip:]
        
        # Convert to response models
        return [
            FamilyResponse(
                id=family.id,
                name=family.name,
                description=family.description,
                admin_user_id=family.admin_user_id,
                members_count=family.members_count,
                created_at=family.created_at,
                updated_at=family.updated_at
            )
            for family in paginated_families
        ]

    except Exception as e:
        logger.error(f"Error fetching user families: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch families",
        )


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    request: Request,
    family_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get a specific family by ID."""
    try:
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is a member of this family
        user_families = await cosmos_repo.get_user_families(str(current_user.id))
        is_member = any(f.id == family_id for f in user_families)

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this family",
            )

        return FamilyResponse(
            id=family.id,
            name=family.name,
            description=family.description,
            admin_user_id=family.admin_user_id,
            members_count=family.members_count,
            created_at=family.created_at,
            updated_at=family.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch family",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch family",
        )


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: str,
    family_data: FamilyUpdate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "update")),
):
    """Update a family (admin only)."""
    try:
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is admin of this family
        if family.admin_user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admin can update family",
            )

        # Update family data
        update_data = family_data.dict(exclude_unset=True)
        updated_family = await cosmos_repo.update_family(family_id, update_data)

        logger.info(f"Family updated: {family_id} by user: {current_user.id}")
        
        return FamilyResponse(
            id=updated_family.id,
            name=updated_family.name,
            description=updated_family.description,
            admin_user_id=updated_family.admin_user_id,
            members_count=updated_family.members_count,
            created_at=updated_family.created_at,
            updated_at=updated_family.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update family",
        )


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "delete")),
):
    """Delete a family (admin only)."""
    try:
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is admin of this family
        if family.admin_user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admins can delete family",
            )

        # Delete family
        await cosmos_repo.delete_family(family_id)

        logger.info(f"Family deleted: {family_id} by user: {current_user.id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete family",
        )


# Family Member Management Endpoints


@router.post(
    "/{family_id}/members",
    response_model=FamilyMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_family_member(
    family_id: str,
    member_data: FamilyMemberCreate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "update")),
):
    """Add a member to a family (admin only) using unified Cosmos DB."""
    try:
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is admin of this family
        if family.admin_user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admins can add members",
            )

        # Check if user exists
        user = await cosmos_repo.get_user(str(member_data.user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if user is already a member
        user_families = await cosmos_repo.get_user_families(str(member_data.user_id))
        is_already_member = any(f.id == family_id for f in user_families)

        if is_already_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this family",
            )

        # Add user to family
        await cosmos_repo.add_user_to_family(str(member_data.user_id), family_id)

        logger.info(f"Family member added: {member_data.user_id} to family: {family_id}")
        
        # Return member response
        return FamilyMemberResponse(
            id=str(member_data.user_id),
            user_id=str(member_data.user_id),
            family_id=family_id,
            role=member_data.role or FamilyRole.MEMBER,
            joined_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding family member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add family member",
        )


@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    family_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get all members of a family using unified Cosmos DB."""
    try:
        # Check if user is a member of this family
        user_families = await cosmos_repo.get_user_families(str(current_user.id))
        is_member = any(f.id == family_id for f in user_families)

        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this family",
            )

        # Get family to access member list
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Get details for each member
        members = []
        for member_id in family.member_ids:
            user = await cosmos_repo.get_user(member_id)
            if user:
                role = FamilyRole.ADMIN if member_id == family.admin_user_id else FamilyRole.MEMBER
                members.append(FamilyMemberResponse(
                    id=member_id,
                    user_id=member_id,
                    family_id=family_id,
                    role=role,
                    joined_at=family.created_at  # Simplified for now
                ))

        return members

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family members for family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch family members",
        )


@router.put("/{family_id}/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    family_id: str,
    member_id: str,
    member_data: FamilyMemberUpdate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "update")),
):
    """Update a family member (admin only, or self for limited fields) using unified Cosmos DB."""
    try:
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if member exists in family
        if member_id not in family.member_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found"
            )

        # Check permissions
        is_admin = family.admin_user_id == str(current_user.id)
        is_self = member_id == str(current_user.id)

        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this family member",
            )

        # For simplified unified Cosmos approach, we can mainly update roles
        # Other member-specific data could be stored in user documents
        update_data = member_data.dict(exclude_unset=True)
        
        # If updating role and user is admin
        if "role" in update_data and is_admin:
            if update_data["role"] == FamilyRole.ADMIN:
                # Transfer admin role
                await cosmos_repo.update_family(family_id, {"admin_user_id": member_id})
            # Note: In simplified approach, role is derived from admin_user_id
        
        # For now, return the updated member info
        user = await cosmos_repo.get_user(member_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        role = FamilyRole.ADMIN if member_id == family.admin_user_id else FamilyRole.MEMBER

        logger.info(f"Family member updated: {member_id} by user: {current_user.id}")
        
        return FamilyMemberResponse(
            id=member_id,
            user_id=member_id,
            family_id=family_id,
            role=role,
            joined_at=family.created_at  # Simplified for now
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating family member {member_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update family member",
        )


@router.delete("/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_family_member(
    family_id: str,
    member_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from a family (admin only, or self) using unified Cosmos DB."""
    try:
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if member exists in family
        if member_id not in family.member_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found"
            )

        # Check permissions
        is_admin = family.admin_user_id == str(current_user.id)
        is_self = member_id == str(current_user.id)

        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this family member",
            )

        # Prevent removing the last admin (admin removing themselves)
        if member_id == family.admin_user_id and len(family.member_ids) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the admin from the family. Transfer admin role first.",
            )

        # Remove member from family
        await cosmos_repo.remove_user_from_family(member_id, family_id)

        logger.info(f"Family member removed: {member_id} from family: {family_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing family member {member_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove family member",
        )


# Family Invitation Endpoints


@router.post(
    "/{family_id}/invite",
    response_model=FamilyInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_family_member(
    request: Request,
    family_id: str,
    invitation_data: FamilyInvitationCreate,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "manage")),
):
    """Invite a member to join a family using unified Cosmos DB."""
    try:
        # Verify family exists
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if current user is admin or has invite permissions
        user_membership = await cosmos_repo.get_family_member(family_id, str(current_user.id))
        has_invite_permission = (
            user_membership and user_membership.role in [FamilyRole.COORDINATOR, FamilyRole.ADULT]
        ) or family.admin_user_id == str(current_user.id)

        if not has_invite_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite members",
            )

        # Check if email is already a family member
        family_members = await cosmos_repo.get_family_members(family_id)
        for member in family_members:
            user = await cosmos_repo.get_user(str(member.user_id))
            if user and user.email == invitation_data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already a family member",
                )

        # Check if there's already a pending invitation
        existing_invitations = await cosmos_repo.get_family_invitations(family_id)
        for invitation in existing_invitations:
            if (invitation.email == invitation_data.email and 
                invitation.status == InvitationStatus.PENDING):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Invitation already pending for this email",
                )

        # Generate invitation token and expiry
        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days to accept

        # Create invitation using Cosmos DB
        invitation_data_dict = {
            "family_id": family_id,
            "invited_by": str(current_user.id),
            "email": invitation_data.email,
            "role": invitation_data.role,
            "status": InvitationStatus.PENDING,
            "invitation_token": invitation_token,
            "message": invitation_data.message,
            "expires_at": expires_at,
        }

        invitation = await cosmos_repo.create_family_invitation(invitation_data_dict)

        # Send invitation email
        try:
            await send_family_invitation_email(
                to_email=invitation_data.email,
                family_name=family.name,
                inviter_name=current_user.name or current_user.email,
                invitation_token=invitation_token,
                message=invitation_data.message,
            )
        except Exception as email_error:
            logger.warning(f"Failed to send invitation email: {email_error}")
            # Don't fail the invitation creation if email fails

        logger.info(f"Family invitation created: {invitation.id} for family: {family_id}")
        return invitation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating family invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation",
        )


@router.post("/accept-invitation", status_code=status.HTTP_200_OK)
async def accept_family_invitation(
    request: Request,
    token: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(get_current_user),
):
    """Accept a family invitation using unified Cosmos DB."""
    try:
        # Find the invitation
        invitation = await cosmos_repo.get_family_invitation_by_token(token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        # Check if invitation is still valid
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer valid",
            )

        if invitation.expires_at < datetime.utcnow():
            # Update invitation status to expired
            await cosmos_repo.update_family_invitation(
                invitation.id, {"status": InvitationStatus.EXPIRED}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
            )

        # Verify email matches
        if invitation.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation is not for this user",
            )

        # Check if user is already a family member
        existing_member = await cosmos_repo.get_family_member(
            invitation.family_id, str(current_user.id)
        )

        if existing_member:
            # Update invitation status and return success
            await cosmos_repo.update_family_invitation(
                invitation.id, 
                {"status": InvitationStatus.ACCEPTED, "accepted_at": datetime.utcnow()}
            )
            return {"message": "Already a member of this family"}

        # Create family member
        family_member_data = {
            "family_id": invitation.family_id,
            "user_id": str(current_user.id),
            "name": current_user.name or current_user.email,
            "role": invitation.role,
        }

        await cosmos_repo.create_family_member(family_member_data)

        # Update invitation status
        await cosmos_repo.update_family_invitation(
            invitation.id,
            {"status": InvitationStatus.ACCEPTED, "accepted_at": datetime.utcnow()}
        )

        logger.info(f"Family invitation accepted: {invitation.id} by user: {current_user.id}")
        return {"message": "Successfully joined family"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting family invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation",
        )


@router.post("/decline-invitation", status_code=status.HTTP_200_OK)
async def decline_family_invitation(
    request: Request,
    token: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(get_current_user),
):
    """Decline a family invitation using unified Cosmos DB."""
    try:
        # Find the invitation
        invitation = await cosmos_repo.get_family_invitation_by_token(token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        # Check if invitation is still valid
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer valid",
            )

        # Verify email matches
        if invitation.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation is not for this user",
            )

        # Update invitation status
        await cosmos_repo.update_family_invitation(
            invitation.id, {"status": InvitationStatus.DECLINED}
        )

        logger.info(f"Family invitation declined: {invitation.id} by user: {current_user.id}")
        return {"message": "Invitation declined"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error declining family invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decline invitation",
        )


@router.get("/{family_id}/invitations", response_model=List[FamilyInvitationResponse])
async def get_family_invitations(
    request: Request,
    family_id: str,
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get all invitations for a family using unified Cosmos DB."""
    try:
        # Verify family exists
        family = await cosmos_repo.get_family(family_id)
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if current user is admin or family member
        user_membership = await cosmos_repo.get_family_member(family_id, str(current_user.id))
        has_access = user_membership or family.admin_user_id == str(current_user.id)

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view invitations",
            )

        # Get invitations
        invitations = await cosmos_repo.get_family_invitations(family_id)
        
        # Sort by created_at descending
        invitations.sort(key=lambda x: x.created_at, reverse=True)

        return invitations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invitations",
        )


async def send_family_invitation_email(
    to_email: str,
    family_name: str,
    inviter_name: str,
    invitation_token: str,
    message: Optional[str] = None,
):
    """Send family invitation email."""
    from ..services.email_service import email_service

    # Create invitation URL (this would be configurable)
    invitation_url = f"https://pathfinder.app/accept-invitation?token={invitation_token}"

    success = await email_service.send_family_invitation(
        recipient_email=to_email,
        family_name=family_name,
        inviter_name=inviter_name,
        invitation_link=invitation_url,
        message=message,
    )

    if not success:
        logger.warning(f"Failed to send family invitation email to {to_email}")

    return success
