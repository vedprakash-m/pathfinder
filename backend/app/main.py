"""
FastAPI application entry point for Pathfinder AI-Powered Trip Planner.
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
    
    # Initialize Celery (if enabled)
    if settings.REDIS_URL:
        try:
            from app.core.celery_app import celery_app
            logger.info("Celery background task system initialized")
            app.state.celery = celery_app
        except Exception as e:
            logger.error(f"Failed to initialize Celery: {e}")
            if settings.ENVIRONMENT == "production":
                raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down application...")
    await websocket_manager.shutdown()
    
    # Close any open connections
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
    
    # Close Celery connections
    if hasattr(app.state, "celery") and app.state.celery:
        app.state.celery.control.shutdown()
    
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
        allowed_hosts=settings.ALLOWED_HOSTS,
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
    default_limit=100,  # Default 100 requests per minute
    api_limit=1000,  # API endpoints 1000 requests per minute
    public_limit=30,  # Public endpoints 30 requests per minute
    endpoint_limits={
        "POST:/api/v1/auth/login": 10,  # Limit login attempts
        "POST:/api/v1/auth/register": 5,  # Limit registration
    }
)

# CSRF protection middleware (disabled in testing)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        CSRFMiddleware,
        secret_key=settings.SECRET_KEY,
        cookie_secure=True
    )
elif settings.ENVIRONMENT != "testing":
    # In development, we still use CSRF but with less strict settings
    app.add_middleware(
        CSRFMiddleware,
        secret_key=settings.SECRET_KEY,
        cookie_secure=False  # Allow HTTP in development
    )
# Skip CSRF in testing mode

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*", "X-CSRF-Token"],  # Add CSRF token header
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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )