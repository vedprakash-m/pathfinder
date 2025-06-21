"""
Family management API endpoints.
Handles family creation, member management, and family-related operations.
"""

from typing import List, Optional
from datetime import datetime, timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from ..core.zero_trust import require_permissions
from ..core.security import get_current_user
from ..models.user import User
from ..models.family import (
    Family,
    FamilyMember,
    FamilyRole,
    FamilyInvitationModel,
    InvitationStatus,
    FamilyCreate,
    FamilyUpdate,
    FamilyResponse,
    FamilyMemberCreate,
    FamilyMemberUpdate,
    FamilyMemberResponse,
    FamilyInvitationCreate,
    FamilyInvitationResponse,
)
from ..core.logging_config import get_logger

router = APIRouter(tags=["families"])
logger = get_logger(__name__)


@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    request: Request,
    family_data: FamilyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "create")),
):
    """Create a new family."""
    try:
        # Check if user already has a family with the same name
        existing_family = (
            db.query(Family)
            .filter(
                and_(
                    Family.name == family_data.name,
                    Family.members.any(FamilyMember.user_id == current_user.id),
                )
            )
            .first()
        )

        if existing_family:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Family with this name already exists for user",
            )

        # Create family
        family = Family(**family_data.dict())
        db.add(family)
        db.flush()  # Get the family ID

        # Add creator as admin
        family_member = FamilyMember(
            family_id=family.id,
            user_id=current_user.id,
            role=FamilyRole.ADMIN,
            is_primary_contact=True,
        )
        db.add(family_member)
        db.commit()
        db.refresh(family)

        logger.info(f"Family created: {family.id} by user: {current_user.id}")
        return family

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating family: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create family"
        )


@router.get("/", response_model=List[FamilyResponse])
async def get_user_families(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get all families for the current user."""
    try:
        families = (
            db.query(Family)
            .join(FamilyMember)
            .filter(FamilyMember.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        return families

    except Exception as e:
        logger.error(f"Error fetching user families: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch families"
        )


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    request: Request,
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get a specific family by ID."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is a member of this family
        membership = (
            db.query(FamilyMember)
            .filter(
                and_(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id)
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this family"
            )

        return family

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch family"
        )


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: int,
    family_data: FamilyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "update")),
):
    """Update a family (admin only)."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is admin of this family
        membership = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.role == FamilyRole.ADMIN,
                )
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admins can update family details",
            )

        # Update family
        update_data = family_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(family, field, value)

        db.commit()
        db.refresh(family)

        logger.info(f"Family updated: {family_id} by user: {current_user.id}")
        return family

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update family"
        )


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "delete")),
):
    """Delete a family (admin only)."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is admin of this family
        membership = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.role == FamilyRole.ADMIN,
                )
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only family admins can delete family"
            )

        # Delete family (cascade will handle members)
        db.delete(family)
        db.commit()

        logger.info(f"Family deleted: {family_id} by user: {current_user.id}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete family"
        )


# Family Member Management Endpoints


@router.post(
    "/{family_id}/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED
)
async def add_family_member(
    family_id: int,
    member_data: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "update")),
):
    """Add a member to a family (admin only)."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if user is admin of this family
        admin_membership = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.role == FamilyRole.ADMIN,
                )
            )
            .first()
        )

        if not admin_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only family admins can add members"
            )

        # Check if user exists
        user = db.query(User).filter(User.id == member_data.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if user is already a member
        existing_membership = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id, FamilyMember.user_id == member_data.user_id
                )
            )
            .first()
        )

        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this family",
            )

        # Create family member
        family_member = FamilyMember(family_id=family_id, **member_data.dict())
        db.add(family_member)
        db.commit()
        db.refresh(family_member)

        logger.info(f"Family member added: {member_data.user_id} to family: {family_id}")
        return family_member

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding family member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add family member"
        )


@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get all members of a family."""
    try:
        # Check if user is a member of this family
        membership = (
            db.query(FamilyMember)
            .filter(
                and_(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id)
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this family"
            )

        members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()

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
    family_id: int,
    member_id: int,
    member_data: FamilyMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "update")),
):
    """Update a family member (admin only, or self for limited fields)."""
    try:
        family_member = (
            db.query(FamilyMember)
            .filter(and_(FamilyMember.id == member_id, FamilyMember.family_id == family_id))
            .first()
        )

        if not family_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found"
            )

        # Check permissions
        is_admin = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.role == FamilyRole.ADMIN,
                )
            )
            .first()
        )

        is_self = family_member.user_id == current_user.id

        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this family member",
            )

        # If not admin, restrict updateable fields
        update_data = member_data.dict(exclude_unset=True)
        if not is_admin and is_self:
            # Regular members can only update emergency contact
            allowed_fields = ["emergency_contact_name", "emergency_contact_phone"]
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        # Update family member
        for field, value in update_data.items():
            setattr(family_member, field, value)

        db.commit()
        db.refresh(family_member)

        logger.info(f"Family member updated: {member_id} by user: {current_user.id}")
        return family_member

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating family member {member_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update family member",
        )


@router.delete("/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_family_member(
    family_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from a family (admin only, or self)."""
    try:
        family_member = (
            db.query(FamilyMember)
            .filter(and_(FamilyMember.id == member_id, FamilyMember.family_id == family_id))
            .first()
        )

        if not family_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Family member not found"
            )

        # Check permissions
        is_admin = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.role == FamilyRole.ADMIN,
                )
            )
            .first()
        )

        is_self = family_member.user_id == current_user.id

        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this family member",
            )

        # Prevent removing the last admin
        if family_member.role == FamilyRole.ADMIN:
            admin_count = (
                db.query(FamilyMember)
                .filter(
                    and_(FamilyMember.family_id == family_id, FamilyMember.role == FamilyRole.ADMIN)
                )
                .count()
            )

            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin from the family",
                )

        # Remove family member
        db.delete(family_member)
        db.commit()

        logger.info(f"Family member removed: {member_id} from family: {family_id}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "manage")),
):
    """Invite a member to join a family."""
    try:
        # Verify family exists and user has permission to invite
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if current user is admin or has invite permissions
        user_membership = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.user_id == current_user.id,
                    FamilyMember.role.in_([FamilyRole.COORDINATOR, FamilyRole.ADULT]),
                )
            )
            .first()
        )

        if not user_membership and family.admin_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite members",
            )

        # Check if email is already a family member
        existing_member = (
            db.query(FamilyMember)
            .join(User)
            .filter(and_(FamilyMember.family_id == family_id, User.email == invitation_data.email))
            .first()
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User is already a family member"
            )

        # Check if there's already a pending invitation
        existing_invitation = (
            db.query(FamilyInvitationModel)
            .filter(
                and_(
                    FamilyInvitationModel.family_id == family_id,
                    FamilyInvitationModel.email == invitation_data.email,
                    FamilyInvitationModel.status == InvitationStatus.PENDING,
                )
            )
            .first()
        )

        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation already pending for this email",
            )

        # Generate invitation token and expiry
        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days to accept

        # Create invitation
        invitation = FamilyInvitationModel(
            family_id=family_id,
            invited_by=current_user.id,
            email=invitation_data.email,
            role=invitation_data.role,
            status=InvitationStatus.PENDING,
            invitation_token=invitation_token,
            message=invitation_data.message,
            expires_at=expires_at,
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

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
        db.rollback()
        logger.error(f"Error creating family invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create invitation"
        )


@router.post("/accept-invitation", status_code=status.HTTP_200_OK)
async def accept_family_invitation(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a family invitation."""
    try:
        # Find the invitation
        invitation = (
            db.query(FamilyInvitationModel)
            .filter(FamilyInvitationModel.invitation_token == token)
            .first()
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        # Check if invitation is still valid
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is no longer valid"
            )

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired"
            )

        # Verify email matches
        if invitation.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is not for this user"
            )

        # Check if user is already a family member
        existing_member = (
            db.query(FamilyMember)
            .filter(
                and_(
                    FamilyMember.family_id == invitation.family_id,
                    FamilyMember.user_id == current_user.id,
                )
            )
            .first()
        )

        if existing_member:
            # Update invitation status and return success
            invitation.status = InvitationStatus.ACCEPTED
            invitation.accepted_at = datetime.utcnow()
            db.commit()
            return {"message": "Already a member of this family"}

        # Create family member
        family_member = FamilyMember(
            family_id=invitation.family_id,
            user_id=current_user.id,
            name=current_user.name or current_user.email,
            role=invitation.role,
        )

        # Update invitation status
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()

        db.add(family_member)
        db.commit()

        logger.info(f"Family invitation accepted: {invitation.id} by user: {current_user.id}")
        return {"message": "Successfully joined family"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error accepting family invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to accept invitation"
        )


@router.post("/decline-invitation", status_code=status.HTTP_200_OK)
async def decline_family_invitation(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Decline a family invitation."""
    try:
        # Find the invitation
        invitation = (
            db.query(FamilyInvitationModel)
            .filter(FamilyInvitationModel.invitation_token == token)
            .first()
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found"
            )

        # Check if invitation is still valid
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is no longer valid"
            )

        # Verify email matches
        if invitation.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invitation is not for this user"
            )

        # Update invitation status
        invitation.status = InvitationStatus.DECLINED
        db.commit()

        logger.info(f"Family invitation declined: {invitation.id} by user: {current_user.id}")
        return {"message": "Invitation declined"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error declining family invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decline invitation"
        )


@router.get("/{family_id}/invitations", response_model=List[FamilyInvitationResponse])
async def get_family_invitations(
    request: Request,
    family_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("families", "read")),
):
    """Get all invitations for a family."""
    try:
        # Verify family exists and user has permission
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Family not found")

        # Check if current user is admin or family member
        user_membership = (
            db.query(FamilyMember)
            .filter(
                and_(FamilyMember.family_id == family_id, FamilyMember.user_id == current_user.id)
            )
            .first()
        )

        if not user_membership and family.admin_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view invitations",
            )

        # Get invitations
        invitations = (
            db.query(FamilyInvitationModel)
            .filter(FamilyInvitationModel.family_id == family_id)
            .order_by(FamilyInvitationModel.created_at.desc())
            .all()
        )

        return invitations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch invitations"
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
