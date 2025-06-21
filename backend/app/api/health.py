"""
Health check endpoints for the Pathfinder API.
"""

import socket
import time
from datetime import datetime, timezone
from typing import Dict, Optional

import psutil
from app.core.config import get_settings
from app.core.cosmos_db import get_cosmos_client
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.services.email_service import email_service
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/health",
    tags=["health"],
)

logger = get_logger(__name__)


@router.get("/")
async def health_check() -> Dict:
    """
    Basic health check endpoint.
    Returns status OK if the API is running.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "service": "pathfinder-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db), cosmos_client=Depends(get_cosmos_client)
) -> Dict:
    """
    Readiness check that verifies database connections.
    Returns status OK if the API is ready to serve traffic.
    """
    status = "ok"
    details = {}

    # Check SQL database connection
    try:
        result = await db.execute("SELECT 1")
        details["database"] = "connected"
    except Exception as e:
        status = "error"
        details["database"] = f"error: {str(e)}"
        logger.error(f"Database connection error: {e}")

    # Check Cosmos DB connection
    try:
        cosmos_databases = list(cosmos_client.list_databases())
        details["cosmos_db"] = "connected"
    except Exception as e:
        status = "error"
        details["cosmos_db"] = f"error: {str(e)}"
        logger.error(f"Cosmos DB connection error: {e}")

    # Add other checks as needed (Redis, AI service, etc.)

    return {"status": status, "service": "pathfinder-api", "details": details}


@router.get("/live")
async def liveness_check() -> Dict:
    """
    Liveness check for Kubernetes health probes.
    Returns status OK if the API is alive.
    """
    return {
        "status": "ok",
        "service": "pathfinder-api",
    }


@router.get("/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db), cosmos_client=Depends(get_cosmos_client)
) -> Dict:
    """
    Detailed health check endpoint that provides comprehensive system status.
    """
    settings = get_settings()
    start_time = time.time()
    status = "healthy"
    details = {}

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        details["system"] = {
            "status": "healthy",
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": round(disk.percent, 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
        }

        # Check for resource warnings
        if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
            details["system"]["status"] = "warning"
            if status == "healthy":
                status = "degraded"

    except Exception as e:
        details["system"] = {"status": "error", "error": str(e)}
        status = "degraded"

    # Check SQL database connection
    try:
        db_start = time.time()
        result = await db.execute("SELECT 1")
        db_time = round((time.time() - db_start) * 1000, 2)

        details["database"] = {
            "status": "connected",
            "type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
            "response_time_ms": db_time,
            "url_type": (
                settings.DATABASE_URL.split("://")[0]
                if "://" in settings.DATABASE_URL
                else "unknown"
            ),
        }

        if db_time > 1000:  # More than 1 second is concerning
            details["database"]["status"] = "slow"
            if status == "healthy":
                status = "degraded"

    except Exception as e:
        status = "degraded"
        details["database"] = {"status": "error", "error": str(e)}
        logger.error(f"Database connection error: {e}")

    # Check Cosmos DB connection
    try:
        if settings.COSMOS_DB_ENABLED:
            cosmos_start = time.time()
            cosmos_databases = list(cosmos_client.list_databases())
            cosmos_time = round((time.time() - cosmos_start) * 1000, 2)

            details["cosmos_db"] = {
                "status": "connected",
                "type": "azure_cosmos",
                "database_count": len(cosmos_databases),
                "response_time_ms": cosmos_time,
            }
        else:
            details["cosmos_db"] = {"status": "disabled", "type": "azure_cosmos"}
    except Exception as e:
        if settings.COSMOS_DB_ENABLED:
            status = "degraded"
            details["cosmos_db"] = {"status": "error", "error": str(e)}
            logger.error(f"Cosmos DB connection error: {e}")
        else:
            details["cosmos_db"] = {"status": "disabled", "type": "azure_cosmos"}

    # Check email service
    try:
        email_status = (
            "configured"
            if (email_service.sendgrid_client or email_service.smtp_config)
            else "not_configured"
        )
        email_type = (
            "sendgrid"
            if email_service.sendgrid_client
            else ("smtp" if email_service.smtp_config else "none")
        )

        details["email_service"] = {
            "status": email_status,
            "type": email_type,
            "templates_loaded": bool(email_service.template_env),
        }
    except Exception as e:
        details["email_service"] = {"status": "error", "error": str(e)}

    # Check AI service availability
    try:
        ai_status = "configured" if settings.OPENAI_API_KEY else "not_configured"
        details["ai_service"] = {
            "status": ai_status,
            "type": "openai",
            "llm_orchestration_enabled": settings.LLM_ORCHESTRATION_ENABLED,
            "cost_tracking_enabled": settings.AI_COST_TRACKING_ENABLED,
        }
    except Exception as e:
        details["ai_service"] = {"status": "error", "error": str(e)}

    # Check cache service
    try:
        cache_type = "redis" if settings.USE_REDIS_CACHE else "memory"
        details["cache"] = {
            "status": "enabled" if settings.CACHE_ENABLED else "disabled",
            "type": cache_type,
            "ttl": settings.CACHE_TTL,
            "max_size": settings.CACHE_MAX_SIZE,
        }
    except Exception as e:
        details["cache"] = {"status": "error", "error": str(e)}

    total_time = round((time.time() - start_time) * 1000, 2)

    return {
        "status": status,
        "service": "pathfinder-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "response_time_ms": total_time,
        "details": details,
    }


@router.get("/metrics")
async def metrics_endpoint() -> Dict:
    """
    Prometheus-style metrics endpoint for monitoring.
    """
    settings = get_settings()

    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Application metrics (placeholder - would be collected from actual usage)
        metrics = {
            "system_cpu_percent": cpu_percent,
            "system_memory_percent": memory.percent,
            "system_memory_available_bytes": memory.available,
            "system_disk_percent": disk.percent,
            "system_disk_free_bytes": disk.free,
            "app_version": "1.0.0",
            "app_environment": settings.ENVIRONMENT,
            "app_uptime_seconds": time.time(),  # Placeholder - should track actual uptime
            "database_connections_active": 1,  # Placeholder
            "http_requests_total": 0,  # Placeholder
            "http_request_duration_seconds": 0.0,  # Placeholder
            "ai_requests_total": 0,  # Placeholder
            "ai_cost_total_usd": 0.0,  # Placeholder
            "email_notifications_sent_total": 0,  # Placeholder
            "active_trips_count": 0,  # Placeholder
            "active_families_count": 0,  # Placeholder
        }

        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}",
        )


@router.get("/version")
async def version_info() -> Dict:
    """
    Version and build information endpoint.
    """
    settings = get_settings()

    return {
        "version": "1.0.0",
        "service": "pathfinder-api",
        "environment": settings.ENVIRONMENT,
        "build_timestamp": "2025-06-15T00:00:00Z",  # Would be set during build
        "git_commit": "latest",  # Would be set during build
        "python_version": "3.9+",
        "dependencies": {
            "fastapi": "0.104+",
            "sqlalchemy": "2.0+",
            "pydantic": "2.0+",
        },
    }
