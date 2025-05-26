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
    NotificationStats
)
from app.services.websocket import ConnectionManager

logger = get_logger(__name__)


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self, db: AsyncSession, websocket_manager: Optional[ConnectionManager] = None):
        self.db = db
        self.websocket_manager = websocket_manager
    
    async def create_notification(self, notification_data: NotificationCreate) -> NotificationResponse:
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
                expires_at=notification_data.expires_at
            )
            
            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)
            
            response = self._build_notification_response(notification)
            
            # Send real-time notification
            if self.websocket_manager:
                await self._send_real_time_notification(str(notification_data.user_id), response)
            
            logger.info(f"Notification created: {notification.id}")
            return response
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification: {str(e)}")
            raise ValueError(f"Failed to create notification: {str(e)}")
    
    async def create_bulk_notifications(self, bulk_data: BulkNotificationCreate) -> List[NotificationResponse]:
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
                    expires_at=bulk_data.expires_at
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
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 50,
        unread_only: bool = False
    ) -> List[NotificationResponse]:
        """Get notifications for a user."""
        try:
            query = select(Notification).where(
                Notification.user_id == UUID(user_id)
            )
            
            # Filter by read status if requested
            if unread_only:
                query = query.where(Notification.is_read == False)
            
            # Filter out expired notifications
            query = query.where(
                (Notification.expires_at.is_(None)) | 
                (Notification.expires_at > datetime.now(timezone.utc))
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
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> Optional[NotificationResponse]:
        """Mark a notification as read."""
        try:
            # Get notification and verify ownership
            query = select(Notification).where(
                Notification.id == UUID(notification_id),
                Notification.user_id == UUID(user_id)
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
                .where(
                    and_(
                        Notification.user_id == UUID(user_id),
                        Notification.is_read == False
                    )
                )
                .values(
                    is_read=True,
                    read_at=datetime.now(timezone.utc)
                )
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
                        Notification.user_id == UUID(user_id)
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
                            Notification.expires_at > datetime.now(timezone.utc)
                        )
                    )
                )
            )
            
            count = result.scalar() or 0
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0
    
    # Helper methods for specific notification types
    
    async def notify_trip_invitation(self, user_id: str, trip_name: str, inviter_name: str, trip_id: str) -> None:
        """Send trip invitation notification."""
        notification_data = NotificationCreate(
            user_id=UUID(user_id),
            type=NotificationType.TRIP_INVITATION,
            priority=NotificationPriority.HIGH,
            title="Trip Invitation",
            message=f"You've been invited to join '{trip_name}' by {inviter_name}",
            trip_id=UUID(trip_id),
            data={"trip_id": trip_id, "trip_name": trip_name, "inviter": inviter_name}
        )
        await self.create_notification(notification_data)
    
    async def notify_trip_update(self, user_ids: List[str], trip_name: str, update_type: str, trip_id: str) -> None:
        """Send trip update notifications."""
        bulk_data = BulkNotificationCreate(
            user_ids=[UUID(uid) for uid in user_ids],
            type=NotificationType.TRIP_UPDATE,
            priority=NotificationPriority.NORMAL,
            title="Trip Update",
            message=f"'{trip_name}' has been updated: {update_type}",
            trip_id=UUID(trip_id),
            data={"trip_id": trip_id, "trip_name": trip_name, "update_type": update_type}
        )
        await self.create_bulk_notifications(bulk_data)
    
    async def notify_itinerary_ready(self, user_ids: List[str], trip_name: str, trip_id: str) -> None:
        """Send itinerary ready notifications."""
        bulk_data = BulkNotificationCreate(
            user_ids=[UUID(uid) for uid in user_ids],
            type=NotificationType.ITINERARY_READY,
            priority=NotificationPriority.HIGH,
            title="Itinerary Ready",
            message=f"The itinerary for '{trip_name}' is ready for review!",
            trip_id=UUID(trip_id),
            data={"trip_id": trip_id, "trip_name": trip_name}
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
            expires_at=notification.expires_at
        )
    
    async def _send_real_time_notification(self, user_id: str, notification: NotificationResponse) -> None:
        """Send real-time notification via WebSocket."""
        if self.websocket_manager:
            message = {
                "type": "notification",
                "data": notification.model_dump()
            }
            await self.websocket_manager.send_to_user(user_id, json.dumps(message))