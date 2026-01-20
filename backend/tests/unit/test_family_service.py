"""Unit tests for FamilyService."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from services.family_service import FamilyService


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_notification_service():
    """Create a mock notification service."""
    service = AsyncMock()
    return service


@pytest.fixture
def family_service(mock_repository, mock_notification_service):
    """Create a family service with mocked dependencies."""
    with patch("services.family_service.CosmosRepository") as MockRepo, patch(
        "services.family_service.NotificationService"
    ) as MockNotif:
        MockRepo.return_value = mock_repository
        MockNotif.return_value = mock_notification_service
        service = FamilyService()
        service.repository = mock_repository
        service.notification_service = mock_notification_service
        return service


class TestFamilyService:
    """Test cases for FamilyService."""

    @pytest.mark.asyncio
    async def test_create_family(self, family_service, mock_repository):
        """Test creating a family."""
        mock_repository.create = AsyncMock(
            return_value={
                "id": "family_123",
                "pk": "family_123",
                "entity_type": "family",
                "name": "Smith Family",
                "owner_id": "user_1",
                "member_ids": ["user_1"],
                "created_at": datetime.now(UTC).isoformat(),
            }
        )

        result = await family_service.create_family(name="Smith Family", owner_id="user_1")

        assert result["name"] == "Smith Family"
        assert result["owner_id"] == "user_1"
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_family(self, family_service, mock_repository):
        """Test getting a family by ID."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "family_123",
                "pk": "family_123",
                "entity_type": "family",
                "name": "Smith Family",
            }
        )

        result = await family_service.get_family("family_123")

        assert result["id"] == "family_123"
        mock_repository.get_by_id.assert_called_once_with("family_123", "family_123")

    @pytest.mark.asyncio
    async def test_invite_member(self, family_service, mock_repository, mock_notification_service):
        """Test inviting a member to a family."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "family_123",
                "name": "Smith Family",
                "owner_id": "user_1",
                "member_ids": ["user_1"],
            }
        )
        mock_repository.create = AsyncMock(
            return_value={
                "id": "invitation_123",
                "pk": "invitation_123",
                "entity_type": "invitation",
                "family_id": "family_123",
                "inviter_id": "user_1",
                "invitee_email": "john@example.com",
                "status": "pending",
            }
        )

        result = await family_service.invite_member(
            family_id="family_123", inviter_id="user_1", invitee_email="john@example.com"
        )

        assert result["invitee_email"] == "john@example.com"
        assert result["status"] == "pending"
        mock_repository.create.assert_called()

    @pytest.mark.asyncio
    async def test_accept_invitation(self, family_service, mock_repository):
        """Test accepting a family invitation."""
        mock_repository.get_by_id = AsyncMock(
            side_effect=[
                # Invitation
                {
                    "id": "invitation_123",
                    "pk": "invitation_123",
                    "entity_type": "invitation",
                    "family_id": "family_123",
                    "invitee_email": "john@example.com",
                    "status": "pending",
                },
                # Family
                {
                    "id": "family_123",
                    "pk": "family_123",
                    "entity_type": "family",
                    "name": "Smith Family",
                    "member_ids": ["user_1"],
                },
            ]
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "family_123",
                "member_ids": ["user_1", "user_2"],
            }
        )

        result = await family_service.accept_invitation(invitation_id="invitation_123", user_id="user_2")

        assert "user_2" in result["member_ids"]

    @pytest.mark.asyncio
    async def test_remove_member(self, family_service, mock_repository):
        """Test removing a member from a family."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "family_123",
                "pk": "family_123",
                "entity_type": "family",
                "name": "Smith Family",
                "owner_id": "user_1",
                "member_ids": ["user_1", "user_2", "user_3"],
            }
        )
        mock_repository.update = AsyncMock(
            return_value={
                "id": "family_123",
                "member_ids": ["user_1", "user_3"],
            }
        )

        result = await family_service.remove_member(family_id="family_123", member_id="user_2", requester_id="user_1")

        assert "user_2" not in result["member_ids"]

    @pytest.mark.asyncio
    async def test_remove_member_unauthorized(self, family_service, mock_repository):
        """Test that non-owner cannot remove members."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "family_123",
                "owner_id": "user_1",
                "member_ids": ["user_1", "user_2", "user_3"],
            }
        )

        with pytest.raises(PermissionError):
            await family_service.remove_member(
                family_id="family_123",
                member_id="user_3",
                requester_id="user_2",  # Not the owner
            )

    @pytest.mark.asyncio
    async def test_get_family_members(self, family_service, mock_repository):
        """Test getting all members of a family."""
        mock_repository.get_by_id = AsyncMock(
            return_value={
                "id": "family_123",
                "member_ids": ["user_1", "user_2"],
            }
        )
        mock_repository.query = AsyncMock(
            return_value=[
                {"id": "user_1", "display_name": "John", "email": "john@example.com"},
                {"id": "user_2", "display_name": "Jane", "email": "jane@example.com"},
            ]
        )

        results = await family_service.get_family_members("family_123")

        assert len(results) == 2
        assert results[0]["display_name"] == "John"
