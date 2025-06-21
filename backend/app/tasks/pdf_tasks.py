"""
PDF generation background tasks.
"""

from datetime import datetime, timezone

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.task_context import get_trip_service
from app.services.notification_service import NotificationService
from app.services.pdf_service import PDFService
from app.tasks.task_compat import conditional_task
from celery import current_task

logger = get_logger(__name__)


@conditional_task(bind=True, name="app.tasks.pdf_tasks.generate_trip_pdf")
def generate_trip_pdf(self, trip_id: str, user_id: str, pdf_type: str = "itinerary"):
    """Generate PDF documents for trips."""

    async def _generate():
        async for db in get_db():
            try:
                # Update task progress
                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": 10, "total": 100, "status": "Initializing PDF service"},
                )

                # Initialize services
                pdf_service = PDFService()
                trip_service = await get_trip_service()
                notification_service = NotificationService(db)

                # Get trip data
                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": 30, "total": 100, "status": "Fetching trip data"},
                )

                trip_data = await trip_service.get_trip_by_id(trip_id, user_id)
                if not trip_data:
                    raise ValueError(f"Trip {trip_id} not found")

                # Generate PDF based on type
                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": 60, "total": 100, "status": f"Generating {pdf_type} PDF"},
                )

                if pdf_type == "itinerary":
                    result = await pdf_service.generate_itinerary_pdf(
                        trip_id=trip_id, itinerary_data=trip_data.dict(), user_id=user_id
                    )
                elif pdf_type == "summary":
                    result = await pdf_service.generate_trip_summary_pdf(
                        trip_id=trip_id, trip_data=trip_data.dict(), user_id=user_id
                    )
                else:
                    raise ValueError(f"Unknown PDF type: {pdf_type}")

                current_task.update_state(
                    state="PROGRESS",
                    meta={"current": 90, "total": 100, "status": "Sending notification"},
                )

                # Notify user that PDF is ready
                await notification_service.create_notification(
                    {
                        "user_id": user_id,
                        "type": "DOCUMENT_READY",
                        "priority": "NORMAL",
                        "title": f"{pdf_type.title()} PDF Ready",
                        "message": f"Your {pdf_type} PDF for '{trip_data.name}' is ready for download.",
                        "trip_id": trip_id,
                        "data": {
                            "pdf_url": result.get("pdf_url"),
                            "pdf_type": pdf_type,
                            "download_expires": result.get("download_expires"),
                        },
                    }
                )

                logger.info(f"Successfully generated {pdf_type} PDF for trip {trip_id}")

                return {
                    "status": "SUCCESS",
                    "trip_id": trip_id,
                    "pdf_type": pdf_type,
                    "pdf_url": result.get("pdf_url"),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }

            except Exception as e:
                logger.error(f"Error generating {pdf_type} PDF for trip {trip_id}: {e}")

                # Notify user of failure
                try:
                    await notification_service.create_notification(
                        {
                            "user_id": user_id,
                            "type": "SYSTEM_ERROR",
                            "priority": "NORMAL",
                            "title": "PDF Generation Failed",
                            "message": f"Failed to generate {pdf_type} PDF: {str(e)}",
                            "trip_id": trip_id,
                            "data": {"error": str(e), "pdf_type": pdf_type},
                        }
                    )
                except Exception as notify_error:
                    logger.error(f"Failed to send PDF error notification: {notify_error}")

                raise

            finally:
                await db.close()

    return run_async(_generate())


@conditional_task(bind=True, name="app.tasks.pdf_tasks.generate_bulk_pdfs")
def generate_bulk_pdfs(self, trip_id: str, participant_user_ids: list, pdf_type: str = "itinerary"):
    """Generate PDFs for multiple trip participants."""

    async def _generate_bulk():
        results = []

        for i, user_id in enumerate(participant_user_ids):
            try:
                # Update overall progress
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": int((i / len(participant_user_ids)) * 100),
                        "total": 100,
                        "status": f"Generating PDF for participant {i+1}/{len(participant_user_ids)}",
                    },
                )

                # Generate PDF for this participant
                result = generate_trip_pdf.apply(args=[trip_id, user_id, pdf_type]).get()

                results.append({"user_id": user_id, "status": "SUCCESS", "result": result})

            except Exception as e:
                logger.error(f"Failed to generate PDF for user {user_id}: {e}")
                results.append({"user_id": user_id, "status": "FAILED", "error": str(e)})

        logger.info(
            f"Bulk PDF generation completed for trip {trip_id}: {len(results)} PDFs processed"
        )

        return {
            "status": "COMPLETED",
            "trip_id": trip_id,
            "pdf_type": pdf_type,
            "total_participants": len(participant_user_ids),
            "successful": len([r for r in results if r["status"] == "SUCCESS"]),
            "failed": len([r for r in results if r["status"] == "FAILED"]),
            "results": results,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    return run_async(_generate_bulk())


@conditional_task(name="app.tasks.pdf_tasks.cleanup_old_pdfs")
def cleanup_old_pdfs():
    """Clean up old PDF files from storage."""

    async def _cleanup():
        try:
            pdf_service = PDFService()

            # Clean up PDFs older than 30 days
            cleanup_results = await pdf_service.cleanup_old_pdfs(days_old=30)

            logger.info(f"PDF cleanup completed: {cleanup_results}")
            return cleanup_results

        except Exception as e:
            logger.error(f"Error during PDF cleanup: {e}")
            raise

    return run_async(_cleanup())
