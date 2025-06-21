"""
Background tasks module for Pathfinder application.
Contains Celery tasks for AI processing, PDF generation, notifications, and exports.
"""

from app.tasks.ai_tasks import (
    generate_daily_cost_report,
    generate_itinerary_async,
)
from app.tasks.export_tasks import (
    bulk_export_trips,
    cleanup_old_exports,
    export_trip_data,
)
from app.tasks.notification_tasks import (
    cleanup_expired_notifications,
    process_system_alerts,
    send_bulk_notifications,
    send_email_notifications,
)
from app.tasks.pdf_tasks import cleanup_old_pdfs, generate_bulk_pdfs, generate_trip_pdf

__all__ = [
    # AI tasks
    "generate_itinerary_async",
    "generate_daily_cost_report",
    "optimize_ai_models",
    # PDF tasks
    "generate_trip_pdf",
    "generate_bulk_pdfs",
    "cleanup_old_pdfs",
    # Notification tasks
    "send_bulk_notifications",
    "cleanup_expired_notifications",
    "send_email_notifications",
    "process_system_alerts",
    # Export tasks
    "export_trip_data",
    "bulk_export_trips",
    "cleanup_old_exports",
]
