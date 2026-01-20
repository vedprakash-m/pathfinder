"""
Cleanup Timer Function

Scheduled tasks for data cleanup and maintenance.
"""
import logging
from datetime import UTC, datetime, timedelta

import azure.functions as func

from repositories.cosmos_repository import CosmosRepository

bp = func.Blueprint()
logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


@bp.timer_trigger(
    schedule="0 0 2 * * *",  # Run at 2 AM UTC daily
    arg_name="timer",
    run_on_startup=False,
)
async def cleanup_expired_data(timer: func.TimerRequest) -> None:
    """
    Clean up expired data from the database.

    Tasks:
    1. Delete expired invitations (older than 7 days)
    2. Delete old read notifications (older than 30 days)
    3. Clean up orphaned messages (optional)
    """
    logger.info("Starting scheduled cleanup task")

    try:
        repo = CosmosRepository()
        await repo.initialize()

        now = utc_now()
        stats = {"expired_invitations": 0, "old_notifications": 0, "orphaned_messages": 0}

        # 1. Delete expired invitations
        invitation_cutoff = (now - timedelta(days=7)).isoformat()
        expired_invitations_query = f"""
            SELECT c.id FROM c
            WHERE c.entity_type = 'invitation'
            AND c.status = 'pending'
            AND c.expires_at < '{invitation_cutoff}'
        """

        expired_invitations = await repo.query(expired_invitations_query)
        for inv in expired_invitations:
            await repo.delete(inv["id"], inv["id"])
            stats["expired_invitations"] += 1

        logger.info(f"Deleted {stats['expired_invitations']} expired invitations")

        # 2. Delete old read notifications
        notification_cutoff = (now - timedelta(days=30)).isoformat()
        old_notifications_query = f"""
            SELECT c.id FROM c
            WHERE c.entity_type = 'notification'
            AND c.is_read = true
            AND c.read_at < '{notification_cutoff}'
        """

        old_notifications = await repo.query(old_notifications_query)
        for notif in old_notifications:
            await repo.delete(notif["id"], notif["id"])
            stats["old_notifications"] += 1

        logger.info(f"Deleted {stats['old_notifications']} old notifications")

        # 3. Clean up orphaned assistant messages (older than 90 days)
        message_cutoff = (now - timedelta(days=90)).isoformat()
        old_messages_query = f"""
            SELECT c.id FROM c
            WHERE c.entity_type = 'message'
            AND c.message_type IN ('user', 'assistant')
            AND c.created_at < '{message_cutoff}'
        """

        old_messages = await repo.query(old_messages_query)
        for msg in old_messages:
            await repo.delete(msg["id"], msg["id"])
            stats["orphaned_messages"] += 1

        logger.info(f"Deleted {stats['orphaned_messages']} old messages")

        # Log summary
        total_deleted = sum(stats.values())
        logger.info(f"Cleanup completed. Total items deleted: {total_deleted}")
        logger.info(f"Cleanup stats: {stats}")

    except Exception as e:
        logger.exception(f"Error during cleanup task: {e}")
        raise


@bp.timer_trigger(
    schedule="0 0 * * * *",  # Run every hour
    arg_name="timer",
    run_on_startup=False,
)
async def close_expired_polls(timer: func.TimerRequest) -> None:
    """
    Close polls that have passed their expiration time.
    """
    logger.info("Checking for expired polls")

    try:
        repo = CosmosRepository()
        await repo.initialize()

        now = utc_now()

        # Find open polls with passed expiration
        expired_polls_query = f"""
            SELECT * FROM c
            WHERE c.entity_type = 'poll'
            AND c.status = 'open'
            AND c.expires_at < '{now.isoformat()}'
        """

        expired_polls = await repo.query(expired_polls_query)
        closed_count = 0

        for poll in expired_polls:
            poll["status"] = "closed"
            poll["closed_at"] = now.isoformat()
            poll["updated_at"] = now.isoformat()

            await repo.update(poll["id"], poll, poll["id"])
            closed_count += 1

            # Send real-time notification
            from services.realtime_service import RealtimeEvents, get_realtime_service

            realtime_service = get_realtime_service()

            await realtime_service.send_to_group(
                group_name=poll.get("trip_id", ""),
                target=RealtimeEvents.POLL_CLOSED,
                data={
                    "poll_id": poll["id"],
                    "trip_id": poll.get("trip_id"),
                    "title": poll.get("title"),
                    "closed_reason": "expired",
                },
            )

        if closed_count > 0:
            logger.info(f"Closed {closed_count} expired polls")

    except Exception as e:
        logger.exception(f"Error closing expired polls: {e}")
        raise
