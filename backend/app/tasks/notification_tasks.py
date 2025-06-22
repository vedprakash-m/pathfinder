"""
Notification background tasks for batch processing and cleanup.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.services.email_service import EmailNotificationService
from app.services.notification_service import NotificationService
from app.tasks.task_compat import conditional_task
from celery import current_task

logger = get_logger(__name__)


@conditional_task(bind=True, name="app.tasks.notification_tasks.send_bulk_notifications")
def send_bulk_notifications(self, notification_data: Dict[str, Any], user_ids: List[str]):
    """Send notifications to multiple users efficiently."""

    async def _send_bulk():
        async for db in get_db():
            try:
                notification_service = NotificationService(db)

                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 10,
                        "total": 100,
                        "status": "Preparing bulk notifications",
                    },
                )

                # Create bulk notification data
                from app.models.notification import BulkNotificationCreate

                bulk_data = BulkNotificationCreate(user_ids=user_ids, **notification_data)

                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 50,
                        "total": 100,
                        "status": "Creating notifications",
                    },
                )

                # Create notifications
                notifications = await notification_service.create_bulk_notifications(bulk_data)

                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": 90, "total": 100, "status": "Finalizing"},
                )

                logger.info(f"Successfully sent bulk notifications to {len(user_ids)} users")

                return {
                    "status": "SUCCESS",
                    "notifications_sent": len(notifications),
                    "user_count": len(user_ids),
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.error(f"Error sending bulk notifications: {e}")
                raise

            finally:
                await db.close()

    return run_async(_send_bulk())


@conditional_task(name="app.tasks.notification_tasks.cleanup_expired_notifications")
def cleanup_expired_notifications():
    """Clean up expired notifications from the database."""

    async def _cleanup():
        async for db in get_db():
            try:
                notification_service = NotificationService(db)

                # Clean up expired notifications
                deleted_count = await notification_service.cleanup_expired_notifications()

                logger.info(f"Cleaned up {deleted_count} expired notifications")

                return {
                    "status": "SUCCESS",
                    "deleted_count": deleted_count,
                    "cleaned_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.error(f"Error cleaning up notifications: {e}")
                raise

            finally:
                await db.close()

    return run_async(_cleanup())


@conditional_task(bind=True, name="app.tasks.notification_tasks.send_email_notifications")
def send_email_notifications(self, email_data: Dict[str, Any], recipient_emails: List[str]):
    """Send email notifications to multiple recipients."""

    async def _send_emails():
        try:
            email_service = EmailNotificationService()

            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 10,
                    "total": 100,
                    "status": "Initializing email service",
                },
            )

            results = []
            total_recipients = len(recipient_emails)

            for i, email in enumerate(recipient_emails):
                try:
                    # Update progress
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": int(((i + 1) / total_recipients) * 90),
                            "total": 100,
                            "status": f"Sending email {i+1}/{total_recipients}",
                        },
                    )

                    # Send email based on type
                    email_type = email_data.get("type", "general")

                    if email_type == "trip_invitation":
                        success = await email_service.send_trip_invitation(
                            recipient_email=email, **email_data.get("data", {})
                        )
                    elif email_type == "itinerary_notification":
                        success = await email_service.send_itinerary_notification(
                            recipient_email=email, **email_data.get("data", {})
                        )
                    elif email_type == "trip_reminder":
                        success = await email_service.send_trip_reminder(
                            recipient_email=email, **email_data.get("data", {})
                        )
                    else:
                        logger.warning(f"Unknown email type: {email_type}")
                        success = False

                    results.append({"email": email, "status": "SUCCESS" if success else "FAILED"})

                except Exception as e:
                    logger.error(f"Failed to send email to {email}: {e}")
                    results.append({"email": email, "status": "FAILED", "error": str(e)})

            successful = len([r for r in results if r["status"] == "SUCCESS"])

            logger.info(
                f"Email batch completed: {successful}/{total_recipients} emails sent successfully"
            )

            return {
                "status": "COMPLETED",
                "total_recipients": total_recipients,
                "successful": successful,
                "failed": total_recipients - successful,
                "results": results,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in email batch processing: {e}")
            raise

    return run_async(_send_emails())


@conditional_task(name="app.tasks.notification_tasks.process_system_alerts")
def process_system_alerts(alert_type: str, alert_data: Dict[str, Any]):
    """Process system-wide alerts and notifications."""

    async def _process_alerts():
        async for db in get_db():
            try:
                notification_service = NotificationService(db)

                if alert_type == "cost_threshold":
                    await notification_service.send_cost_threshold_alert(
                        service=alert_data.get("service"),
                        current_usage=alert_data.get("current_usage"),
                        threshold=alert_data.get("threshold"),
                        percentage=alert_data.get("percentage"),
                    )
                elif alert_type == "system_health":
                    await notification_service.send_system_health_alert(
                        metric=alert_data.get("metric"),
                        value=alert_data.get("value"),
                        threshold=alert_data.get("threshold"),
                    )
                else:
                    # Generic admin alert
                    await notification_service.send_admin_alert(alert_data)

                logger.info(f"Processed system alert: {alert_type}")

                return {
                    "status": "SUCCESS",
                    "alert_type": alert_type,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.error(f"Error processing system alert: {e}")
                raise

            finally:
                await db.close()

    return run_async(_process_alerts())
