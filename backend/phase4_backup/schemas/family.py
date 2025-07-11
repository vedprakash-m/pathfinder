"""Family-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FamilyCreate(BaseModel):
    """Schema for creating a new family."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class FamilyResponse(BaseModel):
    """Schema for family response."""

    id: str
    name: str
    description: Optional[str] = None
    admin_user_id: str
    members_count: int
    member_ids: List[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, doc):
        """Create response from FamilyDocument."""
        return cls(
            id=doc.id,
            name=doc.name,
            description=doc.description,
            admin_user_id=doc.admin_user_id,
            members_count=doc.members_count,
            member_ids=doc.member_ids,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class FamilyUpdate(BaseModel):
    """Schema for updating family information."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class FamilyInvitation(BaseModel):
    """Schema for family invitation."""

    invitee_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    message: Optional[str] = Field(None, max_length=500)


class FamilyMemberResponse(BaseModel):
    """Schema for family member response."""

    id: str
    family_id: str
    user_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    role: str
    created_at: datetime
