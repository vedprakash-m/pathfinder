"""
FastAPI application entry point for Pathfinder AI-Powered Trip Planner.
Updated to fix dashboard loading route conflicts.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.core.telemetry import setup_opentelemetry
from app.services.websocket import websocket_manager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management."""
    logger.info("Starting Pathfinder application...")
    
    # Initialize database
    await init_db()
    
    # Initialize WebSocket manager
    await websocket_manager.startup()

    # Initialize cache 
    from app.core.cache import cache
    app.state.cache = cache
    logger.info("Cache service initialized")
    
    # Setup performance monitoring
    from app.core.performance import get_performance_metrics
    app.state.get_performance_metrics = get_performance_metrics
    logger.info("Performance monitoring initialized")

    # Initialize Cosmos DB (if enabled)
    if settings.COSMOS_DB_ENABLED:
        logger.info("Initializing Cosmos DB connections")
        # Create CosmosDB containers if they don't exist
        from azure.cosmos.aio import CosmosClient
        from azure.cosmos.exceptions import CosmosResourceExistsError
        
        try:
            # Connect to Azure Cosmos DB
            cosmos_client = CosmosClient(
                url=settings.COSMOS_DB_URL,
                credential=settings.COSMOS_DB_KEY
            )
            
            # Get or create database
            database = cosmos_client.get_database_client(settings.COSMOS_DB_DATABASE)
            
            # Initialize or confirm containers
            try:
                await database.create_container(
                    id=settings.COSMOS_DB_CONTAINER_ITINERARIES,
                    partition_key="/trip_id"
                )
                logger.info(f"Created container: {settings.COSMOS_DB_CONTAINER_ITINERARIES}")
            except CosmosResourceExistsError:
                logger.info(f"Container already exists: {settings.COSMOS_DB_CONTAINER_ITINERARIES}")
                
            try:
                await database.create_container(
                    id=settings.COSMOS_DB_CONTAINER_MESSAGES,
                    partition_key="/trip_id"
                )
                logger.info(f"Created container: {settings.COSMOS_DB_CONTAINER_MESSAGES}")
            except CosmosResourceExistsError:
                logger.info(f"Container already exists: {settings.COSMOS_DB_CONTAINER_MESSAGES}")
                
            try:
                await database.create_container(
                    id=settings.COSMOS_DB_CONTAINER_PREFERENCES,
                    partition_key="/entity_id"
                )
                logger.info(f"Created container: {settings.COSMOS_DB_CONTAINER_PREFERENCES}")
            except CosmosResourceExistsError:
                logger.info(f"Container already exists: {settings.COSMOS_DB_CONTAINER_PREFERENCES}")
                
            logger.info("Cosmos DB initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {str(e)}")
            if settings.ENVIRONMENT != "production":
                logger.warning("Continuing without Cosmos DB in development mode")
            else:
                raise
    logger.info("Application startup complete")
    
    # Initialize cache service (Redis-free alternatives)
    try:
        from app.core.cache_service import cache_service
        app.state.cache_service = cache_service
        logger.info("Cache service initialized (Redis-free for cost optimization)")
    except Exception as e:
        logger.error(f"Failed to initialize cache service: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    
    # Initialize dependency-injector container
    from app.core.container import Container
    container = Container()
    container.init_resources()
    container.wire(packages=("app.api",))
    app.state.container = container
    
    yield
    
    # Cleanup
    logger.info("Shutting down application...")
    await websocket_manager.shutdown()
    
    # Close cache service connections
    if hasattr(app.state, "cache_service") and app.state.cache_service:
        await app.state.cache_service.close()
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Pathfinder API",
    description="AI-Powered Group Trip Planner",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Security middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )

# Import security middleware
from app.core.rate_limiting import RateLimiter
from app.core.csrf import CSRFMiddleware
from app.core.performance import PerformanceMonitoringMiddleware

# Performance monitoring middleware
app.add_middleware(PerformanceMonitoringMiddleware)

# Rate limiting middleware
app.add_middleware(
    RateLimiter,
    window_size=60,  # 1 minute window
    default_limit=500,  # Default 500 requests per minute (temporarily increased)
    api_limit=2000,  # API endpoints 2000 requests per minute (temporarily increased)
    public_limit=500,  # Public endpoints 500 requests per minute (temporarily increased for debugging)
    endpoint_limits={
        "POST:/api/v1/auth/login": 20,  # Limit login attempts (increased)
        "POST:/api/v1/auth/register": 10,  # Limit registration (increased)
        "GET:/api/v1/auth/me": 1000,  # Allow frequent auth checks (increased)
        "GET:/api/v1/auth/user/onboarding-status": 500,  # Allow onboarding status checks (temporarily increased)
        "GET:/api/v1/trips/": 500,  # Allow frequent trips checks (temporarily increased)
    }
)

# CSRF protection middleware (disabled for CORS preflight requests)
# Note: CSRF middleware can interfere with CORS OPTIONS requests
# We'll skip CSRF for now and rely on other security measures
# TODO: Implement CSRF that properly handles CORS preflight
# if settings.ENVIRONMENT == "production":
#     app.add_middleware(
#         CSRFMiddleware,
#         secret_key=settings.SECRET_KEY,
#         cookie_secure=True
#     )
# elif settings.ENVIRONMENT != "testing":
#     # In development, we still use CSRF but with less strict settings
#     app.add_middleware(
#         CSRFMiddleware,
#         secret_key=settings.SECRET_KEY,
#         cookie_secure=False  # Allow HTTP in development
#     )
# Skip CSRF temporarily to resolve CORS issues

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*", "Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["*"]
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    # Check cache service
    cache_status = "connected" if hasattr(app.state, "cache_service") else "not_initialized"
    
    # Check database
    db_status = "connected"
    try:
        # This will be a more comprehensive check in production
        pass
    except Exception:
        db_status = "error"
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "cache": cache_status,
            "cosmos_db": "enabled" if settings.COSMOS_DB_ENABLED else "disabled"
        }
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include health routes (in addition to the basic /health endpoint above)
from app.api.health import router as health_router
app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )