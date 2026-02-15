"""
Cleanup Timer Function

Scheduled tasks for data cleanup and maintenance.
"""

import logging
from datetime import UTC, datetime, timedelta

import azure.functions as func

from models.documents import PollDocument
from repositories.cosmos_repository import cosmos_repo

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
        now = utc_now()
        stats = {"expired_invitations": 0, "old_notifications": 0, "orphaned_messages": 0}

        # 1. Delete expired invitations
        invitation_cutoff = (now - timedelta(days=7)).isoformat()
        expired_invitations_query = """
            SELECT c.id, c.pk FROM c
            WHERE c.entity_type = 'invitation'
            AND c.status = 'pending'
            AND c.expires_at < @cutoff
        """
        params = [{"name": "@cutoff", "value": invitation_cutoff}]

        expired_invitations = await cosmos_repo.query(expired_invitations_query, parameters=params)
        for inv in expired_invitations:
            await cosmos_repo.delete(inv["id"], inv["pk"])
            stats["expired_invitations"] += 1

        logger.info(f"Deleted {stats['expired_invitations']} expired invitations")

        # 2. Delete old read notifications
        notification_cutoff = (now - timedelta(days=30)).isoformat()
        old_notifications_query = """
            SELECT c.id, c.pk FROM c
            WHERE c.entity_type = 'notification'
            AND c.is_read = true
            AND c.read_at < @cutoff
        """
        params = [{"name": "@cutoff", "value": notification_cutoff}]

        old_notifications = await cosmos_repo.query(old_notifications_query, parameters=params)
        for notif in old_notifications:
            await cosmos_repo.delete(notif["id"], notif["pk"])
            stats["old_notifications"] += 1

        logger.info(f"Deleted {stats['old_notifications']} old notifications")

        # 3. Clean up orphaned assistant messages (older than 90 days)
        message_cutoff = (now - timedelta(days=90)).isoformat()
        old_messages_query = """
            SELECT c.id, c.pk FROM c
            WHERE c.entity_type = 'message'
            AND c.message_type IN ('user', 'assistant')
            AND c.created_at < @cutoff
        """
        params = [{"name": "@cutoff", "value": message_cutoff}]

        old_messages = await cosmos_repo.query(old_messages_query, parameters=params)
        for msg in old_messages:
            await cosmos_repo.delete(msg["id"], msg["pk"])
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
        now = utc_now()

        # Find active polls with passed expiration
        expired_polls_query = """
            SELECT * FROM c
            WHERE c.entity_type = 'poll'
            AND c.status = 'active'
            AND c.expires_at < @now
        """
        params = [{"name": "@now", "value": now.isoformat()}]

        expired_polls = await cosmos_repo.query(expired_polls_query, parameters=params, model_class=PollDocument)
        closed_count = 0

        for poll in expired_polls:
            poll.status = "closed"
            await cosmos_repo.update(poll)
            closed_count += 1

            # Send real-time notification
            from services.realtime_service import RealtimeEvents, get_realtime_service

            realtime_service = get_realtime_service()

            await realtime_service.send_to_group(
                group_name=poll.trip_id,
                target=RealtimeEvents.POLL_CLOSED,
                data={
                    "poll_id": poll.id,
                    "trip_id": poll.trip_id,
                    "title": poll.title,
                    "closed_reason": "expired",
                },
            )

        if closed_count > 0:
            logger.info(f"Closed {closed_count} expired polls")

    except Exception as e:
        logger.exception(f"Error closing expired polls: {e}")
        raise
