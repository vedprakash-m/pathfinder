"""
Notification management API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.zero_trust import require_permissions
from app.models.user import User
from app.services.notification_service import (
    BulkNotificationCreate,
    NotificationCreate,
    NotificationResponse,
    NotificationService,
    NotificationUpdate,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(require_permissions("notifications", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get user's notifications."""
    notification_service = NotificationService(db)

    notifications = await notification_service.get_user_notifications(
        user_id=str(current_user.id), skip=skip, limit=limit, unread_only=unread_only
    )

    return notifications


@router.get("/unread-count")
async def get_unread_count(
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Get count of unread notifications."""
    notification_service = NotificationService(db)

    count = await notification_service.get_unread_count(str(current_user.id))

    return {"unread_count": count}


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a notification (admin/system use)."""
    notification_service = NotificationService(db)

    try:
        notification = await notification_service.create_notification(notification_data)
        return notification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk", response_model=List[NotificationResponse])
async def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "create")),
    db: AsyncSession = Depends(get_db),
):
    """Create bulk notifications (admin/system use)."""
    notification_service = NotificationService(db)

    try:
        notifications = await notification_service.create_bulk_notifications(bulk_data)
        return notifications
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    notification_service = NotificationService(db)

    notification = await notification_service.mark_notification_read(
        notification_id=str(notification_id), user_id=str(current_user.id)
    )

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return notification


@router.put("/mark-all-read")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "update")),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    notification_service = NotificationService(db)

    updated_count = await notification_service.mark_all_notifications_read(str(current_user.id))

    return {"message": f"Marked {updated_count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    notification_service = NotificationService(db)

    success = await notification_service.delete_notification(
        notification_id=str(notification_id), user_id=str(current_user.id)
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    return {"message": "Notification deleted successfully"}


@router.post("/cleanup")
async def cleanup_expired_notifications(
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """Clean up expired notifications (admin use)."""
    notification_service = NotificationService(db)

    deleted_count = await notification_service.cleanup_expired_notifications()

    return {"message": f"Cleaned up {deleted_count} expired notifications"}
