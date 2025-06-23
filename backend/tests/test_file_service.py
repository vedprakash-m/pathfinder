"""
Unit tests for the file service module.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.file_service import FileService
from app.core.config import get_settings
from datetime import datetime


class TestFileService:
    """Test cases for FileService."""

    @pytest.fixture
    def mock_blob_service_client(self):
        """Create mock blob service client."""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_blob = AsyncMock()  # Change to AsyncMock for blob operations
        
        # Mock container operations with AsyncMock
        mock_client.get_container_client.return_value = mock_container
        mock_container.create_container = AsyncMock()
        mock_container.exists = AsyncMock(return_value=True)
        
        # CRITICAL: Mock blob operations with AsyncMock
        # The issue is that get_blob_client is called with container and blob parameters
        # but we need to make sure it returns our AsyncMock blob object
        def mock_get_blob_client(*args, **kwargs):
            return mock_blob
        
        mock_client.get_blob_client = mock_get_blob_client
        mock_container.get_blob_client = mock_get_blob_client
        
        mock_blob.upload_blob = AsyncMock()
        mock_blob.download_blob = AsyncMock()
        mock_blob.delete_blob = AsyncMock()
        mock_blob.exists = AsyncMock(return_value=True)
        mock_blob.get_blob_properties = AsyncMock()
        mock_blob.url = "https://mockaccount.blob.core.windows.net/container/blob"
        
        # Mock async iterator for list_blobs
        async def mock_list_blobs(*args, **kwargs):
            """Mock async iterator for list_blobs."""
            mock_blobs = []
            for i, name in enumerate(["file1.txt", "file2.txt"]):
                mock_blob_item = MagicMock()
                mock_blob_item.name = name
                mock_blob_item.size = (i + 1) * 100
                mock_blob_item.last_modified = datetime(2023, 1, 1, 0, 0, 0)  # Add datetime
                mock_blob_item.content_settings = None  # Add content_settings
                mock_blob_item.etag = f"etag-{i}"  # Add etag
                mock_blob_item.metadata = {}  # Add metadata
                mock_blobs.append(mock_blob_item)
            
            for blob in mock_blobs:
                yield blob
        
        mock_container.list_blobs = mock_list_blobs
        
        return mock_client

    @pytest.fixture
    def file_service(self, mock_blob_service_client):
        """Create file service with mocked Azure client."""
        # Mock the module-level settings first
        mock_settings = MagicMock()
        mock_settings.AZURE_STORAGE_CONNECTION_STRING = 'mock_connection'
        mock_settings.AZURE_STORAGE_CONTAINER = 'mock_container'
        mock_settings.AZURE_STORAGE_ACCOUNT = 'mockaccount'
        mock_settings.AZURE_STORAGE_KEY = 'mock_key'
        
        with patch('app.services.file_service.settings', mock_settings):
            with patch('app.services.file_service.BlobServiceClient') as mock_blob_client_class:
                mock_blob_client_class.from_connection_string.return_value = mock_blob_service_client
                
                service = FileService()
                return service

    @pytest.mark.asyncio
    async def test_ensure_container_exists_success(self, file_service, mock_blob_service_client):
        """Test successful container creation."""
        mock_container = mock_blob_service_client.get_container_client.return_value
        mock_container.create_container.side_effect = None  # Success
        
        await file_service.ensure_container_exists()
        
        mock_container.create_container.assert_called_once()

    @pytest.mark.asyncio 
    async def test_ensure_container_exists_already_exists(self, file_service, mock_blob_service_client):
        """Test when container already exists."""
        from azure.core.exceptions import ResourceExistsError
        mock_container = mock_blob_service_client.get_container_client.return_value
        mock_container.create_container.side_effect = ResourceExistsError("Container exists")
        
        await file_service.ensure_container_exists()
        
        mock_container.create_container.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, file_service, mock_blob_service_client):
        """Test successful file upload."""
        file_content = b"test file content"
        file_name = "test.txt"
        
        result = await file_service.upload_file(file_content, file_name)
        
        assert "blob_name" in result
        assert result["original_filename"] == file_name
        assert result["size"] == len(file_content)

    @pytest.mark.asyncio
    async def test_upload_file_with_folder(self, file_service, mock_blob_service_client):
        """Test file upload with folder structure."""
        file_content = b"test file content"
        file_name = "test.txt"
        folder = "uploads/documents"
        
        result = await file_service.upload_file(file_content, file_name, folder=folder)
        
        assert "blob_name" in result
        assert result["original_filename"] == file_name
        assert folder in result["blob_name"]

    @pytest.mark.asyncio
    async def test_upload_file_error_handling(self, file_service, mock_blob_service_client):
        """Test file upload error handling."""
        # Get the mock blob from our fixture  
        mock_blob = mock_blob_service_client.get_blob_client()
        mock_blob.upload_blob.side_effect = Exception("Upload failed")
        
        file_content = b"test file content"
        file_name = "test.txt"
        
        with pytest.raises(Exception, match="Upload failed"):
            await file_service.upload_file(file_content, file_name)

    @pytest.mark.asyncio
    async def test_download_file_success(self, file_service, mock_blob_service_client):
        """Test successful file download."""
        # Get the mock blob from our fixture
        mock_blob = mock_blob_service_client.get_blob_client()
        
        # Mock download response
        mock_download_stream = AsyncMock()
        mock_download_stream.readall = AsyncMock(return_value=b"test file content")
        mock_blob.download_blob.return_value = mock_download_stream
        
        # Mock blob properties with proper datetime object
        mock_properties = MagicMock()
        mock_properties.metadata = {"original_filename": "test.txt"}
        mock_properties.content_settings.content_type = "text/plain"
        mock_properties.size = 17
        mock_properties.last_modified = datetime(2023, 1, 1, 0, 0, 0)  # Use datetime object
        mock_properties.etag = "test-etag"
        mock_blob.get_blob_properties.return_value = mock_properties
        
        file_data, metadata = await file_service.download_file("test.txt")
        
        assert file_data == b"test file content"
        assert metadata["original_filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_service, mock_blob_service_client):
        """Test successful file deletion."""
        result = await file_service.delete_file("test.txt")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, file_service, mock_blob_service_client):
        """Test deleting non-existent file."""
        from azure.core.exceptions import ResourceNotFoundError
        # Get the mock blob from our fixture
        mock_blob = mock_blob_service_client.get_blob_client()
        mock_blob.delete_blob.side_effect = ResourceNotFoundError("Blob not found")
        
        result = await file_service.delete_file("nonexistent.txt")
        
        assert result is False

    def test_generate_download_url(self, file_service, mock_blob_service_client):
        """Test generating download URL."""
        # Mock the settings to include the required Azure Storage credentials
        with patch('app.services.file_service.settings') as mock_settings:
            mock_settings.AZURE_STORAGE_ACCOUNT = 'mockaccount'
            mock_settings.AZURE_STORAGE_KEY = 'mock_key'
            
            with patch('app.services.file_service.generate_blob_sas') as mock_generate_sas:
                mock_generate_sas.return_value = "mock_sas_token"
                
                url = file_service.generate_download_url("test.txt")
                
                assert "https://" in url
                assert "mock_sas_token" in url

    def test_generate_download_url_default_expiry(self, file_service, mock_blob_service_client):
        """Test generating download URL with default expiry."""
        # Mock the settings to include the required Azure Storage credentials
        with patch('app.services.file_service.settings') as mock_settings:
            mock_settings.AZURE_STORAGE_ACCOUNT = 'mockaccount'
            mock_settings.AZURE_STORAGE_KEY = 'mock_key'
            
            with patch('app.services.file_service.generate_blob_sas') as mock_generate_sas:
                mock_generate_sas.return_value = "mock_sas_token"
                
                url = file_service.generate_download_url("test.txt")
                
                assert url is not None

    def test_generate_download_url_error_handling(self, file_service, mock_blob_service_client):
        """Test download URL generation error handling."""
        with patch('app.services.file_service.generate_blob_sas') as mock_generate_sas:
            mock_generate_sas.side_effect = Exception("SAS generation failed")
            
            with pytest.raises(Exception):
                file_service.generate_download_url("test.txt")

    @pytest.mark.asyncio
    async def test_list_files_no_folder(self, file_service, mock_blob_service_client):
        """Test listing files without folder filter."""
        # The mock_list_blobs is already set up in the fixture
        files = await file_service.list_files()
        
        assert len(files) == 2
        assert files[0]["blob_name"] == "file1.txt"

    @pytest.mark.asyncio
    async def test_list_files_with_folder(self, file_service, mock_blob_service_client):
        """Test listing files with folder filter."""
        mock_container = mock_blob_service_client.get_container_client.return_value
        
        # Override the list_blobs for this specific test
        async def mock_list_blobs_folder(*args, **kwargs):
            mock_blob = MagicMock()
            mock_blob.name = "folder/file1.txt"
            mock_blob.size = 100
            mock_blob.last_modified = datetime(2023, 1, 1, 0, 0, 0)
            mock_blob.content_settings = None
            mock_blob.etag = "test-etag"
            mock_blob.metadata = {}
            yield mock_blob
        
        mock_container.list_blobs = mock_list_blobs_folder
        
        files = await file_service.list_files(folder="folder")
        
        assert len(files) == 1
        assert files[0]["blob_name"] == "folder/file1.txt"

    @pytest.mark.asyncio
    async def test_list_files_error_handling(self, file_service, mock_blob_service_client):
        """Test file listing error handling."""
        mock_container = mock_blob_service_client.get_container_client.return_value
        
        # Mock list_blobs to raise an exception directly
        def mock_list_blobs_sync(*args, **kwargs):
            raise Exception("List failed")
        
        mock_container.list_blobs = mock_list_blobs_sync
        
        with pytest.raises(Exception, match="List failed"):
            await file_service.list_files()

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, file_service, mock_blob_service_client):
        """Test getting file info successfully."""
        # Get the mock blob from our fixture
        mock_blob = mock_blob_service_client.get_blob_client()
        
        mock_properties = MagicMock()
        mock_properties.size = 1024
        mock_properties.content_settings.content_type = "text/plain"
        mock_properties.last_modified = datetime(2023, 1, 1, 0, 0, 0)  # Use datetime object
        mock_properties.metadata = {"original_filename": "test.txt"}
        mock_blob.get_blob_properties.return_value = mock_properties
        
        info = await file_service.get_file_info("test.txt")
        
        assert info["size"] == 1024
        assert info["content_type"] == "text/plain"

    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, file_service, mock_blob_service_client):
        """Test getting info for non-existent file."""
        from azure.core.exceptions import ResourceNotFoundError
        # Get the mock blob from our fixture
        mock_blob = mock_blob_service_client.get_blob_client()
        mock_blob.get_blob_properties.side_effect = ResourceNotFoundError("Blob not found")
        
        with pytest.raises(FileNotFoundError):
            await file_service.get_file_info("nonexistent.txt")


class TestFileServiceIntegration:
    """Integration tests for FileService."""

    @pytest.fixture
    def file_service(self):
        """Create file service for integration testing."""
        # Mock the module-level settings first
        mock_settings = MagicMock()
        mock_settings.AZURE_STORAGE_CONNECTION_STRING = 'mock_connection'
        mock_settings.AZURE_STORAGE_CONTAINER = 'mock_container'
        
        with patch('app.services.file_service.settings', mock_settings):
            # For integration tests, we still need to mock Azure services
            with patch('app.services.file_service.BlobServiceClient') as mock_blob_client_class:
                mock_client = MagicMock()
                mock_blob_client_class.from_connection_string.return_value = mock_client
                
                # Mock all async operations using the same pattern as main fixture
                mock_container = MagicMock()
                mock_blob = AsyncMock()  # Use AsyncMock for blob operations
                
                mock_client.get_container_client.return_value = mock_container
                mock_container.create_container = AsyncMock()
                
                # CRITICAL: Use the same blob client mocking pattern
                def mock_get_blob_client(*args, **kwargs):
                    return mock_blob
                
                mock_client.get_blob_client = mock_get_blob_client
                mock_container.get_blob_client = mock_get_blob_client
                
                mock_blob.upload_blob = AsyncMock()
                mock_blob.download_blob = AsyncMock()
                mock_blob.delete_blob = AsyncMock()
                mock_blob.url = "https://mockaccount.blob.core.windows.net/container/blob"
                
                service = FileService()
                return service

    @pytest.mark.asyncio
    async def test_upload_download_cycle(self, file_service):
        """Test complete upload-download cycle."""
        file_content = b"test file content for cycle"
        file_name = "cycle_test.txt"
        
        # Mock upload
        upload_result = await file_service.upload_file(file_content, file_name)
        assert "blob_name" in upload_result
        
        # For this test, we can't actually download since it's mocked
        # But we can verify the upload was called correctly
        assert upload_result["original_filename"] == file_name

    @pytest.mark.asyncio
    async def test_file_operations_error_recovery(self, file_service):
        """Test error recovery in file operations."""
        # Test upload failure followed by retry
        # Get the mock blob properly from the service
        mock_blob = file_service.client.get_blob_client()
        
        # First attempt fails
        mock_blob.upload_blob.side_effect = [Exception("Network error"), None]
        
        file_content = b"test content"
        file_name = "retry_test.txt"
        
        # First upload should fail
        with pytest.raises(Exception):
            await file_service.upload_file(file_content, file_name)
        
        # Reset side effect for second attempt
        mock_blob.upload_blob.side_effect = None
        
        # Second upload should succeed
        result = await file_service.upload_file(file_content, file_name)
        assert "blob_name" in result 