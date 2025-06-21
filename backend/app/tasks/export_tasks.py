"""
Data export background tasks.
"""

from datetime import datetime, timezone
from typing import List

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.task_context import get_trip_service
from app.services.export_service import DataExportService
from app.services.notification_service import NotificationService
from app.tasks.task_compat import conditional_task
from celery import current_task

logger = get_logger(__name__)


@conditional_task(bind=True, name="app.tasks.export_tasks.export_trip_data")
def export_trip_data(
    self,
    trip_id: str,
    user_id: str,
    export_format: str = "excel",
    export_type: str = "complete",
):
    """Export trip data in various formats."""

    async def _export():
        async for db in get_db():
            try:
                # Update task progress
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 10,
                        "total": 100,
                        "status": "Initializing export service",
                    },
                )

                # Initialize services
                export_service = DataExportService()
                trip_service = await get_trip_service()
                notification_service = NotificationService(db)

                # Get trip data
                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": 30, "total": 100,
                        "status": "Fetching trip data"},
                )

                trip_data = await trip_service.get_trip_by_id(trip_id, user_id)
                if not trip_data:
                    raise ValueError(f"Trip {trip_id} not found")

                # Get additional data based on export type
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 50,
                        "total": 100,
                        "status": f"Preparing {export_type} export",
                    },
                )

                if export_type == "complete":
                    # Export all trip data
                    result = await export_service.export_trip_complete(
                        trip_id=trip_id, format_type=export_format, user_id=user_id
                    )
                elif export_type == "itinerary":
                    # Export only itinerary data
                    itinerary_data = await trip_service.get_latest_itinerary(
                        trip_id, user_id
                    )
                    result = await export_service.export_itinerary_data(
                        itinerary_data=itinerary_data or {},
                        trip_id=trip_id,
                        user_id=user_id,
                        format_type=export_format,
                    )
                elif export_type == "participants":
                    # Export participant data
                    participants = await trip_service.get_trip_participants(trip_id)
                    result = await export_service.export_participant_data(
                        participants=[p.dict() for p in participants],
                        trip_id=trip_id,
                        user_id=user_id,
                        format_type=export_format,
                    )
                elif export_type == "budget":
                    # Export budget data
                    result = await export_service.export_budget_data(
                        trip_id=trip_id, user_id=user_id, format_type=export_format
                    )
                else:
                    raise ValueError(f"Unknown export type: {export_type}")

                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": 90,
                        "total": 100,
                        "status": "Sending notification",
                    },
                )

                # Notify user that export is ready
                await notification_service.create_notification(
                    {
                        "user_id": user_id,
                        "type": "DOCUMENT_READY",
                        "priority": "NORMAL",
                        "title": f"{export_type.title()} Export Ready",
                        "message": f"Your {export_type} export for '{trip_data.name}' is ready for download.",
                        "trip_id": trip_id,
                        "data": {
                            "download_url": result.get("download_url"),
                            "export_type": export_type,
                            "export_format": export_format,
                            "file_size": result.get("file_size"),
                            "download_expires": result.get("download_expires"),
                        },
                    }
                )

                logger.info(
                    f"Successfully exported {export_type} data for trip {trip_id}"
                )

                return {
                    "status": "SUCCESS",
                    "trip_id": trip_id,
                    "export_type": export_type,
                    "export_format": export_format,
                    "download_url": result.get("download_url"),
                    "file_size": result.get("file_size"),
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.error(
                    f"Error exporting {export_type} data for trip {trip_id}: {e}"
                )

                # Notify user of failure
                try:
                    await notification_service.create_notification(
                        {
                            "user_id": user_id,
                            "type": "SYSTEM_ERROR",
                            "priority": "NORMAL",
                            "title": "Export Failed",
                            "message": f"Failed to export {export_type} data: {str(e)}",
                            "trip_id": trip_id,
                            "data": {"error": str(e), "export_type": export_type},
                        }
                    )
                except Exception as notify_error:
                    logger.error(
                        f"Failed to send export error notification: {notify_error}"
                    )

                raise

            finally:
                await db.close()

    return run_async(_export())


@conditional_task(bind=True, name="app.tasks.export_tasks.bulk_export_trips")
def bulk_export_trips(
    self, trip_ids: List[str], user_id: str, export_format: str = "excel"
):
    """Export multiple trips in a single archive."""

    async def _bulk_export():
        try:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": 10,
                    "total": 100,
                    "status": "Initializing bulk export",
                },
            )

            export_service = DataExportService()
            results = []

            for i, trip_id in enumerate(trip_ids):
                try:
                    # Update progress
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "current": int(10 + ((i / len(trip_ids)) * 80)),
                            "total": 100,
                            "status": f"Exporting trip {i+1}/{len(trip_ids)}",
                        },
                    )

                    # Export individual trip
                    result = export_trip_data.apply(
                        args=[trip_id, user_id, export_format, "complete"]
                    ).get()

                    results.append(
                        {"trip_id": trip_id, "status": "SUCCESS", "result": result}
                    )

                except Exception as e:
                    logger.error(f"Failed to export trip {trip_id}: {e}")
                    results.append(
                        {"trip_id": trip_id,
                            "status": "FAILED", "error": str(e)}
                    )

            # Create combined archive
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 95, "total": 100,
                    "status": "Creating archive"},
            )

            archive_result = await export_service.create_bulk_export_archive(
                results, user_id, export_format
            )

            logger.info(f"Bulk export completed for {len(trip_ids)} trips")

            return {
                "status": "COMPLETED",
                "total_trips": len(trip_ids),
                "successful": len([r for r in results if r["status"] == "SUCCESS"]),
                "failed": len([r for r in results if r["status"] == "FAILED"]),
                "archive_url": archive_result.get("archive_url"),
                "results": results,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in bulk trip export: {e}")
            raise

    return run_async(_bulk_export())


@conditional_task(name="app.tasks.export_tasks.cleanup_old_exports")
def cleanup_old_exports():
    """Clean up old export files from storage."""

    async def _cleanup():
        try:
            export_service = DataExportService()

            # Clean up exports older than 7 days
            cleanup_results = await export_service.cleanup_old_exports(days_old=7)

            logger.info(f"Export cleanup completed: {cleanup_results}")
            return cleanup_results

        except Exception as e:
            logger.error(f"Error during export cleanup: {e}")
            raise

    return run_async(_cleanup())
