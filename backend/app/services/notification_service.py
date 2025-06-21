"""
Notification service for managing real-time notifications and messaging.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, and_, or_, desc, func

from app.core.logging_config import get_logger
from app.models.notification import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    BulkNotificationCreate,
    NotificationFilters,
    NotificationStats,
)
from app.services.websocket import ConnectionManager
from app.services.email_service import email_service

logger = get_logger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, db: AsyncSession, websocket_manager: Optional[ConnectionManager] = None):
        self.db = db
        self.websocket_manager = websocket_manager

    async def send_admin_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send administrative alerts for cost monitoring and system issues."""
        try:
            # Get all admin users (this would typically come from a role-based system)
            admin_users = await self._get_admin_users()

            alert_notification = NotificationCreate(
                user_id=None,  # Will be set for each admin
                type=NotificationType.SYSTEM_ALERT,
                priority=NotificationPriority.HIGH
                if alert_data.get("severity") == "high"
                else NotificationPriority.MEDIUM,
                title=f"System Alert: {alert_data.get('type', 'Unknown')}",
                message=alert_data.get("message", "System alert triggered"),
                data=alert_data,
            )

            # Send to all admins
            for admin_user_id in admin_users:
                alert_notification.user_id = admin_user_id
                await self.create_notification(alert_notification)

            logger.info(
                f"Admin alert sent to {len(admin_users)} administrators",
                alert_type=alert_data.get("type"),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send admin alert: {str(e)}")
            return False

    async def _get_admin_users(self) -> List[str]:
        """Get list of admin user IDs. This is a placeholder - implement based on your auth system."""
        # This would typically query your user roles/permissions system
        # For now, return empty list - implement based on your specific auth setup
        return []

    async def send_cost_threshold_alert(
        self, service: str, current_usage: float, threshold: float, percentage: float
    ):
        """Send cost threshold alerts to administrators."""
        alert_data = {
            "type": "cost_threshold_exceeded",
            "service": service,
            "current_usage": current_usage,
            "threshold": threshold,
            "percentage": percentage,
            "severity": "high" if percentage > 95 else "medium",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Cost threshold alert: {service} is at {percentage:.1f}% of limit ({current_usage:.2f}/{threshold:.2f})",
        }

        return await self.send_admin_alert(alert_data)

    async def send_system_health_alert(self, metric: str, value: float, threshold: float):
        """Send system health alerts."""
        alert_data = {
            "type": "system_health_alert",
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "severity": "high" if value > threshold * 1.2 else "medium",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"System health alert: {metric} is at {value:.2f} (threshold: {threshold:.2f})",
        }

        return await self.send_admin_alert(alert_data)

    async def create_notification(
        self, notification_data: NotificationCreate
    ) -> NotificationResponse:
        """Create a new notification."""
        try:
            # Create notification instance
            notification = Notification(
                user_id=notification_data.user_id,
                type=notification_data.type,
                priority=notification_data.priority,
                title=notification_data.title,
                message=notification_data.message,
                trip_id=notification_data.trip_id,
                family_id=notification_data.family_id,
                data=json.dumps(notification_data.data) if notification_data.data else None,
                expires_at=notification_data.expires_at,
            )

            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)

            response = self._build_notification_response(notification)

            # Send real-time notification
            if self.websocket_manager:
                await self._send_real_time_notification(str(notification_data.user_id), response)

            # Send email notification based on type and user preferences
            await self._send_email_notification(notification, response)

            logger.info(f"Notification created: {notification.id}")
            return response

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification: {str(e)}")
            raise ValueError(f"Failed to create notification: {str(e)}")

    async def create_bulk_notifications(
        self, bulk_data: BulkNotificationCreate
    ) -> List[NotificationResponse]:
        """Create notifications for multiple users."""
        try:
            notifications = []
            responses = []

            for user_id in bulk_data.user_ids:
                notification = Notification(
                    user_id=user_id,
                    type=bulk_data.type,
                    priority=bulk_data.priority,
                    title=bulk_data.title,
                    message=bulk_data.message,
                    trip_id=bulk_data.trip_id,
                    family_id=bulk_data.family_id,
                    data=json.dumps(bulk_data.data) if bulk_data.data else None,
                    expires_at=bulk_data.expires_at,
                )
                notifications.append(notification)
                self.db.add(notification)

            await self.db.commit()

            # Build responses and send real-time notifications
            for notification in notifications:
                await self.db.refresh(notification)
                response = self._build_notification_response(notification)
                responses.append(response)

                # Send real-time notification
                if self.websocket_manager:
                    await self._send_real_time_notification(str(notification.user_id), response)

            logger.info(f"Bulk notifications created for {len(bulk_data.user_ids)} users")
            return responses

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating bulk notifications: {str(e)}")
            raise ValueError(f"Failed to create bulk notifications: {str(e)}")

    async def get_user_notifications(
        self, user_id: str, skip: int = 0, limit: int = 50, unread_only: bool = False
    ) -> List[NotificationResponse]:
        """Get notifications for a user."""
        try:
            query = select(Notification).where(Notification.user_id == UUID(user_id))

            # Filter by read status if requested
            if unread_only:
                query = query.where(Notification.is_read == False)

            # Filter out expired notifications
            query = query.where(
                (Notification.expires_at.is_(None))
                | (Notification.expires_at > datetime.now(timezone.utc))
            )

            # Order by creation date (newest first) and apply pagination
            query = query.order_by(desc(Notification.created_at)).offset(skip).limit(limit)

            result = await self.db.execute(query)
            notifications = result.scalars().all()

            # Build responses
            responses = [self._build_notification_response(n) for n in notifications]

            return responses

        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            return []

    async def mark_notification_read(
        self, notification_id: str, user_id: str
    ) -> Optional[NotificationResponse]:
        """Mark a notification as read."""
        try:
            # Get notification and verify ownership
            query = select(Notification).where(
                Notification.id == UUID(notification_id), Notification.user_id == UUID(user_id)
            )

            result = await self.db.execute(query)
            notification = result.scalar_one_or_none()

            if not notification:
                return None

            # Mark as read
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(notification)

            response = self._build_notification_response(notification)

            logger.info(f"Notification marked as read: {notification_id}")
            return response

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking notification as read: {str(e)}")
            return None

    async def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all unread notifications as read for a user."""
        try:
            # Update all unread notifications
            result = await self.db.execute(
                update(Notification)
                .where(and_(Notification.user_id == UUID(user_id), Notification.is_read == False))
                .values(is_read=True, read_at=datetime.now(timezone.utc))
                .returning(Notification.id)
            )

            updated_count = len(result.fetchall())
            await self.db.commit()

            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
            return updated_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking all notifications as read: {str(e)}")
            return 0

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        try:
            result = await self.db.execute(
                delete(Notification).where(
                    and_(
                        Notification.id == UUID(notification_id),
                        Notification.user_id == UUID(user_id),
                    )
                )
            )

            deleted_count = result.rowcount
            await self.db.commit()

            if deleted_count > 0:
                logger.info(f"Notification deleted: {notification_id}")
                return True
            else:
                logger.warning(f"Notification not found or not owned by user: {notification_id}")
                return False

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting notification: {str(e)}")
            return False

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        try:
            result = await self.db.execute(
                select(func.count(Notification.id)).where(
                    and_(
                        Notification.user_id == UUID(user_id),
                        Notification.is_read == False,
                        or_(
                            Notification.expires_at.is_(None),
                            Notification.expires_at > datetime.now(timezone.utc),
                        ),
                    )
                )
            )

            count = result.scalar() or 0
            return count

        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0

    # Helper methods for specific notification types

    async def notify_trip_invitation(
        self, user_id: str, trip_name: str, inviter_name: str, trip_id: str
    ) -> None:
        """Send trip invitation notification."""
        notification_data = NotificationCreate(
            user_id=UUID(user_id),
            type=NotificationType.TRIP_INVITATION,
            priority=NotificationPriority.HIGH,
            title="Trip Invitation",
            message=f"You've been invited to join '{trip_name}' by {inviter_name}",
            trip_id=UUID(trip_id),
            data={"trip_id": trip_id, "trip_name": trip_name, "inviter": inviter_name},
        )
        await self.create_notification(notification_data)

    async def notify_trip_update(
        self, user_ids: List[str], trip_name: str, update_type: str, trip_id: str
    ) -> None:
        """Send trip update notifications."""
        bulk_data = BulkNotificationCreate(
            user_ids=[UUID(uid) for uid in user_ids],
            type=NotificationType.TRIP_UPDATE,
            priority=NotificationPriority.NORMAL,
            title="Trip Update",
            message=f"'{trip_name}' has been updated: {update_type}",
            trip_id=UUID(trip_id),
            data={"trip_id": trip_id, "trip_name": trip_name, "update_type": update_type},
        )
        await self.create_bulk_notifications(bulk_data)

    async def notify_itinerary_ready(
        self, user_ids: List[str], trip_name: str, trip_id: str
    ) -> None:
        """Send itinerary ready notifications."""
        bulk_data = BulkNotificationCreate(
            user_ids=[UUID(uid) for uid in user_ids],
            type=NotificationType.ITINERARY_READY,
            priority=NotificationPriority.HIGH,
            title="Itinerary Ready",
            message=f"The itinerary for '{trip_name}' is ready for review!",
            trip_id=UUID(trip_id),
            data={"trip_id": trip_id, "trip_name": trip_name},
        )
        await self.create_bulk_notifications(bulk_data)

    def _build_notification_response(self, notification: Notification) -> NotificationResponse:
        """Build notification response from database model."""
        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            priority=notification.priority,
            title=notification.title,
            message=notification.message,
            trip_id=notification.trip_id,
            family_id=notification.family_id,
            data=json.loads(notification.data) if notification.data else None,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at,
            expires_at=notification.expires_at,
        )

    async def _send_real_time_notification(
        self, user_id: str, notification: NotificationResponse
    ) -> None:
        """Send real-time notification via WebSocket."""
        if self.websocket_manager:
            message = {"type": "notification", "data": notification.model_dump()}
            await self.websocket_manager.send_to_user(user_id, json.dumps(message))

    async def _send_email_notification(
        self, notification: Notification, response: NotificationResponse
    ) -> None:
        """Send email notification based on type and user preferences."""
        try:
            # Get user information (this would typically come from a user service)
            user_email = await self._get_user_email(str(notification.user_id))
            user_name = await self._get_user_name(str(notification.user_id))

            if not user_email:
                logger.warning(f"No email found for user {notification.user_id}")
                return

            # Check if user has email notifications enabled for this type
            if not await self._should_send_email_notification(
                str(notification.user_id), notification.type
            ):
                logger.debug(
                    f"Email notifications disabled for user {notification.user_id}, type {notification.type}"
                )
                return

            # Send email based on notification type
            success = False
            if notification.type == NotificationType.TRIP_INVITATION:
                success = await self._send_trip_invitation_email(
                    notification, user_email, user_name
                )
            elif notification.type == NotificationType.ITINERARY_READY:
                success = await self._send_itinerary_ready_email(
                    notification, user_email, user_name
                )
            elif notification.type == NotificationType.TRIP_UPDATE:
                success = await self._send_trip_update_email(notification, user_email, user_name)
            elif notification.type in [NotificationType.SYSTEM_ANNOUNCEMENT, "SYSTEM_ALERT"]:
                success = await self._send_system_alert_email(notification, user_email, user_name)

            if success:
                logger.info(f"Email notification sent for {notification.type} to {user_email}")
            else:
                logger.warning(
                    f"Failed to send email notification for {notification.type} to {user_email}"
                )

        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")

    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email address. This is a placeholder - implement based on your user system."""
        # This would typically query your user table
        # For now, return a placeholder - implement based on your specific user setup
        try:
            from app.models.user import User

            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            return user.email if user else None
        except Exception as e:
            logger.error(f"Error getting user email: {str(e)}")
            return None

    async def _get_user_name(self, user_id: str) -> str:
        """Get user name. This is a placeholder - implement based on your user system."""
        try:
            from app.models.user import User

            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            return user.full_name if user and user.full_name else "User"
        except Exception as e:
            logger.error(f"Error getting user name: {str(e)}")
            return "User"

    async def _should_send_email_notification(
        self, user_id: str, notification_type: NotificationType
    ) -> bool:
        """Check if user has email notifications enabled for this type."""
        # This would typically check user notification preferences
        # For now, enable email for high-priority notifications
        high_priority_types = [
            NotificationType.TRIP_INVITATION,
            NotificationType.ITINERARY_READY,
            "SYSTEM_ALERT",
        ]
        return notification_type in high_priority_types

    async def _send_trip_invitation_email(
        self, notification: Notification, user_email: str, user_name: str
    ) -> bool:
        """Send trip invitation email."""
        try:
            # Parse notification data
            data = json.loads(notification.data) if notification.data else {}
            trip_name = data.get("trip_name", "Unknown Trip")
            inviter = data.get("inviter", "Someone")

            # Create invitation link (placeholder)
            invitation_link = f"https://pathfinder.com/trips/{notification.trip_id}/accept"

            trip_data = {
                "name": trip_name,
                "destination": data.get("destination", "Unknown"),
                "start_date": data.get("start_date", "TBD"),
                "end_date": data.get("end_date", "TBD"),
                "description": data.get("description", ""),
            }

            return await email_service.send_trip_invitation(
                recipient_email=user_email,
                recipient_name=user_name,
                trip_data=trip_data,
                organizer_name=inviter,
                invitation_link=invitation_link,
            )
        except Exception as e:
            logger.error(f"Error sending trip invitation email: {str(e)}")
            return False

    async def _send_itinerary_ready_email(
        self, notification: Notification, user_email: str, user_name: str
    ) -> bool:
        """Send itinerary ready email."""
        try:
            data = json.loads(notification.data) if notification.data else {}
            trip_name = data.get("trip_name", "Your Trip")

            # Create itinerary link
            itinerary_link = f"https://pathfinder.com/trips/{notification.trip_id}/itinerary"

            trip_data = {"name": trip_name, "destination": data.get("destination", "Unknown")}

            itinerary_summary = {
                "duration_days": data.get("duration_days", "Unknown"),
                "activity_count": data.get("activity_count", 0),
                "estimated_budget": data.get("estimated_budget", 0),
            }

            return await email_service.send_itinerary_ready_notification(
                recipient_email=user_email,
                recipient_name=user_name,
                trip_data=trip_data,
                itinerary_summary=itinerary_summary,
                itinerary_link=itinerary_link,
            )
        except Exception as e:
            logger.error(f"Error sending itinerary ready email: {str(e)}")
            return False

    async def _send_trip_update_email(
        self, notification: Notification, user_email: str, user_name: str
    ) -> bool:
        """Send trip update email."""
        try:
            data = json.loads(notification.data) if notification.data else {}
            trip_name = data.get("trip_name", "Your Trip")
            update_type = data.get("update_type", "updated")

            # Create trip link
            trip_link = f"https://pathfinder.com/trips/{notification.trip_id}"

            trip_data = {
                "name": trip_name,
                "destination": data.get("destination", "Unknown"),
                "start_date": data.get("start_date", "TBD"),
            }

            return await email_service.send_trip_reminder(
                recipient_email=user_email,
                recipient_name=user_name,
                trip_data=trip_data,
                days_until=0,  # Not applicable for updates
                completion_percentage=100,  # Placeholder
                action_items=[f"Trip {update_type}"],
                trip_link=trip_link,
            )
        except Exception as e:
            logger.error(f"Error sending trip update email: {str(e)}")
            return False

    async def _send_system_alert_email(
        self, notification: Notification, user_email: str, user_name: str
    ) -> bool:
        """Send system alert email."""
        try:
            data = json.loads(notification.data) if notification.data else {}

            # Send to administrators
            admin_emails = [user_email]  # In this case, the user is likely an admin

            return await email_service.send_cost_alert_email(
                admin_emails=admin_emails, alert_data=data
            )
        except Exception as e:
            logger.error(f"Error sending system alert email: {str(e)}")
            return False
