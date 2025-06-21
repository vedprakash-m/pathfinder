"""
Background task processing - Redis-free alternatives for cost optimization.
Falls back to database-backed task queue when Redis is not available.
"""

import asyncio
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

# Conditional Celery initialization - only if Redis is enabled
celery_app: Optional[object] = None

if settings.USE_REDIS_CACHE and settings.REDIS_URL:
    try:
        from celery import Celery

        # Create Celery instance only when Redis is available
        celery_app = Celery(
            "pathfinder",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
            include=[
                "app.tasks.ai_tasks",
                "app.tasks.pdf_tasks",
                "app.tasks.notification_tasks",
                "app.tasks.export_tasks",
            ],
        )
    except ImportError:
        print("Celery not available - using SQLite task queue for cost optimization")
        celery_app = None
else:
    print("Redis disabled - using SQLite-based task queue for cost optimization")
    celery_app = None

# Configure Celery (only if available)
if celery_app:
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        result_expires=3600,  # 1 hour
        # Task routing
        task_routes={
            "app.tasks.ai_tasks.*": {"queue": "ai_tasks"},
            "app.tasks.pdf_tasks.*": {"queue": "pdf_tasks"},
            "app.tasks.notification_tasks.*": {"queue": "notifications"},
            "app.tasks.export_tasks.*": {"queue": "exports"},
        },
        # Beat schedule for periodic tasks
        beat_schedule={
            "cleanup-expired-notifications": {
                "task": "app.tasks.notification_tasks.cleanup_expired_notifications",
                "schedule": 3600.0,  # Every hour
            },
            "generate-cost-reports": {
                "task": "app.tasks.ai_tasks.generate_daily_cost_report",
                "schedule": 86400.0,  # Daily
            },
        },
    )


# Helper function to run async functions in Celery tasks
def run_async(coro):
    """Run async function in Celery task context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)
