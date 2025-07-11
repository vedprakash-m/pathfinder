"""
Unified Performance Monitoring and Observability System
Implements comprehensive monitoring patterns from Phase 3 of tech debt remediation plan.
"""

import asyncio
import functools
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import structlog

# Context variables for correlation tracking
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# ==================== MONITORING CONFIGURATION ====================


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class PerformanceThresholds:
    """Performance threshold configuration"""

    api_response_warning: float = 1.0  # seconds
    api_response_critical: float = 5.0  # seconds
    database_query_warning: float = 0.5  # seconds
    database_query_critical: float = 2.0  # seconds
    cache_operation_warning: float = 0.1  # seconds
    external_service_warning: float = 3.0  # seconds
    external_service_critical: float = 10.0  # seconds


@dataclass
class MetricPoint:
    """Individual metric data point"""

    name: str
    value: float
    type: MetricType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    correlation_id: Optional[str] = None


@dataclass
class OperationMetrics:
    """Comprehensive operation metrics"""

    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    correlation_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def finalize(self, success: bool = True, error: Optional[Exception] = None):
        """Finalize metrics calculation"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success

        if error:
            self.error_type = type(error).__name__
            self.error_message = str(error)


# ==================== STRUCTURED LOGGING ====================


class StructuredLogger:
    """Unified structured logging with correlation tracking"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.setup_logging()

    def setup_logging(self):
        """Configure structured logging"""
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="ISO"),
            self.add_correlation_context,
        ]

        # Add appropriate renderer based on environment
        if self.config.get("debug", False):
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            processors.append(structlog.processors.JSONRenderer())

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                logging.INFO if not self.config.get("debug") else logging.DEBUG
            ),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger()

    def add_correlation_context(self, logger, method_name, event_dict):
        """Add correlation context to log events"""
        event_dict["correlation_id"] = correlation_id.get()
        event_dict["request_id"] = request_id.get()
        event_dict["user_id"] = user_id.get()
        return event_dict

    def bind_correlation_id(self, corr_id: Optional[str] = None) -> str:
        """Bind correlation ID to context"""
        if not corr_id:
            corr_id = f"corr_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        correlation_id.set(corr_id)
        return corr_id

    def bind_request_context(self, req_id: str, user_id_val: Optional[str] = None):
        """Bind request context"""
        request_id.set(req_id)
        if user_id_val:
            user_id.set(user_id_val)

    def log_operation(
        self, operation: str, duration_ms: float, success: bool, **kwargs
    ):
        """Log operation with standardized format"""
        level = "info" if success else "error"

        log_data = {
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            **kwargs,
        }

        getattr(self.logger, level)("Operation completed", **log_data)

    def log_api_call(
        self, endpoint: str, method: str, status_code: int, duration_ms: float, **kwargs
    ):
        """Standardized API call logging"""
        self.logger.info(
            "API call",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            **kwargs,
        )

    def log_performance_alert(
        self, operation: str, duration_ms: float, threshold_ms: float, **kwargs
    ):
        """Log performance threshold breach"""
        self.logger.warning(
            "Performance threshold exceeded",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            threshold_ms=threshold_ms,
            **kwargs,
        )

    def log_error(self, error: Exception, operation: str, **kwargs):
        """Standardized error logging"""
        self.logger.error(
            "Operation failed",
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            **kwargs,
        )


# ==================== METRICS COLLECTOR ====================


class MetricsCollector:
    """Collect and aggregate application metrics"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/metrics")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metrics: List[MetricPoint] = []
        self.thresholds = PerformanceThresholds()
        self._lock = asyncio.Lock()

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None,
    ):
        """Record a metric point"""
        async with self._lock:
            metric = MetricPoint(
                name=name,
                value=value,
                type=metric_type,
                labels=labels or {},
                correlation_id=correlation_id.get(),
            )
            self.metrics.append(metric)

            # Periodic cleanup to prevent memory issues
            if len(self.metrics) > 10000:
                await self.flush_metrics()

    async def increment_counter(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric"""
        await self.record_metric(name, 1.0, MetricType.COUNTER, labels)

    async def record_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a gauge metric"""
        await self.record_metric(name, value, MetricType.GAUGE, labels)

    async def record_timer(
        self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None
    ):
        """Record a timer metric"""
        await self.record_metric(name, duration_ms, MetricType.TIMER, labels)

        # Check performance thresholds
        threshold = self._get_threshold_for_operation(name)
        if threshold and duration_ms > threshold * 1000:  # Convert to ms
            logger = StructuredLogger()
            logger.log_performance_alert(name, duration_ms, threshold * 1000)

    async def flush_metrics(self):
        """Flush metrics to storage"""
        if not self.metrics:
            return

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = self.storage_path / f"metrics_{timestamp}.jsonl"

        try:
            with open(file_path, "w") as f:
                for metric in self.metrics:
                    data = {
                        "name": metric.name,
                        "value": metric.value,
                        "type": metric.type.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "labels": metric.labels,
                        "correlation_id": metric.correlation_id,
                    }
                    f.write(json.dumps(data) + "\n")

            self.metrics.clear()

        except Exception as e:
            # Don't let metrics collection fail the application
            print(f"Failed to flush metrics: {e}")

    def _get_threshold_for_operation(self, operation_name: str) -> Optional[float]:
        """Get performance threshold for operation"""
        if "api" in operation_name.lower():
            return self.thresholds.api_response_warning
        elif "database" in operation_name.lower() or "query" in operation_name.lower():
            return self.thresholds.database_query_warning
        elif "cache" in operation_name.lower():
            return self.thresholds.cache_operation_warning
        elif "external" in operation_name.lower() or "http" in operation_name.lower():
            return self.thresholds.external_service_warning
        return None

    async def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for specified time period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff]

        if not recent_metrics:
            return {"error": "No metrics available for the specified period"}

        # Group by metric name
        by_name: Dict[str, List[MetricPoint]] = {}
        for metric in recent_metrics:
            if metric.name not in by_name:
                by_name[metric.name] = []
            by_name[metric.name].append(metric)

        summary = {}
        for name, metrics in by_name.items():
            values = [m.value for m in metrics]
            summary[name] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else None,
            }

        return summary


# ==================== PERFORMANCE MONITORING DECORATORS ====================


def monitor_performance(
    operation_name: str,
    threshold_ms: Optional[float] = None,
    record_metrics: bool = True,
):
    """Decorator for monitoring function performance"""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = OperationMetrics(
                operation_name=operation_name,
                start_time=time.time(),
                correlation_id=correlation_id.get(),
            )

            logger = StructuredLogger()
            collector = MetricsCollector()

            try:
                result = await func(*args, **kwargs)
                metrics.finalize(success=True)

                # Log operation
                logger.log_operation(
                    operation_name, metrics.duration_ms, True, **metrics.context
                )

                # Record metrics
                if record_metrics:
                    await collector.record_timer(
                        f"operation.{operation_name.replace(' ', '_').lower()}",
                        metrics.duration_ms,
                    )

                # Check custom threshold
                if threshold_ms and metrics.duration_ms > threshold_ms:
                    logger.log_performance_alert(
                        operation_name, metrics.duration_ms, threshold_ms
                    )

                return result

            except Exception as e:
                metrics.finalize(success=False, error=e)

                # Log error
                logger.log_error(e, operation_name, **metrics.context)

                # Record error metric
                if record_metrics:
                    await collector.increment_counter(
                        f"error.{operation_name.replace(' ', '_').lower()}",
                        {"error_type": type(e).__name__},
                    )

                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, convert to async context
            return asyncio.create_task(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def monitor_api_endpoint(endpoint_name: str):
    """Specialized decorator for API endpoint monitoring"""
    return monitor_performance(
        f"API {endpoint_name}",
        threshold_ms=1000,  # 1 second warning threshold
        record_metrics=True,
    )


def monitor_database_operation(operation_name: str):
    """Specialized decorator for database operation monitoring"""
    return monitor_performance(
        f"Database {operation_name}",
        threshold_ms=500,  # 500ms warning threshold
        record_metrics=True,
    )


def monitor_external_service(service_name: str):
    """Specialized decorator for external service monitoring"""
    return monitor_performance(
        f"External {service_name}",
        threshold_ms=3000,  # 3 second warning threshold
        record_metrics=True,
    )


# ==================== CONTEXT MANAGERS ====================


@asynccontextmanager
async def monitoring_context(
    operation_name: str, **context
) -> AsyncGenerator[OperationMetrics, None]:
    """Context manager for monitoring code blocks"""
    metrics = OperationMetrics(
        operation_name=operation_name,
        start_time=time.time(),
        correlation_id=correlation_id.get(),
        context=context,
    )

    logger = StructuredLogger()
    collector = MetricsCollector()

    try:
        yield metrics
        metrics.finalize(success=True)

        # Log successful operation
        logger.log_operation(
            operation_name, metrics.duration_ms, True, **metrics.context
        )

        # Record metrics
        await collector.record_timer(
            f"block.{operation_name.replace(' ', '_').lower()}", metrics.duration_ms
        )

    except Exception as e:
        metrics.finalize(success=False, error=e)

        # Log error
        logger.log_error(e, operation_name, **metrics.context)

        # Record error metric
        await collector.increment_counter(
            f"error.block.{operation_name.replace(' ', '_').lower()}",
            {"error_type": type(e).__name__},
        )

        raise


# ==================== HEALTH CHECK SYSTEM ====================


class HealthChecker:
    """System health monitoring and reporting"""

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func

    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {"status": "error", "message": f"Check '{name}' not found"}

        start_time = time.time()
        try:
            result = await self.checks[name]()
            duration_ms = (time.time() - start_time) * 1000

            check_result = {
                "status": "healthy",
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "details": result if isinstance(result, dict) else {"value": result},
            }

            self.last_results[name] = check_result
            return check_result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            check_result = {
                "status": "unhealthy",
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
            }

            self.last_results[name] = check_result
            return check_result

    async def run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all registered health checks"""
        results = {}

        # Run checks concurrently
        tasks = [self.run_check(name) for name in self.checks.keys()]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(self.checks.keys(), check_results, strict=False):
            if isinstance(result, Exception):
                results[name] = {
                    "status": "error",
                    "error": str(result),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                results[name] = result

        return results

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        if not self.last_results:
            return {"status": "unknown", "message": "No health checks run yet"}

        healthy_count = sum(
            1 for r in self.last_results.values() if r.get("status") == "healthy"
        )
        total_count = len(self.last_results)

        if healthy_count == total_count:
            status = "healthy"
        elif healthy_count > 0:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "healthy_checks": healthy_count,
            "total_checks": total_count,
            "last_updated": max(
                (r.get("timestamp", "") for r in self.last_results.values()), default=""
            ),
        }


# ==================== GLOBAL INSTANCES ====================

# Create global instances for easy access
logger = StructuredLogger()
metrics_collector = MetricsCollector()
health_checker = HealthChecker()

# ==================== USAGE EXAMPLES ====================

# Example usage patterns:

# 1. Function decoration
# @monitor_performance("User Authentication")
# async def authenticate_user(credentials):
#     # function implementation
#     pass

# 2. Context manager
# async def some_operation():
#     async with monitoring_context("Complex Operation", user_id=123) as metrics:
#         # Add custom context
#         metrics.context["step"] = "validation"
#         # Do work here
#         pass

# 3. Manual correlation tracking
# def request_handler(request):
#     corr_id = logger.bind_correlation_id()
#     logger.bind_request_context(request.id, request.user_id)
#     # Handle request
#     pass

# 4. Health check registration
# async def database_health():
#     # Check database connectivity
#     return {"connection": "ok", "latency_ms": 15}
#
# health_checker.register_check("database", database_health)
