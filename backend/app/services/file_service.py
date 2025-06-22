"""
File service for Azure Blob Storage integration.
"""

import os
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from app.core.config import get_settings
from app.core.logging_config import get_logger
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient

logger = get_logger(__name__)
settings = get_settings()


class FileService:
    """Service for managing file uploads and downloads with Azure Blob Storage."""

    def __init__(self):
        self.client = None
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            self.client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
        self.container_name = settings.AZURE_STORAGE_CONTAINER

    async def ensure_container_exists(self):
        """Ensure the storage container exists."""
        if not self.client:
            raise RuntimeError("Azure Blob Storage not configured")

        try:
            container_client = self.client.get_container_client(self.container_name)
            await container_client.create_container()
            logger.info(f"Created container: {self.container_name}")
        except ResourceExistsError:
            logger.debug(f"Container already exists: {self.container_name}")

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> dict:
        """
        Upload a file to Azure Blob Storage.

        Args:
            file_data: File content as bytes
            filename: Original filename
            content_type: MIME type of the file
            folder: Folder/prefix for organization

        Returns:
            dict: File metadata including blob_name and url
        """
        if not self.client:
            raise RuntimeError("Azure Blob Storage not configured")

        await self.ensure_container_exists()

        # Generate unique blob name
        file_extension = os.path.splitext(filename)[1]
        blob_name = f"{folder}/{uuid4()}{file_extension}"

        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)

            # Upload with metadata
            metadata = {
                "original_filename": filename,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "content_type": content_type,
            }

            await blob_client.upload_blob(
                file_data,
                content_settings={
                    "content_type": content_type,
                    "content_disposition": f"attachment; filename={filename}",
                },
                metadata=metadata,
                overwrite=True,
            )

            # Get blob URL
            blob_url = blob_client.url

            logger.info(f"File uploaded successfully: {blob_name}")

            return {
                "blob_name": blob_name,
                "original_filename": filename,
                "url": blob_url,
                "content_type": content_type,
                "size": len(file_data),
                "uploaded_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            raise

    async def download_file(self, blob_name: str) -> tuple[bytes, dict]:
        """
        Download a file from Azure Blob Storage.

        Args:
            blob_name: Name of the blob to download

        Returns:
            tuple: (file_data, metadata)
        """
        if not self.client:
            raise RuntimeError("Azure Blob Storage not configured")

        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)

            # Download blob
            download_stream = await blob_client.download_blob()
            file_data = await download_stream.readall()

            # Get metadata
            properties = await blob_client.get_blob_properties()
            metadata = {
                "original_filename": properties.metadata.get("original_filename", blob_name),
                "content_type": properties.content_settings.content_type,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat(),
                "etag": properties.etag,
            }

            logger.info(f"File downloaded successfully: {blob_name}")
            return file_data, metadata

        except ResourceNotFoundError:
            logger.error(f"File not found: {blob_name}")
            raise FileNotFoundError(f"File not found: {blob_name}")
        except Exception as e:
            logger.error(f"Failed to download file {blob_name}: {e}")
            raise

    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Azure Blob Storage.

        Args:
            blob_name: Name of the blob to delete

        Returns:
            bool: True if deleted successfully
        """
        if not self.client:
            raise RuntimeError("Azure Blob Storage not configured")

        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)

            await blob_client.delete_blob()
            logger.info(f"File deleted successfully: {blob_name}")
            return True

        except ResourceNotFoundError:
            logger.warning(f"File not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {blob_name}: {e}")
            raise

    def generate_download_url(self, blob_name: str, expiry_hours: int = 24) -> str:
        """
        Generate a signed URL for downloading a file.

        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until the URL expires

        Returns:
            str: Signed download URL
        """
        if not settings.AZURE_STORAGE_ACCOUNT or not settings.AZURE_STORAGE_KEY:
            raise RuntimeError("Azure Storage account credentials not configured")

        sas_token = generate_blob_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=settings.AZURE_STORAGE_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
        )

        blob_url = f"https://{settings.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"
        return blob_url

    async def list_files(self, folder: str = None) -> List[dict]:
        """
        List files in a folder or container.

        Args:
            folder: Optional folder prefix to filter by

        Returns:
            List[dict]: List of file metadata
        """
        if not self.client:
            raise RuntimeError("Azure Blob Storage not configured")

        try:
            container_client = self.client.get_container_client(self.container_name)

            name_starts_with = folder + "/" if folder else None
            files = []

            async for blob in container_client.list_blobs(name_starts_with=name_starts_with):
                file_info = {
                    "blob_name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat(),
                    "content_type": (
                        blob.content_settings.content_type if blob.content_settings else None
                    ),
                    "etag": blob.etag,
                }

                # Add metadata if available
                if blob.metadata:
                    file_info.update(blob.metadata)

                files.append(file_info)

            logger.info(f"Listed {len(files)} files in folder: {folder or 'root'}")
            return files

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise

    async def get_file_info(self, blob_name: str) -> dict:
        """
        Get metadata for a specific file.

        Args:
            blob_name: Name of the blob

        Returns:
            dict: File metadata
        """
        if not self.client:
            raise RuntimeError("Azure Blob Storage not configured")

        try:
            blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)

            properties = await blob_client.get_blob_properties()

            file_info = {
                "blob_name": blob_name,
                "original_filename": properties.metadata.get("original_filename", blob_name),
                "content_type": properties.content_settings.content_type,
                "size": properties.size,
                "last_modified": properties.last_modified.isoformat(),
                "etag": properties.etag,
                "metadata": properties.metadata,
            }

            return file_info

        except ResourceNotFoundError:
            raise FileNotFoundError(f"File not found: {blob_name}")
        except Exception as e:
            logger.error(f"Failed to get file info for {blob_name}: {e}")
            raise


# Utility functions for common file operations


async def upload_user_avatar(file_data: bytes, user_id: str, filename: str) -> dict:
    """Upload user avatar image."""
    file_service = FileService()
    return await file_service.upload_file(
        file_data, filename, content_type="image/jpeg", folder=f"avatars/{user_id}"
    )


async def upload_trip_document(
    file_data: bytes, trip_id: str, filename: str, content_type: str
) -> dict:
    """Upload trip-related document."""
    file_service = FileService()
    return await file_service.upload_file(
        file_data,
        filename,
        content_type=content_type,
        folder=f"trips/{trip_id}/documents",
    )


async def upload_itinerary_pdf(file_data: bytes, trip_id: str, filename: str) -> dict:
    """Upload generated itinerary PDF."""
    file_service = FileService()
    return await file_service.upload_file(
        file_data,
        filename,
        content_type="application/pdf",
        folder=f"trips/{trip_id}/itineraries",
    )
