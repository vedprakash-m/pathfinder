from __future__ import annotations
"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository, UserDocument
from app.core.database_unified import get_cosmos_service
from app.core.security import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.export import ExportRequest, BulkExportRequest, ExportResponse
Export API endpoints for data export functionality.
"""

from typing import List
from uuid import UUID

from app.core.container import Container
from app.core.database_unified import get_cosmos_repository
from app.core.logging_config import get_logger
from app.core.security import get_current_user, require_permissions
# SQL User model removed - use Cosmos UserDocument
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.services.export_service import DataExportService
from app.tasks.export_tasks import bulk_export_trips, export_trip_data
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

router = APIRouter()
logger = get_logger(__name__)


class ExportRequest(BaseModel):
    """Export request model."""

format: str = "excel"
export_type: str = "complete"
async_processing: bool = True


class BulkExportRequest(BaseModel):
    """Bulk export request model."""

trip_ids: list[UUID]
format: str = "excel"
async_processing: bool = True


@router.post("/trips/{trip_id}")
async def export_trip(
    trip_id: UUID,
export_request: ExportRequest,
background_tasks: BackgroundTasks,
request: Request,
current_user: dict = Depends(require_permissions(["trips: read"])),
cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository)
):
    """Export trip data in various formats."""
try:
        # Verify user has access to trip
trip = await cosmos_repo.get_trip_by_id(str(trip_id))
if not trip:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

# Check if user has access to the trip
user_trips = await cosmos_repo.get_user_trips(current_user["id"])
if not any(t.id == str(trip_id) for t in user_trips):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to export this trip"
)

if export_request.async_processing:
            # Create export task record
export_data = {
                "user_id": current_user["id"],
"trip_id": str(trip_id),
"format": export_request.format,
"export_type": export_request.export_type,
"status": "pending",
}

export_task = await cosmos_repo.create_export_task(export_data)

# Process export asynchronously
task = export_trip_data.delay(
                trip_id=str(trip_id),
user_id=current_user["id"],
export_format=export_request.format,
export_type=export_request.export_type,
)

# Update task with Celery task ID
await cosmos_repo.update_export_task(export_task.id, {"task_id": task.id})

return {
                "message": "Export started",
"task_id": task.id,
"export_id": export_task.id,
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
user_id=str(current_user["id"]),
)
else:
                # Default to complete export
result = await export_service.export_trip_complete(
                    trip_id=str(trip_id),
format_type=export_request.format,
user_id=str(current_user["id"]),
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


@router.get("/tasks/{task_id}")
async def get_export_task_status(
    task_id: str,
current_user: dict = Depends(get_current_user),
):
    """Get the status of an export task."""
try:
        # Get task result (this would integrate with Celery)
# For now, return a mock response
return {
            "task_id": task_id,
"status": "SUCCESS",
"message": "Export completed",
"result": {"download_url": f"/downloads/{task_id}.xlsx"},
}

except Exception as e:
        logger.error(f"Error getting task status {task_id}: {e}")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail="Error getting task status",
)
