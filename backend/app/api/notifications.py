"""
Notification management API endpoints.
"""

from typing import List
from uuid import UUID

from app.core.database_unified import get_cosmos_repository
from app.core.zero_trust import require_permissions
from app.models.user import User
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.services.notification_service import (
    BulkNotificationCreate,
    NotificationCreate,
    NotificationResponse,
    NotificationService,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(require_permissions("notifications", "read")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get user's notifications."""
    notification_service = NotificationService(cosmos_repo)

    notifications = await notification_service.get_user_notifications(
        user_id=str(current_user.id), skip=skip, limit=limit, unread_only=unread_only
    )

    return notifications


@router.get("/unread-count")
async def get_unread_count(
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "read")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Get count of unread notifications."""
    notification_service = NotificationService(cosmos_repo)

    count = await notification_service.get_unread_count(str(current_user.id))

    return {"unread_count": count}


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "create")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Create a notification (admin/system use) using unified Cosmos DB."""
    notification_service = NotificationService(cosmos_repo)

    try:
        notification = await notification_service.create_notification(notification_data)
        return notification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.post("/bulk", response_model=List[NotificationResponse])
async def create_bulk_notifications(
    bulk_data: BulkNotificationCreate,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "create")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Create bulk notifications (admin/system use) using unified Cosmos DB."""
    notification_service = NotificationService(cosmos_repo)

    try:
        notifications = await notification_service.create_bulk_notifications(bulk_data)
        return notifications
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "update")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Mark a notification as read using unified Cosmos DB."""
    notification_service = NotificationService(cosmos_repo)

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
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Mark all notifications as read using unified Cosmos DB."""
    notification_service = NotificationService(cosmos_repo)

    updated_count = await notification_service.mark_all_notifications_read(str(current_user.id))

    return {"message": f"Marked {updated_count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    request: Request,
    current_user: User = Depends(require_permissions("notifications", "delete")),
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Delete a notification using unified Cosmos DB."""
    notification_service = NotificationService(cosmos_repo)

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
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),
):
    """Clean up expired notifications (admin use) using unified Cosmos DB."""
    notification_service = NotificationService(cosmos_repo)

    deleted_count = await notification_service.cleanup_expired_notifications()

    return {"message": f"Cleaned up {deleted_count} expired notifications"}
