"""
Family management API endpoints.
Handles family creation, member management, and family-related operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import get_db
from ..core.security import get_current_user, require_permission
from ..models.user import User
from ..models.family import Family, FamilyMember, FamilyRole, FamilyCreate, FamilyUpdate, FamilyResponse, FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse
from ..core.logging_config import get_logger

router = APIRouter(tags=["families"])
logger = get_logger(__name__)


@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family(
    family_data: FamilyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new family."""
    try:
        # Check if user already has a family with the same name
        existing_family = db.query(Family).filter(
            and_(
                Family.name == family_data.name,
                Family.members.any(FamilyMember.user_id == current_user.id)
            )
        ).first()
        
        if existing_family:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Family with this name already exists for user"
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
            is_primary_contact=True
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create family"
        )


@router.get("/", response_model=List[FamilyResponse])
async def get_user_families(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all families for the current user."""
    try:
        families = db.query(Family).join(FamilyMember).filter(
            FamilyMember.user_id == current_user.id
        ).offset(skip).limit(limit).all()
        
        return families
        
    except Exception as e:
        logger.error(f"Error fetching user families: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch families"
        )


@router.get("/{family_id}", response_model=FamilyResponse)
async def get_family(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific family by ID."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Check if user is a member of this family
        membership = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id
            )
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this family"
            )
        
        return family
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch family"
        )


@router.put("/{family_id}", response_model=FamilyResponse)
async def update_family(
    family_id: int,
    family_data: FamilyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a family (admin only)."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Check if user is admin of this family
        membership = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == FamilyRole.ADMIN
            )
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admins can update family details"
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update family"
        )


@router.delete("/{family_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a family (admin only)."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Check if user is admin of this family
        membership = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == FamilyRole.ADMIN
            )
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admins can delete family"
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete family"
        )


# Family Member Management Endpoints

@router.post("/{family_id}/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_family_member(
    family_id: int,
    member_data: FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a family (admin only)."""
    try:
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family not found"
            )
        
        # Check if user is admin of this family
        admin_membership = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == FamilyRole.ADMIN
            )
        ).first()
        
        if not admin_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only family admins can add members"
            )
        
        # Check if user exists
        user = db.query(User).filter(User.id == member_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is already a member
        existing_membership = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == member_data.user_id
            )
        ).first()
        
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this family"
            )
        
        # Create family member
        family_member = FamilyMember(
            family_id=family_id,
            **member_data.dict()
        )
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add family member"
        )


@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a family."""
    try:
        # Check if user is a member of this family
        membership = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id
            )
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this family"
            )
        
        members = db.query(FamilyMember).filter(
            FamilyMember.family_id == family_id
        ).all()
        
        return members
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching family members for family {family_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch family members"
        )


@router.put("/{family_id}/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    family_id: int,
    member_id: int,
    member_data: FamilyMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a family member (admin only, or self for limited fields)."""
    try:
        family_member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id
            )
        ).first()
        
        if not family_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family member not found"
            )
        
        # Check permissions
        is_admin = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == FamilyRole.ADMIN
            )
        ).first()
        
        is_self = family_member.user_id == current_user.id
        
        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this family member"
            )
        
        # If not admin, restrict updateable fields
        update_data = member_data.dict(exclude_unset=True)
        if not is_admin and is_self:
            # Regular members can only update emergency contact
            allowed_fields = ['emergency_contact_name', 'emergency_contact_phone']
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
            detail="Failed to update family member"
        )


@router.delete("/{family_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_family_member(
    family_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a family (admin only, or self)."""
    try:
        family_member = db.query(FamilyMember).filter(
            and_(
                FamilyMember.id == member_id,
                FamilyMember.family_id == family_id
            )
        ).first()
        
        if not family_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family member not found"
            )
        
        # Check permissions
        is_admin = db.query(FamilyMember).filter(
            and_(
                FamilyMember.family_id == family_id,
                FamilyMember.user_id == current_user.id,
                FamilyMember.role == FamilyRole.ADMIN
            )
        ).first()
        
        is_self = family_member.user_id == current_user.id
        
        if not (is_admin or is_self):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to remove this family member"
            )
        
        # Prevent removing the last admin
        if family_member.role == FamilyRole.ADMIN:
            admin_count = db.query(FamilyMember).filter(
                and_(
                    FamilyMember.family_id == family_id,
                    FamilyMember.role == FamilyRole.ADMIN
                )
            ).count()
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin from the family"
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
            detail="Failed to remove family member"
        )