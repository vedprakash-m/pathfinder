"""
Export API endpoints for data export functionality.
"""

from typing import List
from uuid import UUID

from app.core.container import Container
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.security import get_current_user, require_permissions
from app.models.user import User
from app.services.export_service import DataExportService
from app.tasks.export_tasks import bulk_export_trips, export_trip_data
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
router = APIRouter()


class ExportRequest(BaseModel):
    """Export request model."""

    format: str = "excel"  # excel, csv
    export_type: str = "complete"  # complete, itinerary, participants, budget
    async_processing: bool = True


class BulkExportRequest(BaseModel):
    """Bulk export request model."""

    trip_ids: List[UUID]
    format: str = "excel"
    async_processing: bool = True


@router.post("/trips/{trip_id}")
async def export_trip(
    trip_id: UUID,
    export_request: ExportRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permissions(["trips:read"])),
    db: AsyncSession = Depends(get_db),
):
    """Export trip data in various formats."""
    try:
        # Verify user has access to trip
        trip_service = Container().trip_domain_service()
        trip = await trip_service.get_trip_by_id(trip_id, str(current_user.id))

        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        if export_request.async_processing:
            # Process export asynchronously
            task = export_trip_data.delay(
                trip_id=str(trip_id),
                user_id=str(current_user.id),
                export_format=export_request.format,
                export_type=export_request.export_type,
            )

            return {
                "message": "Export started",
                "task_id": task.id,
                "status": "PENDING",
                "trip_id": str(trip_id),
                "export_type": export_request.export_type,
                "format": export_request.format,
                "check_status_url": f"/api/v1/exports/tasks/{task.id}",
            }
        else:
            # Process export synchronously (for small exports)
            export_service = DataExportService()

            if export_request.export_type == "complete":
                result = await export_service.export_trip_complete(
                    trip_id=str(trip_id),
                    format_type=export_request.format,
                    user_id=str(current_user.id),
                )
            elif export_request.export_type == "itinerary":
                itinerary_data = await trip_service.get_latest_itinerary(
                    trip_id, str(current_user.id)
                )
                result = await export_service.export_itinerary_data(
                    itinerary_data=itinerary_data or {},
                    trip_id=str(trip_id),
                    user_id=str(current_user.id),
                    format_type=export_request.format,
                )
            elif export_request.export_type == "participants":
                participants = await trip_service.get_trip_participants(trip_id)
                result = await export_service.export_participant_data(
                    participants=[p.dict() for p in participants],
                    trip_id=str(trip_id),
                    user_id=str(current_user.id),
                    format_type=export_request.format,
                )
            elif export_request.export_type == "budget":
                result = await export_service.export_budget_data(
                    trip_id=str(trip_id),
                    user_id=str(current_user.id),
                    format_type=export_request.format,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown export type: {export_request.export_type}",
                )

            return {
                "message": "Export completed",
                "status": "SUCCESS",
                "download_url": result.get("download_url"),
                "file_size": result.get("file_size"),
                "export_type": export_request.export_type,
                "format": export_request.format,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting trip {trip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing export request",
        )


@router.post("/trips/bulk")
async def bulk_export_trips_endpoint(
    bulk_request: BulkExportRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(require_permissions("trips", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Export multiple trips in a single archive."""
    try:
        # Verify user has access to all trips
        trip_service = Container().trip_domain_service()
        accessible_trips = []

        for trip_id in bulk_request.trip_ids:
            trip = await trip_service.get_trip_by_id(trip_id, str(current_user.id))
            if trip:
                accessible_trips.append(str(trip_id))

        if not accessible_trips:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No accessible trips found"
            )

        if len(accessible_trips) != len(bulk_request.trip_ids):
            logger.warning(
                f"User {current_user.id} requested {len(bulk_request.trip_ids)} trips but has access to {len(accessible_trips)}"
            )

        if bulk_request.async_processing:
            # Process bulk export asynchronously
            task = bulk_export_trips.delay(
                trip_ids=accessible_trips,
                user_id=str(current_user.id),
                export_format=bulk_request.format,
            )

            return {
                "message": "Bulk export started",
                "task_id": task.id,
                "status": "PENDING",
                "trip_count": len(accessible_trips),
                "format": bulk_request.format,
                "check_status_url": f"/api/v1/exports/tasks/{task.id}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bulk exports must be processed asynchronously",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing bulk export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing bulk export request",
        )


@router.get("/tasks/{task_id}")
async def get_export_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    """Get the status of an export task."""
    try:
        from app.core.celery_app import celery_app

        # Get task result
        task_result = celery_app.AsyncResult(task_id)

        if task_result.state == "PENDING":
            response = {
                "task_id": task_id,
                "status": "PENDING",
                "message": "Task is waiting to be processed",
            }
        elif task_result.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "status": "PROGRESS",
                "message": "Task is being processed",
                "progress": task_result.info,
            }
        elif task_result.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "status": "SUCCESS",
                "message": "Task completed successfully",
                "result": task_result.result,
            }
        else:
            # Task failed
            response = {
                "task_id": task_id,
                "status": "FAILED",
                "message": "Task failed",
                "error": str(task_result.info),
            }

        return response

    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving task status"
        )


@router.get("/activity-summary/{trip_id}")
async def export_activity_summary(
    trip_id: UUID,
    current_user: User = Depends(require_permissions("trips", "read")),
    db: AsyncSession = Depends(get_db),
):
    """Export activity summary for quick reference."""
    try:
        # Verify user has access to trip
        trip_service = Container().trip_domain_service()
        trip = await trip_service.get_trip_by_id(trip_id, str(current_user.id))

        if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

        # Get itinerary data
        itinerary_data = await trip_service.get_latest_itinerary(trip_id, str(current_user.id))

        if not itinerary_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No itinerary found for this trip"
            )

        # Export activity summary
        export_service = DataExportService()
        result = await export_service.export_activity_summary(
            itinerary_data=itinerary_data, trip_id=str(trip_id), user_id=str(current_user.id)
        )

        return {
            "message": "Activity summary exported",
            "status": "SUCCESS",
            "summary": result,
            "trip_id": str(trip_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting activity summary for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting activity summary",
        )


@router.delete("/cleanup")
async def cleanup_old_exports(
    days_old: int = Query(7, ge=1, le=365, description="Delete exports older than this many days"),
    current_user: User = Depends(require_permissions("exports", "admin")),
):
    """Clean up old export files (admin only)."""
    try:
        from app.tasks.export_tasks import cleanup_old_exports

        # Start cleanup task
        task = cleanup_old_exports.delay()

        return {
            "message": "Export cleanup started",
            "task_id": task.id,
            "days_old": days_old,
            "check_status_url": f"/api/v1/exports/tasks/{task.id}",
        }

    except Exception as e:
        logger.error(f"Error starting export cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting cleanup process",
        )
