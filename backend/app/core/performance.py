"""
Performance monitoring for backend services.

This module provides:
- Request timing metrics
- Database query timing
- API endpoint performance tracking
- Memory usage monitoring
- CPU usage monitoring
"""

import asyncio
import functools
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import psutil
from app.core.cache import cache
from app.core.config import get_settings
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)

# Global performance metrics store
_metrics_store = {
    "endpoint_response_times": {},  # Endpoint -> list of response times
    "database_query_times": {},  # Query name -> list of execution times
    "api_request_counts": {},  # Endpoint -> count
    "slowest_queries": [],  # List of (name, time, query) tuples
    "memory_usage_samples": [],  # List of (timestamp, usage) tuples
    "last_metrics_rollup": datetime.now(),
}


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate response time
        duration = time.time() - start_time

        # Get the route path for more stable metrics
        route_path = request.scope.get("path", "unknown")
        if route_path != "unknown":
            # Handle API endpoints specifically
            if route_path.startswith("/api/"):
                # Track endpoint response time
                if route_path not in _metrics_store["endpoint_response_times"]:
                    _metrics_store["endpoint_response_times"][route_path] = []

                _metrics_store["endpoint_response_times"][route_path].append(duration)

                # Track request counts
                _metrics_store["api_request_counts"][route_path] = (
                    _metrics_store["api_request_counts"].get(route_path, 0) + 1
                )

                # Add Server-Timing header in response
                response.headers["Server-Timing"] = f"total;dur={duration * 1000:.2f}"

                # Log slow requests
                if duration > settings.SLOW_REQUEST_THRESHOLD:
                    logger.warning(
                        f"Slow request to {route_path}: {duration:.4f}s "
                        f"(method={request.method}, status_code={response.status_code})"
                    )

            # Periodically roll up metrics
            await _maybe_rollup_metrics()

        return response


class DatabasePerformanceMonitor:
    """Monitor database query performance."""

    @staticmethod
    @contextmanager
    def measure_query(query_name: str, query_text: Optional[str] = None):
        """Measure the execution time of a database query."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time

            # Store the metrics
            if query_name not in _metrics_store["database_query_times"]:
                _metrics_store["database_query_times"][query_name] = []

            _metrics_store["database_query_times"][query_name].append(duration)

            # Track slow queries
            if duration > settings.SLOW_QUERY_THRESHOLD:
                logger.warning(f"Slow query {query_name}: {duration:.4f}s")

                # Add to slowest queries
                _metrics_store["slowest_queries"].append(
                    (query_name, duration, query_text or "Query text not provided")
                )

                # Keep only the top N slowest queries
                _metrics_store["slowest_queries"] = sorted(
                    _metrics_store["slowest_queries"], key=lambda x: x[1], reverse=True
                )[:50]


def track_execution_time(func_name: Optional[str] = None):
    """Decorator to track function execution time."""

    def decorator(func):
        nonlocal func_name
        if func_name is None:
            func_name = func.__qualname__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            # Store the metrics
            metric_name = f"function.{func_name}"
            if metric_name not in _metrics_store["endpoint_response_times"]:
                _metrics_store["endpoint_response_times"][metric_name] = []

            _metrics_store["endpoint_response_times"][metric_name].append(duration)

            # Log slow function execution
            if duration > settings.SLOW_FUNCTION_THRESHOLD:
                logger.warning(f"Slow function {func_name}: {duration:.4f}s")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            # Store the metrics
            metric_name = f"function.{func_name}"
            if metric_name not in _metrics_store["endpoint_response_times"]:
                _metrics_store["endpoint_response_times"][metric_name] = []

            _metrics_store["endpoint_response_times"][metric_name].append(duration)

            # Log slow function execution
            if duration > settings.SLOW_FUNCTION_THRESHOLD:
                logger.warning(f"Slow function {func_name}: {duration:.4f}s")

            return result

        # Choose the appropriate wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    if callable(func_name):
        # Called without arguments
        func = func_name
        func_name = func.__qualname__
        return decorator(func)

    # Called with arguments
    return decorator


async def _maybe_rollup_metrics():
    """Periodically roll up metrics to prevent memory bloat."""
    now = datetime.now()
    if (
        now - _metrics_store["last_metrics_rollup"]
    ).total_seconds() > settings.METRICS_ROLLUP_INTERVAL:
        await _rollup_metrics()
        _metrics_store["last_metrics_rollup"] = now


async def _rollup_metrics():
    """Roll up performance metrics to save memory."""
    # Get current memory usage
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / 1024 / 1024  # MB

    # Add memory usage sample
    _metrics_store["memory_usage_samples"].append((datetime.now(), memory_usage))

    # Trim memory samples (keep last 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    _metrics_store["memory_usage_samples"] = [
        sample
        for sample in _metrics_store["memory_usage_samples"]
        if sample[0] >= cutoff
    ]

    # Compute average endpoint times and reset
    endpoint_averages = {}
    for endpoint, times in _metrics_store["endpoint_response_times"].items():
        if times:
            endpoint_averages[endpoint] = sum(times) / len(times)

    # Compute average query times
    query_averages = {}
    for query, times in _metrics_store["database_query_times"].items():
        if times:
            query_averages[query] = sum(times) / len(times)

    # Cache the rolled up metrics
    metrics_snapshot = {
        "timestamp": datetime.now().isoformat(),
        "endpoint_average_times": endpoint_averages,
        "query_average_times": query_averages,
        "api_request_counts": _metrics_store["api_request_counts"].copy(),
        "slowest_queries": _metrics_store["slowest_queries"][:10],
        "memory_usage": memory_usage,
        "cpu_percent": psutil.cpu_percent(interval=0.1),
    }

    # Save to cache
    await cache.set("performance_metrics_latest", metrics_snapshot)

    # Reset metrics to prevent memory growth
    for endpoint in _metrics_store["endpoint_response_times"]:
        _metrics_store["endpoint_response_times"][endpoint] = []

    for query in _metrics_store["database_query_times"]:
        _metrics_store["database_query_times"][query] = []


async def get_performance_metrics() -> Dict[str, Any]:
    """Get the current performance metrics."""
    # Ensure metrics are up to date
    await _rollup_metrics()

    # Return the latest metrics from cache
    metrics = await cache.get("performance_metrics_latest")
    if not metrics:
        return {
            "timestamp": datetime.now().isoformat(),
            "endpoint_average_times": {},
            "query_average_times": {},
            "api_request_counts": {},
            "slowest_queries": [],
            "memory_usage": 0,
            "cpu_percent": 0,
        }

    return metrics


async def get_performance_history() -> List[Dict[str, Any]]:
    """Get historical performance metrics."""
    # Get from cache
    history = await cache.get("performance_metrics_history")
    if not history:
        return []

    return history


def optimize_query(async_session: AsyncSession, query: str, params: Dict = None) -> str:
    """
    Analyze and optimize a SQL query.

    This is a placeholder for more complex query optimization.
    In a real implementation, this would analyze the query execution plan
    and suggest optimizations.
    """
    # Simple optimization rules (would be more sophisticated in production)
    optimized = query

    # Check for missing indexes on WHERE clauses
    if "WHERE" in query and "CREATE INDEX" not in query:
        # This is just a placeholder for real index analysis
        logger.info("Query might benefit from index analysis")

    # Check for SELECT *
    if "SELECT *" in query:
        logger.info("Consider replacing 'SELECT *' with specific columns")

    # Check for missing LIMIT
    if "LIMIT" not in query and "DELETE" not in query and "UPDATE" not in query:
        logger.info("Consider adding LIMIT clause to query")

    # Check for JOIN without conditions
    if "JOIN" in query and "ON" not in query:
        logger.warning("JOIN without ON conditions detected")

    return optimized


# Add performance monitoring settings to config.py
# Add these to the Settings class
# SLOW_REQUEST_THRESHOLD: float = Field(default=1.0, env="SLOW_REQUEST_THRESHOLD")
# SLOW_QUERY_THRESHOLD: float = Field(default=0.5, env="SLOW_QUERY_THRESHOLD")
# SLOW_FUNCTION_THRESHOLD: float = Field(default=0.5, env="SLOW_FUNCTION_THRESHOLD")
# METRICS_ROLLUP_INTERVAL: int = Field(default=300, env="METRICS_ROLLUP_INTERVAL")
