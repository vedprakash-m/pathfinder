"""
FastAPI Application - Main entry point for the LLM Orchestration service
Provides REST API endpoints for LLM requests and system management
"""
import asyncio
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.types import (
    LLMRequest, LLMResponse, TenantInfo, LLMProvider,
    LLMOrchestrationError, LLMBudgetExceededError, LLMRateLimitError
)
from core.gateway import LLMGateway
from services.config_manager import AdminConfigManager
from services.routing_engine import RoutingEngine
from services.budget_manager import BudgetManager
from services.cache_manager import CacheManager
from services.circuit_breaker import CircuitBreakerManager
from services.usage_logger import UsageLogger
from services.cost_estimator import CostEstimator
from services.analytics_collector import AnalyticsCollector
from services.key_vault import AzureKeyVaultProvider

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global gateway instance
gateway: Optional[LLMGateway] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global gateway
    
    try:
        logger.info("Starting LLM Orchestration service")
        
        # Initialize all components
        gateway = await initialize_gateway()
        
        logger.info("LLM Orchestration service started successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start LLM Orchestration service", error=str(e))
        raise
    finally:
        # Cleanup
        if gateway:
            await gateway.shutdown()
        logger.info("LLM Orchestration service stopped")


# FastAPI application
app = FastAPI(
    title="LLM Orchestration Service",
    description="Enterprise-grade LLM orchestration with intelligent routing, budget management, and analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)


# Request/Response Models
class ProcessLLMRequest(BaseModel):
    """API request model for processing LLM requests"""
    request: LLMRequest
    tenant_id: str


class ProcessLLMResponse(BaseModel):
    """API response model for LLM processing"""
    success: bool
    response: Optional[LLMResponse] = None
    error: Optional[str] = None
    processing_time: float
    cost: float


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: str
    version: str
    components: Dict[str, Any]


async def initialize_gateway() -> LLMGateway:
    """Initialize the LLM Gateway with all required services"""
    
    # Load configuration  
    config_manager = AdminConfigManager(
        config_path="/Users/vedprakashmishra/pathfinder/llm_orchestration/config/admin_config.yaml"
    )
    await config_manager.load_config()
    
    # Initialize Key Vault
    key_vault = AzureKeyVaultProvider(vault_name="llm-orchestration-vault")
    
    # Initialize routing engine
    routing_engine = RoutingEngine(
        config_manager=config_manager,
        providers=[LLMProvider.OPENAI, LLMProvider.GEMINI, LLMProvider.ANTHROPIC]
    )
    
    # Initialize budget manager with basic config
    budget_config = await config_manager.get_budget_config()
    budget_manager = BudgetManager(
        config=budget_config,
        alert_webhook_url="https://alerts.example.com/webhook"
    )
    
    # Initialize cache manager
    cache_manager = CacheManager(
        redis_url="redis://localhost:6379",
        default_ttl=3600
    )
    await cache_manager.connect()
    
    # Initialize circuit breaker manager with basic config
    performance_config = await config_manager.get_performance_config()
    circuit_breaker = CircuitBreakerManager(performance_config.get("circuit_breaker", {}))
    
    # Initialize usage logger
    usage_logger = UsageLogger(
        storage_backend="file",
        log_file_path="/tmp/llm_usage.log"
    )
    await usage_logger.start()
    
    # Initialize cost estimator
    pricing_config = config_manager.get_pricing_config()
    cost_estimator = CostEstimator(pricing_config)
    
    # Initialize analytics collector
    analytics_collector = AnalyticsCollector()
    await analytics_collector.start()
    
    # Create and return gateway
    return LLMGateway(
        config_manager=config_manager,
        routing_engine=routing_engine,
        budget_manager=budget_manager,
        cache_manager=cache_manager,
        circuit_breaker=circuit_breaker,
        usage_logger=usage_logger,
        cost_estimator=cost_estimator,
        analytics_collector=analytics_collector
    )


async def get_tenant_info(tenant_id: str) -> TenantInfo:
    """
    Retrieve tenant information
    In production, this would query a database
    """
    # Mock tenant data for now
    return TenantInfo(
        tenant_id=tenant_id,
        is_active=True,
        subscription_tier="premium",
        daily_budget_limit=100.0,
        monthly_budget_limit=3000.0,
        rate_limit_requests_per_minute=100,
        allowed_providers=[LLMProvider.OPENAI, LLMProvider.GEMINI],
        custom_settings={}
    )


@app.post("/api/v1/llm/process", response_model=ProcessLLMResponse)
async def process_llm_request(
    request_data: ProcessLLMRequest,
    background_tasks: BackgroundTasks
) -> ProcessLLMResponse:
    """
    Process an LLM request through the orchestration layer
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Received LLM request",
            request_id=request_data.request.request_id,
            tenant_id=request_data.tenant_id,
            task_type=request_data.request.task_type.value
        )
        
        # Get tenant information
        tenant_info = await get_tenant_info(request_data.tenant_id)
        
        # Process request through gateway
        response = await gateway.process_request(
            request=request_data.request,
            tenant_info=tenant_info
        )
        
        processing_time = time.time() - start_time
        
        # Calculate cost (this is also done internally but we return it to the client)
        cost = await gateway.cost_estimator.calculate_actual_cost(
            request_data.request, response
        )
        
        logger.info(
            "LLM request processed successfully",
            request_id=request_data.request.request_id,
            processing_time=processing_time,
            cost=cost
        )
        
        return ProcessLLMResponse(
            success=True,
            response=response,
            processing_time=processing_time,
            cost=cost
        )
        
    except LLMBudgetExceededError as e:
        processing_time = time.time() - start_time
        logger.warning("Budget exceeded", request_id=request_data.request.request_id, error=str(e))
        raise HTTPException(status_code=402, detail=str(e))
        
    except LLMRateLimitError as e:
        processing_time = time.time() - start_time
        logger.warning("Rate limit exceeded", request_id=request_data.request.request_id, error=str(e))
        raise HTTPException(status_code=429, detail=str(e))
        
    except LLMOrchestrationError as e:
        processing_time = time.time() - start_time
        logger.error("Gateway error", request_id=request_data.request.request_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error("Unexpected error", request_id=request_data.request.request_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint
    """
    try:
        components = await gateway.get_system_health() if gateway else {}
        
        return HealthResponse(
            status="healthy",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            version="1.0.0",
            components=components
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            version="1.0.0",
            components={"error": str(e)}
        )


@app.get("/api/v1/metrics/real-time")
async def get_real_time_metrics() -> Dict[str, Any]:
    """
    Get real-time system metrics
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        metrics = await gateway.analytics_collector.get_real_time_metrics()
        return metrics
        
    except Exception as e:
        logger.error("Failed to get real-time metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@app.get("/api/v1/analytics/tenant/{tenant_id}")
async def get_tenant_analytics(
    tenant_id: str,
    hours: int = 24
) -> Dict[str, Any]:
    """
    Get analytics for a specific tenant
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        analytics = await gateway.analytics_collector.get_tenant_analytics(
            tenant_id=tenant_id,
            hours=hours
        )
        return analytics
        
    except Exception as e:
        logger.error("Failed to get tenant analytics", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/api/v1/analytics/system")
async def get_system_analytics(hours: int = 24) -> Dict[str, Any]:
    """
    Get system-wide analytics
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        analytics = await gateway.analytics_collector.get_system_analytics(hours=hours)
        return analytics
        
    except Exception as e:
        logger.error("Failed to get system analytics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/api/v1/budget/status/{tenant_id}")
async def get_budget_status(tenant_id: str) -> Dict[str, Any]:
    """
    Get budget status for a tenant
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        status = await gateway.budget_manager.get_budget_status(tenant_id)
        return status
        
    except Exception as e:
        logger.error("Failed to get budget status", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve budget status")


@app.post("/api/v1/admin/circuit-breaker/{provider}/force-open")
async def force_open_circuit_breaker(provider: str) -> Dict[str, str]:
    """
    Force open a circuit breaker for maintenance
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        provider_type = LLMProvider(provider)
        await gateway.circuit_breaker.force_open(provider_type)
        
        return {"status": "success", "message": f"Circuit breaker opened for {provider}"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        logger.error("Failed to open circuit breaker", provider=provider, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to open circuit breaker")


@app.post("/api/v1/admin/circuit-breaker/{provider}/force-close")
async def force_close_circuit_breaker(provider: str) -> Dict[str, str]:
    """
    Force close a circuit breaker after maintenance
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        provider_type = LLMProvider(provider)
        await gateway.circuit_breaker.force_close(provider_type)
        
        return {"status": "success", "message": f"Circuit breaker closed for {provider}"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        logger.error("Failed to close circuit breaker", provider=provider, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to close circuit breaker")


@app.post("/api/v1/admin/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Invalidate cache entries
    """
    try:
        if not gateway:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        deleted_count = await gateway.cache_manager.invalidate_cache(pattern)
        
        return {
            "status": "success",
            "deleted_entries": deleted_count,
            "pattern": pattern or "all"
        }
        
    except Exception as e:
        logger.error("Failed to invalidate cache", pattern=pattern, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use structlog configuration
    )
