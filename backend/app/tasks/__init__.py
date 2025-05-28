"""
Background tasks module for Pathfinder application.
Contains Celery tasks for AI processing, PDF generation, notifications, and exports.
"""

from app.tasks.ai_tasks import (
    generate_itinerary_async,
    optimize_itinerary_async,
    generate_daily_cost_report
)

from app.tasks.pdf_tasks import (
    generate_trip_pdf,
    generate_bulk_pdfs,
    cleanup_old_pdfs
)

from app.tasks.notification_tasks import (
    send_bulk_notifications,
    cleanup_expired_notifications,
    send_email_notifications,
    process_system_alerts
)

from app.tasks.export_tasks import (
    export_trip_data,
    bulk_export_trips,
    cleanup_old_exports
)

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
    "cleanup_old_exports"
]
