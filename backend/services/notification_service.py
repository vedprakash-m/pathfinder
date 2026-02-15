"""
Notification Service

Handles in-app notifications and real-time message delivery.
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from models.documents import NotificationDocument
from repositories.cosmos_repository import cosmos_repo

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class NotificationType(StrEnum):
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


class NotificationService:
    """Handles notification creation and delivery."""

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        trip_id: str | None = None,
        family_id: str | None = None,
        action_url: str | None = None,
        metadata: dict[str, Any] | None = None,
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
        notification = NotificationDocument(
            pk=f"notification_{user_id}",
            user_id=user_id,
            notification_type=notification_type.value,
            title=title,
            body=body,
            trip_id=trip_id,
            family_id=family_id,
            action_url=action_url,
            metadata=metadata or {},
        )

        created = await cosmos_repo.create(notification)
        return created

    async def notify_users(
        self,
        user_ids: list[str],
        notification_type: NotificationType,
        title: str,
        body: str,
        trip_id: str | None = None,
        family_id: str | None = None,
        action_url: str | None = None,
        metadata: dict[str, Any] | None = None,
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
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'notification'
            AND c.user_id = @userId
        """
        params = [{"name": "@userId", "value": user_id}]

        if unread_only:
            query += " AND c.is_read = false"

        query += " ORDER BY c.created_at DESC"

        results = await cosmos_repo.query(
            query=query, parameters=params, model_class=NotificationDocument, max_items=limit
        )

        return results[offset:] if offset else results

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications.

        Args:
            user_id: Target user ID

        Returns:
            Count of unread notifications
        """
        query = """
            SELECT VALUE COUNT(1) FROM c
            WHERE c.entity_type = 'notification'
            AND c.user_id = @userId
            AND c.is_read = false
        """
        params = [{"name": "@userId", "value": user_id}]

        return await cosmos_repo.count(query=query, parameters=params)

    async def mark_as_read(self, notification_id: str, user_id: str) -> NotificationDocument | None:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)

        Returns:
            Updated notification or None
        """
        pk = f"notification_{user_id}"
        notification = await cosmos_repo.get_by_id(notification_id, pk, NotificationDocument)

        if not notification:
            return None

        # Verify ownership
        if notification.user_id != user_id:
            return None

        notification.is_read = True
        notification.read_at = utc_now()

        return await cosmos_repo.update(notification)

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: Target user ID

        Returns:
            Number of notifications marked as read
        """
        query = """
            SELECT * FROM c
            WHERE c.entity_type = 'notification'
            AND c.user_id = @userId
            AND c.is_read = false
        """
        params = [{"name": "@userId", "value": user_id}]

        results = await cosmos_repo.query(query=query, parameters=params, model_class=NotificationDocument)

        marked = 0
        now = utc_now()

        for notification in results:
            notification.is_read = True
            notification.read_at = now
            await cosmos_repo.update(notification)
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
        pk = f"notification_{user_id}"
        notification = await cosmos_repo.get_by_id(notification_id, pk, NotificationDocument)

        if not notification or notification.user_id != user_id:
            return False

        return await cosmos_repo.delete(notification_id, pk)


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
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
