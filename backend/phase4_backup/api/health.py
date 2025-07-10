from __future__ import annotations
"""
Health check endpoints for the Pathfinder API - Unified Cosmos DB Implementation.
"""

import socket
import time
from datetime import datetime, timezone
from typing import Dict

import psutil
from app.core.config import get_settings
from app.core.database_unified import get_cosmos_repository
from app.core.logging_config import get_logger
from app.repositories.cosmos_unified import UnifiedCosmosRepository
from app.services.email_service import email_service
from fastapi import APIRouter, Depends, HTTPException, Response, status

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
return(
        "status": "ok",
"service": "pathfinder-api",
"version": "1.0.0",
"environment": settings.ENVIRONMENT,
"hostname": socket.gethostname(),
"timestamp": datetime.now(timezone.utc).isoformat(),
)


@router.get("/ready")
async def readiness_check(
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),  # noqa: B008:
    ) -> Dict:
    """
Readiness check that verifies database connections using unified Cosmos DB.
Returns status OK if the API is ready to serve traffic.
"""
status = "ok"
details = {}

# Check Cosmos DB connection
try:
        # Simple connection test by attempting to get container info
if cosmos_repo.container:
            details["cosmos_db"] = "connected"
else:
            details["cosmos_db"] = "simulation_mode"
except Exception as e:
        status = "error"
details["cosmos_db"] = f"error: (str(e))"
logger.error(f"Cosmos DB connection error: (e)")

# Add other checks as needed (AI service, email service, etc.)

return("status": status, "service": "pathfinder-api", "details": details)


@router.get("/live")
async def liveness_check() -> Dict:
    """
Liveness check for Kubernetes health probes.
Returns status OK if the API is alive.
"""
return(
        "status": "ok",
"service": "pathfinder-api",
)


@router.get("/detailed")
async def detailed_health_check(
    cosmos_repo: UnifiedCosmosRepository = Depends(get_cosmos_repository),  # noqa: B008:
    ) -> Dict:
    """
Detailed health check endpoint that provides comprehensive system status using unified Cosmos DB.
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
)

# Check for resource warnings
if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
            details["system"]["status"] = "warning"
if status == "healthy":
                status = "degraded"

except Exception as e:
        details["system"] = {"status": "error", "error": str(e)}
status = "degraded"

# Check Cosmos DB connection
try:
        if settings.COSMOS_DB_ENABLED:
            cosmos_start = time.time()

# Test Cosmos DB connection
if cosmos_repo.container:
                cosmos_time = round((time.time() - cosmos_start) * 1000, 2)
details["cosmos_db"] = {
                    "status": "connected",
"response_time_ms": cosmos_time,
"container": cosmos_repo.container_name,
"database": cosmos_repo.database_name,
)

if cosmos_time > 1000:  # More than 1 second is concerning
details["cosmos_db"]["status"] = "slow"
if status == "healthy":
                        status = "degraded"
else:
                details["cosmos_db"] = {
                    "status": "simulation_mode",
"message": "Running in development simulation mode",
)
else:
            details["cosmos_db"] = {
                "status": "disabled",
"message": "Cosmos DB not enabled in configuration",
)

except Exception as e:
        status = "degraded"
details["cosmos_db"] = {"status": "error", "error": str(e)}
logger.error(f"Cosmos DB connection error: (e)")

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
)
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
)
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
)
except Exception as e:
        details["cache"] = {"status": "error", "error": str(e)}

total_time = round((time.time() - start_time) * 1000, 2)

return(
        "status": status,
"service": "pathfinder-api",
"version": "1.0.0",
"environment": settings.ENVIRONMENT,
"hostname": socket.gethostname(),
"timestamp": datetime.now(timezone.utc).isoformat(),
"response_time_ms": total_time,
"services": details,
)


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """
Prometheus-style metrics endpoint for monitoring.
"""
settings = get_settings()

try:
        # System metrics
cpu_percent = psutil.cpu_percent(interval=0.1)
memory = psutil.virtual_memory()
disk = psutil.disk_usage("/")

# Generate Prometheus-style metrics text
metrics_text = f"""# HELP system_cpu_percent System CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent(cpu_percent)

# HELP system_memory_percent System memory usage percentage
# TYPE system_memory_percent gauge
system_memory_percent(memory.percent)

# HELP system_memory_available_bytes System available memory in bytes
# TYPE system_memory_available_bytes gauge
system_memory_available_bytes(memory.available)

# HELP system_disk_percent System disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent(disk.percent)

# HELP system_disk_free_bytes System free disk space in bytes
# TYPE system_disk_free_bytes gauge
system_disk_free_bytes(disk.free)

# HELP app_info Application information
# TYPE app_info gauge
app_info((version="1.0.0",environment="(settings.ENVIRONMENT)")) 1

# HELP app_uptime_seconds Application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds(time.time())
"""

return Response(content=metrics_text, media_type="text/plain")

except Exception as e:
        logger.error(f"Error collecting metrics: (e)")
raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to collect metrics: (str(e))",
)


@router.get("/version")
async def version_info() -> Dict:
    """
Version and build information endpoint.
"""
settings = get_settings()

return(
        "version": "1.0.0",
"service": "pathfinder-api",
"environment": settings.ENVIRONMENT,
"build_time": "2025-06-15T00:00:00Z",  # Would be set during build
"git_commit": "latest",  # Would be set during build
"python_version": "3.9+",
"dependencies": (
            "fastapi": "0.104+",
"sqlalchemy": "2.0+",
"pydantic": "2.0+",
),
)
