"""
Usage Logger - Comprehensive logging service for LLM requests and responses
Tracks usage patterns, performance metrics, and audit trails
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog
from core.types import LLMRequest, LLMResponse, TenantInfo

logger = structlog.get_logger(__name__)


class UsageLogger:
    """
    Logs all LLM usage data for analytics, billing, and audit purposes
    Supports multiple storage backends (database, files, external services)
    """

    def __init__(
        self,
        storage_backend: str = "database",  # database, file, elasticsearch
        database_url: Optional[str] = None,
        log_file_path: Optional[str] = None,
        batch_size: int = 100,
        flush_interval: int = 30,
    ):
        self.storage_backend = storage_backend
        self.database_url = database_url
        self.log_file_path = log_file_path
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # Batching for performance
        self.log_batch: list = []
        self.last_flush_time = time.time()

        # Statistics
        self.logs_written = 0
        self.logs_failed = 0

        # Background task for periodic flushing
        self.flush_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the usage logger and background tasks"""
        logger.info("Starting usage logger", backend=self.storage_backend)

        # Initialize storage backend
        await self._initialize_storage()

        # Start background flush task
        self.flush_task = asyncio.create_task(self._periodic_flush())

    async def log_request(
        self,
        request: LLMRequest,
        response: LLMResponse,
        tenant_info: TenantInfo,
        processing_time: float,
        cost: float,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a completed LLM request with full details
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.request_id,
            "tenant_id": tenant_info.tenant_id,
            "user_id": request.user_id,
            # Request details
            "request": {
                "prompt_length": len(request.prompt),
                "prompt_hash": self._hash_prompt(request.prompt),
                "model_preference": (
                    request.model_preference.value if request.model_preference else None
                ),
                "task_type": request.task_type.value,
                "priority": request.priority.value,
                "parameters": request.parameters.dict() if request.parameters else {},
                "context_length": len(request.context) if request.context else 0,
            },
            # Response details
            "response": {
                "model_used": response.model_used,
                "provider": response.provider,
                "content_length": len(response.content),
                "finish_reason": response.finish_reason,
                "token_usage": response.usage.dict() if response.usage else {},
                "response_time": processing_time,
            },
            # Cost and billing
            "cost": {
                "estimated_cost": cost,
                "currency": "USD",
                "billing_unit": "tokens",
            },
            # Performance metrics
            "performance": {
                "processing_time_ms": processing_time * 1000,
                "tokens_per_second": self._calculate_tokens_per_second(response, processing_time),
                "cache_hit": response.from_cache if hasattr(response, "from_cache") else False,
            },
            # Additional metadata
            "metadata": additional_metadata or {},
        }

        await self._add_to_batch(log_entry)

    async def log_error(
        self,
        request: LLMRequest,
        tenant_info: TenantInfo,
        error: Exception,
        processing_time: float,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a failed LLM request
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.request_id,
            "tenant_id": tenant_info.tenant_id,
            "user_id": request.user_id,
            "event_type": "error",
            # Request details
            "request": {
                "prompt_length": len(request.prompt),
                "prompt_hash": self._hash_prompt(request.prompt),
                "model_preference": (
                    request.model_preference.value if request.model_preference else None
                ),
                "task_type": request.task_type.value,
                "priority": request.priority.value,
            },
            # Error details
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "processing_time": processing_time,
            },
            # Additional metadata
            "metadata": additional_metadata or {},
        }

        await self._add_to_batch(log_entry)

    async def log_cache_hit(
        self, request: LLMRequest, tenant_info: TenantInfo, processing_time: float
    ) -> None:
        """
        Log a cache hit event
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.request_id,
            "tenant_id": tenant_info.tenant_id,
            "user_id": request.user_id,
            "event_type": "cache_hit",
            # Request details
            "request": {
                "prompt_length": len(request.prompt),
                "prompt_hash": self._hash_prompt(request.prompt),
                "task_type": request.task_type.value,
            },
            # Performance
            "performance": {
                "processing_time_ms": processing_time * 1000,
                "cache_hit": True,
            },
            # Cost savings
            "cost": {
                "estimated_savings": 0.01,  # Estimated cost saved by cache hit
                "currency": "USD",
            },
        }

        await self._add_to_batch(log_entry)

    async def _add_to_batch(self, log_entry: Dict[str, Any]) -> None:
        """Add log entry to batch for efficient writing"""
        self.log_batch.append(log_entry)

        # Flush if batch is full
        if len(self.log_batch) >= self.batch_size:
            await self._flush_batch()

    async def _flush_batch(self) -> None:
        """Flush current batch to storage"""
        if not self.log_batch:
            return

        batch_to_write = self.log_batch.copy()
        self.log_batch.clear()
        self.last_flush_time = time.time()

        try:
            await self._write_logs(batch_to_write)
            self.logs_written += len(batch_to_write)

            logger.debug(
                "Log batch flushed successfully",
                batch_size=len(batch_to_write),
                total_logs=self.logs_written,
            )

        except Exception as e:
            self.logs_failed += len(batch_to_write)
            logger.error("Failed to write log batch", batch_size=len(batch_to_write), error=str(e))

            # Re-add failed logs to batch for retry (with limit)
            if len(batch_to_write) < 1000:  # Prevent memory buildup
                self.log_batch.extend(batch_to_write)

    async def _periodic_flush(self) -> None:
        """Background task to periodically flush logs"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.flush_interval)

                # Check if it's time to flush
                if (time.time() - self.last_flush_time) >= self.flush_interval:
                    await self._flush_batch()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic flush", error=str(e))

    async def _initialize_storage(self) -> None:
        """Initialize the storage backend"""
        if self.storage_backend == "database":
            await self._initialize_database()
        elif self.storage_backend == "file":
            await self._initialize_file_storage()
        elif self.storage_backend == "elasticsearch":
            await self._initialize_elasticsearch()

    async def _initialize_database(self) -> None:
        """Initialize database storage"""
        # TODO: Implement database initialization
        # This would create the usage_logs table if it doesn't exist
        logger.info("Database storage initialized")

    async def _initialize_file_storage(self) -> None:
        """Initialize file-based storage"""
        if self.log_file_path:
            import os

            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            logger.info("File storage initialized", path=self.log_file_path)

    async def _initialize_elasticsearch(self) -> None:
        """Initialize Elasticsearch storage"""
        # TODO: Implement Elasticsearch initialization
        logger.info("Elasticsearch storage initialized")

    async def _write_logs(self, log_entries: list) -> None:
        """Write log entries to storage backend"""
        if self.storage_backend == "database":
            await self._write_to_database(log_entries)
        elif self.storage_backend == "file":
            await self._write_to_file(log_entries)
        elif self.storage_backend == "elasticsearch":
            await self._write_to_elasticsearch(log_entries)

    async def _write_to_database(self, log_entries: list) -> None:
        """Write logs to database"""
        # TODO: Implement database writing
        # This would insert log entries into the usage_logs table
        pass

    async def _write_to_file(self, log_entries: list) -> None:
        """Write logs to file"""
        if not self.log_file_path:
            return

        import aiofiles

        async with aiofiles.open(self.log_file_path, "a") as f:
            for entry in log_entries:
                await f.write(json.dumps(entry) + "\n")

    async def _write_to_elasticsearch(self, log_entries: list) -> None:
        """Write logs to Elasticsearch"""
        # TODO: Implement Elasticsearch writing
        pass

    def _hash_prompt(self, prompt: str) -> str:
        """Create hash of prompt for privacy (don't store full prompt)"""
        import hashlib

        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def _calculate_tokens_per_second(
        self, response: LLMResponse, processing_time: float
    ) -> Optional[float]:
        """Calculate tokens per second for performance metrics"""
        if response.usage and response.usage.completion_tokens and processing_time > 0:
            return response.usage.completion_tokens / processing_time
        return None

    async def get_usage_stats(
        self,
        tenant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a tenant or globally
        """
        # TODO: Implement querying logic based on storage backend
        return {
            "logs_written": self.logs_written,
            "logs_failed": self.logs_failed,
            "batch_size": len(self.log_batch),
            "storage_backend": self.storage_backend,
        }

    async def close(self) -> None:
        """Shutdown usage logger gracefully"""
        logger.info("Shutting down usage logger")

        # Signal shutdown to background tasks
        self.shutdown_event.set()

        # Cancel flush task
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass

        # Flush any remaining logs
        await self._flush_batch()

        logger.info("Usage logger shutdown complete")
