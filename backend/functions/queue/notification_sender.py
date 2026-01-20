"""
Notification Sender Queue Function

Processes async notification requests from the queue.
"""
import json
import logging
from datetime import UTC, datetime

import azure.functions as func

from services.notification_service import NotificationType, get_notification_service
from services.realtime_service import RealtimeEvents, get_realtime_service

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


@bp.queue_trigger(arg_name="msg", queue_name="notifications", connection="AZURE_STORAGE_CONNECTION_STRING")
async def process_notification(msg: func.QueueMessage) -> None:
    """
    Process a notification request from the queue.

    Message format:
    {
        "type": "notification_type",
        "user_ids": ["user_id1", "user_id2"],
        "title": "Notification title",
        "body": "Notification body",
        "trip_id": "optional_trip_id",
        "family_id": "optional_family_id",
        "action_url": "optional_action_url",
        "metadata": {}
    }
    """
    try:
        # Parse message
        message_body = msg.get_body().decode("utf-8")
        request = json.loads(message_body)

        notification_type = request.get("type")
        user_ids = request.get("user_ids", [])
        title = request.get("title")
        body = request.get("body")
        trip_id = request.get("trip_id")
        family_id = request.get("family_id")
        action_url = request.get("action_url")
        metadata = request.get("metadata", {})

        if not user_ids or not title or not body:
            logger.error("Invalid notification message: missing required fields")
            return

        # Map type string to enum
        try:
            notif_type = NotificationType(notification_type)
        except ValueError:
            notif_type = NotificationType.MESSAGE_RECEIVED

        logger.info(f"Sending notification to {len(user_ids)} users: {title}")

        # Create notifications
        notification_service = get_notification_service()
        notifications = await notification_service.notify_users(
            user_ids=user_ids,
            notification_type=notif_type,
            title=title,
            body=body,
            trip_id=trip_id,
            family_id=family_id,
            action_url=action_url,
            metadata=metadata,
        )

        # Send real-time notifications
        realtime_service = get_realtime_service()
        for notification in notifications:
            await realtime_service.send_to_user(
                user_id=notification.user_id,
                target=RealtimeEvents.NOTIFICATION,
                data={
                    "id": notification.id,
                    "type": notification.notification_type.value,
                    "title": notification.title,
                    "body": notification.body,
                    "trip_id": notification.trip_id,
                    "action_url": notification.action_url,
                    "created_at": notification.created_at.isoformat(),
                },
            )

        logger.info(f"Successfully sent {len(notifications)} notifications")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in queue message: {e}")
    except Exception as e:
        logger.exception(f"Error processing notification: {e}")
        raise  # Re-raise to trigger retry


@bp.queue_trigger(arg_name="msg", queue_name="realtime-messages", connection="AZURE_STORAGE_CONNECTION_STRING")
async def process_realtime_message(msg: func.QueueMessage) -> None:
    """
    Process a real-time message request from the queue.

    Used for sending SignalR messages that need guaranteed delivery.

    Message format:
    {
        "target": "event_name",
        "data": {...},
        "user_id": "optional_user_id",
        "group": "optional_group_name"
    }
    """
    try:
        # Parse message
        message_body = msg.get_body().decode("utf-8")
        request = json.loads(message_body)

        target = request.get("target")
        data = request.get("data", {})
        user_id = request.get("user_id")
        group = request.get("group")

        if not target:
            logger.error("Invalid realtime message: missing target")
            return

        realtime_service = get_realtime_service()

        if user_id:
            # Send to specific user
            await realtime_service.send_to_user(user_id, target, data)
            logger.info(f"Sent realtime message to user {user_id}: {target}")
        elif group:
            # Send to group
            await realtime_service.send_to_group(group, target, data)
            logger.info(f"Sent realtime message to group {group}: {target}")
        else:
            # Broadcast
            await realtime_service.broadcast(target, data)
            logger.info(f"Broadcast realtime message: {target}")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in queue message: {e}")
    except Exception as e:
        logger.exception(f"Error processing realtime message: {e}")
        raise
