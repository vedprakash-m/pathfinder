"""
Family Service

Business logic for family management operations.
"""
import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

from models.documents import FamilyDocument, InvitationDocument, UserDocument
from models.schemas import FamilyCreate, FamilyUpdate
from repositories.cosmos_repository import cosmos_repo

logger = logging.getLogger(__name__)


class FamilyService:
    """Service for family-related operations."""

    async def create_family(self, data: FamilyCreate, user: UserDocument) -> FamilyDocument:
        """
        Create a new family with the user as admin.

        Args:
            data: Family creation data
            user: Authenticated user creating the family

        Returns:
            Created family document
        """
        family = FamilyDocument(
            pk=f"family_{user.id}",
            name=data.name,
            description=data.description,
            admin_user_id=user.id,
            member_ids=[user.id],
            member_count=1,
        )

        created = await cosmos_repo.create(family)

        # Add family to user's family_ids
        if created.id not in user.family_ids:
            user.family_ids.append(created.id)
            await cosmos_repo.update(user)

        logger.info(f"Created family '{created.name}' by user {user.id}")
        return created

    async def get_family(self, family_id: str) -> Optional[FamilyDocument]:
        """
        Get a family by ID.

        Args:
            family_id: Family ID

        Returns:
            Family document if found
        """
        query = "SELECT * FROM c WHERE c.entity_type = 'family' AND c.id = @familyId"
        families = await cosmos_repo.query(
            query=query, parameters=[{"name": "@familyId", "value": family_id}], model_class=FamilyDocument, max_items=1
        )

        return families[0] if families else None

    async def get_user_families(self, user_id: str, limit: int = 20) -> list[FamilyDocument]:
        """
        Get all families a user belongs to.

        Args:
            user_id: User ID
            limit: Maximum families to return

        Returns:
            List of family documents
        """
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'family'
            AND ARRAY_CONTAINS(c.member_ids, @userId)
            ORDER BY c.created_at DESC
        """

        return await cosmos_repo.query(
            query=query, parameters=[{"name": "@userId", "value": user_id}], model_class=FamilyDocument, max_items=limit
        )

    async def update_family(self, family_id: str, data: FamilyUpdate, user: UserDocument) -> Optional[FamilyDocument]:
        """
        Update a family.

        Args:
            family_id: Family ID
            data: Update data
            user: Authenticated user

        Returns:
            Updated family or None if not found/unauthorized
        """
        family = await self.get_family(family_id)

        if not family:
            return None

        # Only admin can update
        if family.admin_user_id != user.id:
            logger.warning(f"User {user.id} cannot update family {family_id}")
            return None

        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(family, field) and value is not None:
                setattr(family, field, value)

        updated = await cosmos_repo.update(family)
        logger.info(f"Updated family {family_id} by user {user.id}")

        return updated

    async def delete_family(self, family_id: str, user: UserDocument) -> bool:
        """
        Delete a family.

        Args:
            family_id: Family ID
            user: Authenticated user

        Returns:
            True if deleted, False otherwise
        """
        family = await self.get_family(family_id)

        if not family:
            return False

        # Only admin can delete
        if family.admin_user_id != user.id:
            logger.warning(f"User {user.id} cannot delete family {family_id}")
            return False

        # Remove family from all members' family_ids
        for member_id in family.member_ids:
            await self._remove_family_from_user(member_id, family_id)

        deleted = await cosmos_repo.delete(family_id, family.pk)

        if deleted:
            logger.info(f"Deleted family {family_id} by user {user.id}")

        return deleted

    async def invite_member(
        self, family_id: str, email: str, role: str, user: UserDocument
    ) -> Optional[InvitationDocument]:
        """
        Create an invitation to join a family.

        Args:
            family_id: Family ID
            email: Email to invite
            role: Role for the invitee
            user: Authenticated user (inviter)

        Returns:
            Created invitation or None
        """
        family = await self.get_family(family_id)

        if not family:
            return None

        # Only admin can invite
        if family.admin_user_id != user.id:
            logger.warning(f"User {user.id} cannot invite to family {family_id}")
            return None

        invitation = InvitationDocument(
            pk=f"invitation_{family_id}",
            family_id=family_id,
            family_name=family.name,
            inviter_id=user.id,
            inviter_name=user.name or user.email,
            email=email,
            role=role,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        created = await cosmos_repo.create(invitation)
        logger.info(f"Created invitation for {email} to family {family_id}")

        return created

    async def accept_invitation(self, token: str, user: UserDocument) -> Optional[FamilyDocument]:
        """
        Accept a family invitation.

        Args:
            token: Invitation token
            user: Authenticated user accepting

        Returns:
            Family joined or None
        """
        # Find invitation by token
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'invitation'
            AND c.token = @token
            AND c.status = 'pending'
        """
        invitations = await cosmos_repo.query(
            query=query, parameters=[{"name": "@token", "value": token}], model_class=InvitationDocument, max_items=1
        )

        if not invitations:
            logger.warning(f"Invalid invitation token: {token}")
            return None

        invitation = invitations[0]

        # Check if expired
        if invitation.expires_at < datetime.now(UTC):
            invitation.status = "expired"
            await cosmos_repo.update(invitation)
            return None

        # Check email matches
        if invitation.email.lower() != user.email.lower():
            logger.warning(f"Email mismatch for invitation: {invitation.email} vs {user.email}")
            return None

        # Add user to family
        family = await self.get_family(invitation.family_id)
        if not family:
            return None

        if user.id not in family.member_ids:
            family.member_ids.append(user.id)
            family.member_count = len(family.member_ids)
            await cosmos_repo.update(family)

        # Add family to user
        if family.id not in user.family_ids:
            user.family_ids.append(family.id)
            await cosmos_repo.update(user)

        # Mark invitation as accepted
        invitation.status = "accepted"
        await cosmos_repo.update(invitation)

        logger.info(f"User {user.id} joined family {family.id}")
        return family

    async def remove_member(self, family_id: str, member_id: str, user: UserDocument) -> bool:
        """
        Remove a member from a family.

        Args:
            family_id: Family ID
            member_id: Member to remove
            user: Authenticated user (admin)

        Returns:
            True if removed
        """
        family = await self.get_family(family_id)

        if not family:
            return False

        # Only admin can remove, or member can remove themselves
        if family.admin_user_id != user.id and user.id != member_id:
            return False

        # Cannot remove admin
        if member_id == family.admin_user_id:
            logger.warning("Cannot remove family admin")
            return False

        if member_id in family.member_ids:
            family.member_ids.remove(member_id)
            family.member_count = len(family.member_ids)
            await cosmos_repo.update(family)
            await self._remove_family_from_user(member_id, family_id)
            logger.info(f"Removed {member_id} from family {family_id}")
            return True

        return False

    async def get_family_members(self, family_id: str) -> list[UserDocument]:
        """
        Get all members of a family.

        Args:
            family_id: Family ID

        Returns:
            List of user documents
        """
        family = await self.get_family(family_id)
        if not family:
            return []

        if not family.member_ids:
            return []

        # Query users by IDs
        placeholders = ", ".join(f"@id{i}" for i in range(len(family.member_ids)))
        query = f"SELECT * FROM c WHERE c.entity_type = 'user' AND c.id IN ({placeholders})"
        params = [{"name": f"@id{i}", "value": mid} for i, mid in enumerate(family.member_ids)]

        return await cosmos_repo.query(query=query, parameters=params, model_class=UserDocument)

    def user_is_member(self, family: FamilyDocument, user_id: str) -> bool:
        """Check if user is a member of the family."""
        return user_id in family.member_ids

    def user_is_admin(self, family: FamilyDocument, user_id: str) -> bool:
        """Check if user is the admin of the family."""
        return family.admin_user_id == user_id

    async def _remove_family_from_user(self, user_id: str, family_id: str) -> None:
        """Remove family from user's family_ids list."""
        query = "SELECT * FROM c WHERE c.entity_type = 'user' AND c.id = @userId"
        users = await cosmos_repo.query(
            query=query, parameters=[{"name": "@userId", "value": user_id}], model_class=UserDocument, max_items=1
        )

        if users and family_id in users[0].family_ids:
            users[0].family_ids.remove(family_id)
            await cosmos_repo.update(users[0])
