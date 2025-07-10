"""
Analytics Collector - Comprehensive metrics and analytics collection
Tracks performance, usage patterns, costs, and system health
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from core.llm_types import LLMRequest, LLMResponse, TenantInfo

logger = structlog.get_logger(__name__)


class MetricsBuffer:
    """Thread-safe buffer for storing metrics with time windows"""

    def __init__(self, max_size: int = 10000, time_window: int = 3600):
        self.max_size = max_size
        self.time_window = time_window  # seconds
        self.data = deque(maxlen=max_size)
        self._lock = asyncio.Lock()

    async def add(self, metric: Dict[str, Any]) -> None:
        async with self._lock:
            metric["timestamp"] = time.time()
            self.data.append(metric)

    async def get_recent(self, seconds: int = 300) -> List[Dict[str, Any]]:
        """Get metrics from the last N seconds"""
        async with self._lock:
            cutoff = time.time() - seconds
            return [m for m in self.data if m.get("timestamp", 0) >= cutoff]

    async def get_all(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.data)


class AnalyticsCollector:
    """
    Collects and aggregates analytics data for the LLM orchestration system
    Provides real-time metrics, usage patterns, and performance insights
    """

    def __init__(
        self, metrics_retention_hours: int = 24, aggregation_interval: int = 60  # seconds
    ):
        self.metrics_retention_hours = metrics_retention_hours
        self.aggregation_interval = aggregation_interval

        # Metrics buffers
        self.request_metrics = MetricsBuffer()
        self.performance_metrics = MetricsBuffer()
        self.cost_metrics = MetricsBuffer()
        self.error_metrics = MetricsBuffer()
        self.cache_metrics = MetricsBuffer()

        # Aggregated statistics
        self.aggregated_stats = {
            "requests_per_minute": defaultdict(int),
            "errors_per_minute": defaultdict(int),
            "cost_per_hour": defaultdict(float),
            "provider_usage": defaultdict(int),
            "tenant_usage": defaultdict(int),
            "task_type_distribution": defaultdict(int),
            "average_response_time": defaultdict(list),
        }

        # Background tasks
        self.aggregation_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start background analytics tasks"""
        logger.info("Starting analytics collector")

        # Start background aggregation
        self.aggregation_task = asyncio.create_task(self._periodic_aggregation())
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def record_request_metrics(
        self,
        request: LLMRequest,
        response: LLMResponse,
        tenant_info: TenantInfo,
        processing_time: float,
        cost: float,
    ) -> None:
        """Record comprehensive metrics for a completed request"""

        # Request metrics
        await self.request_metrics.add(
            {
                "type": "request",
                "request_id": request.request_id,
                "tenant_id": tenant_info.tenant_id,
                "user_id": request.user_id,
                "provider": response.provider,
                "model": response.model_used,
                "task_type": request.task_type.value,
                "priority": request.priority.value,
                "processing_time": processing_time,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
                "finish_reason": response.finish_reason,
                "from_cache": False,
            }
        )

        # Performance metrics
        await self.performance_metrics.add(
            {
                "type": "performance",
                "provider": response.provider,
                "model": response.model_used,
                "processing_time": processing_time,
                "tokens_per_second": (
                    response.usage.completion_tokens / processing_time
                    if response.usage and response.usage.completion_tokens and processing_time > 0
                    else 0
                ),
                "request_size": len(request.prompt),
                "response_size": len(response.content),
            }
        )

        # Cost metrics
        await self.cost_metrics.add(
            {
                "type": "cost",
                "tenant_id": tenant_info.tenant_id,
                "provider": response.provider,
                "model": response.model_used,
                "cost": cost,
                "tokens": response.usage.total_tokens if response.usage else 0,
            }
        )

    async def record_cache_hit(
        self, request: LLMRequest, tenant_info: TenantInfo, processing_time: float
    ) -> None:
        """Record cache hit metrics"""

        await self.cache_metrics.add(
            {
                "type": "cache_hit",
                "tenant_id": tenant_info.tenant_id,
                "user_id": request.user_id,
                "task_type": request.task_type.value,
                "processing_time": processing_time,
                "cost_saved": 0.01,  # Estimated cost savings
            }
        )

        await self.request_metrics.add(
            {
                "type": "request",
                "request_id": request.request_id,
                "tenant_id": tenant_info.tenant_id,
                "user_id": request.user_id,
                "provider": "cache",
                "model": "cache",
                "task_type": request.task_type.value,
                "processing_time": processing_time,
                "from_cache": True,
            }
        )

    async def record_error(
        self, request: LLMRequest, tenant_info: TenantInfo, error: Exception, processing_time: float
    ) -> None:
        """Record error metrics"""

        await self.error_metrics.add(
            {
                "type": "error",
                "request_id": request.request_id,
                "tenant_id": tenant_info.tenant_id,
                "user_id": request.user_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "task_type": request.task_type.value,
                "processing_time": processing_time,
                "model_preference": (
                    request.model_preference.value if request.model_preference else None
                ),
            }
        )

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time system metrics for monitoring"""

        # Get recent metrics (last 5 minutes)
        recent_requests = await self.request_metrics.get_recent(300)
        recent_errors = await self.error_metrics.get_recent(300)
        recent_performance = await self.performance_metrics.get_recent(300)
        recent_cache = await self.cache_metrics.get_recent(300)

        # Calculate real-time stats
        total_requests = len(recent_requests)
        total_errors = len(recent_errors)
        cache_hits = len(recent_cache)

        # Request rate (per minute)
        request_rate = total_requests / 5.0 if total_requests > 0 else 0

        # Error rate
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # Cache hit rate
        cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0

        # Average response time
        response_times = [r["processing_time"] for r in recent_requests if "processing_time" in r]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Provider distribution
        provider_counts = defaultdict(int)
        for request in recent_requests:
            if request.get("provider"):
                provider_counts[request["provider"]] += 1

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_rate_per_minute": request_rate,
            "total_requests_5min": total_requests,
            "error_rate_percent": error_rate,
            "cache_hit_rate_percent": cache_hit_rate,
            "average_response_time_ms": avg_response_time * 1000,
            "provider_distribution": dict(provider_counts),
            "active_providers": len(provider_counts),
            "performance_summary": {
                "fastest_response": min(response_times) * 1000 if response_times else 0,
                "slowest_response": max(response_times) * 1000 if response_times else 0,
                "p95_response_time": (
                    self._calculate_percentile(response_times, 0.95) * 1000 if response_times else 0
                ),
            },
        }

    async def get_tenant_analytics(self, tenant_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get analytics for a specific tenant"""

        # Get metrics for the specified time window
        cutoff_time = time.time() - (hours * 3600)

        all_requests = await self.request_metrics.get_all()
        tenant_requests = [
            r
            for r in all_requests
            if r.get("tenant_id") == tenant_id and r.get("timestamp", 0) >= cutoff_time
        ]

        all_costs = await self.cost_metrics.get_all()
        tenant_costs = [
            c
            for c in all_costs
            if c.get("tenant_id") == tenant_id and c.get("timestamp", 0) >= cutoff_time
        ]

        all_errors = await self.error_metrics.get_all()
        tenant_errors = [
            e
            for e in all_errors
            if e.get("tenant_id") == tenant_id and e.get("timestamp", 0) >= cutoff_time
        ]

        # Calculate tenant-specific metrics
        total_requests = len(tenant_requests)
        total_cost = sum(c.get("cost", 0) for c in tenant_costs)
        total_errors = len(tenant_errors)

        # Model usage distribution
        model_usage = defaultdict(int)
        for request in tenant_requests:
            if request.get("model"):
                model_usage[request["model"]] += 1

        # Task type distribution
        task_distribution = defaultdict(int)
        for request in tenant_requests:
            if request.get("task_type"):
                task_distribution[request["task_type"]] += 1

        # Token usage
        total_tokens = sum(r.get("total_tokens", 0) for r in tenant_requests)

        return {
            "tenant_id": tenant_id,
            "time_period_hours": hours,
            "summary": {
                "total_requests": total_requests,
                "total_cost": total_cost,
                "total_errors": total_errors,
                "error_rate_percent": (
                    (total_errors / total_requests * 100) if total_requests > 0 else 0
                ),
                "average_cost_per_request": (
                    total_cost / total_requests if total_requests > 0 else 0
                ),
                "total_tokens": total_tokens,
            },
            "usage_patterns": {
                "model_distribution": dict(model_usage),
                "task_type_distribution": dict(task_distribution),
                "hourly_usage": self._calculate_hourly_usage(tenant_requests, hours),
            },
            "cost_breakdown": {
                "total_cost": total_cost,
                "cost_by_model": self._calculate_cost_by_model(tenant_costs),
                "cost_trend": self._calculate_cost_trend(tenant_costs, hours),
            },
        }

    async def get_system_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system-wide analytics"""

        cutoff_time = time.time() - (hours * 3600)

        # Get all recent metrics
        all_requests = await self.request_metrics.get_all()
        recent_requests = [r for r in all_requests if r.get("timestamp", 0) >= cutoff_time]

        all_costs = await self.cost_metrics.get_all()
        recent_costs = [c for c in all_costs if c.get("timestamp", 0) >= cutoff_time]

        all_errors = await self.error_metrics.get_all()
        recent_errors = [e for e in all_errors if e.get("timestamp", 0) >= cutoff_time]

        # System-wide calculations
        total_requests = len(recent_requests)
        total_cost = sum(c.get("cost", 0) for c in recent_costs)
        total_errors = len(recent_errors)

        # Provider performance
        provider_stats = defaultdict(lambda: {"requests": 0, "errors": 0, "total_time": 0})
        for request in recent_requests:
            provider = request.get("provider", "unknown")
            provider_stats[provider]["requests"] += 1
            provider_stats[provider]["total_time"] += request.get("processing_time", 0)

        for error in recent_errors:
            provider = error.get("provider", "unknown")
            provider_stats[provider]["errors"] += 1

        # Calculate provider metrics
        provider_metrics = {}
        for provider, stats in provider_stats.items():
            provider_metrics[provider] = {
                "requests": stats["requests"],
                "errors": stats["errors"],
                "error_rate": (
                    (stats["errors"] / stats["requests"] * 100) if stats["requests"] > 0 else 0
                ),
                "avg_response_time": (
                    (stats["total_time"] / stats["requests"]) if stats["requests"] > 0 else 0
                ),
            }

        return {
            "time_period_hours": hours,
            "system_summary": {
                "total_requests": total_requests,
                "total_cost": total_cost,
                "total_errors": total_errors,
                "average_requests_per_hour": total_requests / hours if hours > 0 else 0,
                "system_error_rate": (
                    (total_errors / total_requests * 100) if total_requests > 0 else 0
                ),
            },
            "provider_performance": provider_metrics,
            "tenant_summary": self._calculate_tenant_summary(recent_requests, recent_costs),
            "usage_trends": {
                "hourly_requests": self._calculate_hourly_usage(recent_requests, hours),
                "cost_per_hour": self._calculate_hourly_costs(recent_costs, hours),
            },
        }

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _calculate_hourly_usage(self, requests: List[Dict], hours: int) -> Dict[str, int]:
        """Calculate usage per hour"""
        hourly_usage = defaultdict(int)
        current_time = time.time()

        for request in requests:
            timestamp = request.get("timestamp", 0)
            hour_key = int((current_time - timestamp) // 3600)
            if hour_key < hours:
                hourly_usage[f"hour_{hour_key}"] += 1

        return dict(hourly_usage)

    def _calculate_cost_by_model(self, costs: List[Dict]) -> Dict[str, float]:
        """Calculate total cost by model"""
        model_costs = defaultdict(float)
        for cost in costs:
            model = cost.get("model", "unknown")
            model_costs[model] += cost.get("cost", 0)

        return dict(model_costs)

    def _calculate_cost_trend(self, costs: List[Dict], hours: int) -> List[Dict[str, Any]]:
        """Calculate cost trend over time"""
        hourly_costs = defaultdict(float)
        current_time = time.time()

        for cost in costs:
            timestamp = cost.get("timestamp", 0)
            hour_key = int((current_time - timestamp) // 3600)
            if hour_key < hours:
                hourly_costs[hour_key] += cost.get("cost", 0)

        # Convert to time series
        trend = []
        for hour in range(hours):
            trend.append(
                {
                    "hour_offset": hour,
                    "cost": hourly_costs[hour],
                    "timestamp": current_time - (hour * 3600),
                }
            )

        return trend

    def _calculate_tenant_summary(self, requests: List[Dict], costs: List[Dict]) -> Dict[str, Any]:
        """Calculate summary by tenant"""
        tenant_stats = defaultdict(lambda: {"requests": 0, "cost": 0})

        for request in requests:
            tenant_id = request.get("tenant_id", "unknown")
            tenant_stats[tenant_id]["requests"] += 1

        for cost in costs:
            tenant_id = cost.get("tenant_id", "unknown")
            tenant_stats[tenant_id]["cost"] += cost.get("cost", 0)

        return {
            tenant_id: {
                "requests": stats["requests"],
                "total_cost": stats["cost"],
                "avg_cost_per_request": (
                    stats["cost"] / stats["requests"] if stats["requests"] > 0 else 0
                ),
            }
            for tenant_id, stats in tenant_stats.items()
        }

    def _calculate_hourly_costs(self, costs: List[Dict], hours: int) -> Dict[str, float]:
        """Calculate costs per hour"""
        hourly_costs = defaultdict(float)
        current_time = time.time()

        for cost in costs:
            timestamp = cost.get("timestamp", 0)
            hour_key = int((current_time - timestamp) // 3600)
            if hour_key < hours:
                hourly_costs[f"hour_{hour_key}"] += cost.get("cost", 0)

        return dict(hourly_costs)

    async def _periodic_aggregation(self) -> None:
        """Background task for periodic data aggregation"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.aggregation_interval)

                # Perform aggregation operations
                await self._aggregate_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic aggregation", error=str(e))

    async def _periodic_cleanup(self) -> None:
        """Background task for cleaning up old metrics"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(3600)  # Clean up every hour

                # Clean up old metrics
                await self._cleanup_old_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic cleanup", error=str(e))

    async def _aggregate_metrics(self) -> None:
        """Aggregate recent metrics for faster querying"""
        # TODO: Implement metric aggregation logic
        pass

    async def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period"""
        cutoff_time = time.time() - (self.metrics_retention_hours * 3600)

        # Clean up each metrics buffer
        for buffer in [
            self.request_metrics,
            self.performance_metrics,
            self.cost_metrics,
            self.error_metrics,
            self.cache_metrics,
        ]:
            async with buffer._lock:
                # Remove old entries
                while buffer.data and buffer.data[0].get("timestamp", 0) < cutoff_time:
                    buffer.data.popleft()

    async def close(self) -> None:
        """Shutdown analytics collector gracefully"""
        logger.info("Shutting down analytics collector")

        # Signal shutdown
        self.shutdown_event.set()

        # Cancel background tasks
        if self.aggregation_task:
            self.aggregation_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        # Wait for tasks to complete
        if self.aggregation_task:
            try:
                await self.aggregation_task
            except asyncio.CancelledError:
                pass

        if self.cleanup_task:
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Analytics collector shutdown complete")
