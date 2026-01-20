"""
Notification Service

Handles in-app notifications and real-time message delivery.
"""
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from models.documents import BaseDocument
from repositories.cosmos_repository import CosmosRepository


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class NotificationType(str, Enum):
    """Types of notifications."""

    TRIP_CREATED = "trip_created"
    TRIP_UPDATED = "trip_updated"
    TRIP_CANCELLED = "trip_cancelled"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    INVITATION_RECEIVED = "invitation_received"
    INVITATION_ACCEPTED = "invitation_accepted"
    INVITATION_DECLINED = "invitation_declined"
    POLL_CREATED = "poll_created"
    POLL_CLOSED = "poll_closed"
    VOTE_RECEIVED = "vote_received"
    ITINERARY_READY = "itinerary_ready"
    ITINERARY_APPROVED = "itinerary_approved"
    MESSAGE_RECEIVED = "message_received"
    CONSENSUS_REACHED = "consensus_reached"


class NotificationDocument(BaseDocument):
    """Notification document for Cosmos DB."""

    entity_type: str = "notification"
    user_id: str
    title: str
    body: str
    notification_type: NotificationType
    trip_id: Optional[str] = None
    family_id: Optional[str] = None
    action_url: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    metadata: dict[str, Any] = {}


class NotificationService:
    """Handles notification creation and delivery."""

    def __init__(self) -> None:
        self._repo: Optional[CosmosRepository] = None

    @property
    def repo(self) -> CosmosRepository:
        if self._repo is None:
            self._repo = CosmosRepository()
        return self._repo

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        trip_id: Optional[str] = None,
        family_id: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> NotificationDocument:
        """
        Create a new notification.

        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            body: Notification body text
            trip_id: Optional related trip
            family_id: Optional related family
            action_url: Optional URL to navigate to
            metadata: Optional additional data

        Returns:
            Created notification
        """
        await self.repo.initialize()

        notification = NotificationDocument(
            id=str(uuid.uuid4()),
            entity_type="notification",
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            trip_id=trip_id,
            family_id=family_id,
            action_url=action_url,
            metadata=metadata or {},
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        await self.repo.create(notification.model_dump(), notification.id)

        return notification

    async def notify_users(
        self,
        user_ids: list[str],
        notification_type: NotificationType,
        title: str,
        body: str,
        trip_id: Optional[str] = None,
        family_id: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> list[NotificationDocument]:
        """
        Send notification to multiple users.

        Args:
            user_ids: List of target user IDs
            notification_type: Type of notification
            title: Notification title
            body: Notification body text
            trip_id: Optional related trip
            family_id: Optional related family
            action_url: Optional URL to navigate to
            metadata: Optional additional data

        Returns:
            List of created notifications
        """
        notifications: list[NotificationDocument] = []

        for user_id in user_ids:
            notification = await self.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                trip_id=trip_id,
                family_id=family_id,
                action_url=action_url,
                metadata=metadata,
            )
            notifications.append(notification)

        return notifications

    async def get_user_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[NotificationDocument]:
        """
        Get notifications for a user.

        Args:
            user_id: Target user ID
            unread_only: Only return unread notifications
            limit: Maximum notifications to return
            offset: Pagination offset

        Returns:
            List of notifications
        """
        await self.repo.initialize()

        conditions = ["c.entity_type = 'notification'", f"c.user_id = '{user_id}'"]

        if unread_only:
            conditions.append("c.is_read = false")

        query = f"""
            SELECT * FROM c
            WHERE {' AND '.join(conditions)}
            ORDER BY c.created_at DESC
            OFFSET {offset} LIMIT {limit}
        """

        results = await self.repo.query(query)
        return [NotificationDocument(**n) for n in results]

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications.

        Args:
            user_id: Target user ID

        Returns:
            Count of unread notifications
        """
        await self.repo.initialize()

        query = f"""
            SELECT VALUE COUNT(1) FROM c
            WHERE c.entity_type = 'notification'
            AND c.user_id = '{user_id}'
            AND c.is_read = false
        """

        return await self.repo.count(query)

    async def mark_as_read(self, notification_id: str, user_id: str) -> Optional[NotificationDocument]:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)

        Returns:
            Updated notification or None
        """
        await self.repo.initialize()

        # Get existing notification
        notification_dict = await self.repo.get_by_id(notification_id, notification_id)
        if not notification_dict:
            return None

        # Verify ownership
        if notification_dict.get("user_id") != user_id:
            return None

        # Update
        now = utc_now()
        notification_dict["is_read"] = True
        notification_dict["read_at"] = now.isoformat()
        notification_dict["updated_at"] = now.isoformat()

        await self.repo.update(notification_id, notification_dict, notification_id)

        return NotificationDocument(**notification_dict)

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: Target user ID

        Returns:
            Number of notifications marked as read
        """
        await self.repo.initialize()

        # Get all unread
        query = f"""
            SELECT * FROM c
            WHERE c.entity_type = 'notification'
            AND c.user_id = '{user_id}'
            AND c.is_read = false
        """

        results = await self.repo.query(query)
        now = utc_now()
        marked = 0

        for notification in results:
            notification["is_read"] = True
            notification["read_at"] = now.isoformat()
            notification["updated_at"] = now.isoformat()
            await self.repo.update(notification["id"], notification, notification["id"])
            marked += 1

        return marked

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)

        Returns:
            True if deleted
        """
        await self.repo.initialize()

        # Verify ownership first
        notification = await self.repo.get_by_id(notification_id, notification_id)
        if not notification or notification.get("user_id") != user_id:
            return False

        await self.repo.delete(notification_id, notification_id)
        return True


# Notification helper functions for common scenarios


async def notify_trip_created(
    service: NotificationService, trip_id: str, trip_name: str, creator_name: str, member_ids: list[str]
) -> list[NotificationDocument]:
    """Notify members when a trip is created."""
    return await service.notify_users(
        user_ids=member_ids,
        notification_type=NotificationType.TRIP_CREATED,
        title="New Trip Created",
        body=f"{creator_name} created a new trip: {trip_name}",
        trip_id=trip_id,
        action_url=f"/trips/{trip_id}",
    )


async def notify_invitation_received(
    service: NotificationService, user_id: str, family_name: str, inviter_name: str, invitation_id: str
) -> NotificationDocument:
    """Notify user of family invitation."""
    return await service.create_notification(
        user_id=user_id,
        notification_type=NotificationType.INVITATION_RECEIVED,
        title="Family Invitation",
        body=f"{inviter_name} invited you to join {family_name}",
        action_url=f"/invitations/{invitation_id}",
    )


async def notify_itinerary_ready(
    service: NotificationService, trip_id: str, trip_name: str, member_ids: list[str]
) -> list[NotificationDocument]:
    """Notify members when itinerary is generated."""
    return await service.notify_users(
        user_ids=member_ids,
        notification_type=NotificationType.ITINERARY_READY,
        title="Itinerary Ready",
        body=f"The itinerary for {trip_name} is ready for review!",
        trip_id=trip_id,
        action_url=f"/trips/{trip_id}/itinerary",
    )


async def notify_poll_created(
    service: NotificationService, trip_id: str, poll_title: str, creator_name: str, member_ids: list[str]
) -> list[NotificationDocument]:
    """Notify members when a poll is created."""
    return await service.notify_users(
        user_ids=member_ids,
        notification_type=NotificationType.POLL_CREATED,
        title="New Poll",
        body=f"{creator_name} created a poll: {poll_title}",
        trip_id=trip_id,
        action_url=f"/trips/{trip_id}/collaboration",
    )


# Service singleton
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get or create notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
