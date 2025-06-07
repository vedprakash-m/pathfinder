"""
Health check endpoints for the Pathfinder API.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import socket

from app.core.database import get_db
from app.core.cosmos_db import get_cosmos_client
from app.core.logging_config import get_logger

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
    return {
        "status": "ok",
        "service": "pathfinder-api",
        "hostname": socket.gethostname(),
    }


@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    cosmos_client = Depends(get_cosmos_client)
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
    
    return {
        "status": status,
        "service": "pathfinder-api",
        "details": details
    }


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
    db: AsyncSession = Depends(get_db),
    cosmos_client = Depends(get_cosmos_client)
) -> Dict:
    """
    Detailed health check endpoint that provides comprehensive system status.
    """
    status = "ok"
    details = {
        "database": {"status": "unknown"},
        "cosmos_db": {"status": "unknown"},
        "cache": {"status": "unknown"},
        "ai_service": {"status": "unknown"}
    }
    
    # Check SQL database connection
    try:
        result = await db.execute("SELECT 1")
        details["database"] = {"status": "connected", "type": "azure_sql"}
    except Exception as e:
        status = "degraded"
        details["database"] = {"status": "error", "error": str(e)}
        logger.error(f"Database connection error: {e}")
    
    # Check Cosmos DB connection
    try:
        cosmos_databases = list(cosmos_client.list_databases())
        details["cosmos_db"] = {"status": "connected", "type": "azure_cosmos"}
    except Exception as e:
        status = "degraded"
        details["cosmos_db"] = {"status": "error", "error": str(e)}
        logger.error(f"Cosmos DB connection error: {e}")
    
    # Check Redis cache
    try:
        # For now, just mark as unknown since Redis is optional in tests
        details["cache"] = {"status": "unknown", "type": "redis"}
    except Exception as e:
        details["cache"] = {"status": "error", "error": str(e)}
    
    # Check AI service availability
    try:
        # For now, just mark as available
        details["ai_service"] = {"status": "available", "type": "llm_orchestration"}
    except Exception as e:
        details["ai_service"] = {"status": "error", "error": str(e)}
    
    return {
        "status": status,
        "service": "pathfinder-api",
        "timestamp": "2025-01-01T00:00:00Z",  # TODO: Use actual timestamp
        "details": details
    }
