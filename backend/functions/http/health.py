"""
Health Check HTTP Function

Provides health endpoints for Azure Functions monitoring.
"""

from datetime import UTC, datetime

import azure.functions as func

from core.config import get_settings
from repositories.cosmos_repository import cosmos_repo
from services.llm.client import llm_client

bp = func.Blueprint()


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


@bp.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Basic health check endpoint.

    Returns 200 if the function app is running.
    """
    return func.HttpResponse(
        body='{"status": "healthy", "service": "pathfinder-api"}', status_code=200, mimetype="application/json"
    )


@bp.route(route="health/ready", methods=["GET"])
async def readiness_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Readiness check - verifies all dependencies are available.

    Checks:
    - Cosmos DB connectivity
    - OpenAI API availability
    - Configuration loaded
    """
    checks = {"timestamp": utc_now().isoformat(), "status": "healthy", "checks": {}}

    all_healthy = True

    # Check configuration
    try:
        get_settings()
        checks["checks"]["config"] = {"status": "healthy", "details": "Configuration loaded"}
    except Exception as e:
        checks["checks"]["config"] = {"status": "unhealthy", "details": str(e)}
        all_healthy = False

    # Check Cosmos DB
    try:
        # Simple query to verify connectivity using singleton
        await cosmos_repo.count("SELECT VALUE COUNT(1) FROM c WHERE c.id = 'health-check'")
        checks["checks"]["cosmos_db"] = {"status": "healthy", "details": "Connected to Cosmos DB"}
    except Exception as e:
        checks["checks"]["cosmos_db"] = {"status": "unhealthy", "details": str(e)}
        all_healthy = False

    # Check OpenAI
    try:
        is_healthy = await llm_client.check_health()
        if is_healthy:
            checks["checks"]["openai"] = {"status": "healthy", "details": "OpenAI API accessible"}
        else:
            checks["checks"]["openai"] = {"status": "unhealthy", "details": "OpenAI API check failed"}
            all_healthy = False
    except Exception as e:
        checks["checks"]["openai"] = {"status": "unhealthy", "details": str(e)}
        all_healthy = False

    # Set overall status
    checks["status"] = "healthy" if all_healthy else "unhealthy"

    import json

    return func.HttpResponse(
        body=json.dumps(checks), status_code=200 if all_healthy else 503, mimetype="application/json"
    )


@bp.route(route="health/live", methods=["GET"])
async def liveness_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Liveness check - basic check that the process is alive.

    Used by Azure to determine if the container should be restarted.
    """
    return func.HttpResponse(body='{"status": "alive"}', status_code=200, mimetype="application/json")
