"""Export-related schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class ExportRequest(BaseModel):
    """Schema for export request."""
    format: str = Field(default="excel", pattern="^(excel|csv|json|pdf)$")
    export_type: str = Field(default="complete", pattern="^(complete|summary|custom)$")
    async_processing: bool = True

class BulkExportRequest(BaseModel):
    """Schema for bulk export request."""
    trip_ids: List[UUID]
    format: str = Field(default="excel", pattern="^(excel|csv|json|pdf)$")
    async_processing: bool = True

class ExportResponse(BaseModel):
    """Schema for export response."""
    task_id: str
    status: str
    download_url: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None

class ExportTaskStatus(BaseModel):
    """Schema for export task status."""
    task_id: str
    status: str
    progress: Optional[int] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
