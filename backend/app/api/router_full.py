from __future__ import annotations
"""
Full API router including all reconstructed endpoints.
"""

from fastapi import APIRouter
from app.api import auth, trips, families, consensus, polls

# Create full API router
api_router = APIRouter()

# Include all reconstructed routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(trips.router, prefix="/trips", tags=["trips"])
api_router.include_router(families.router, prefix="/families", tags=["families"])
api_router.include_router(consensus.router, prefix="/consensus", tags=["consensus"])
api_router.include_router(polls.router, prefix="/polls", tags=["polls"])

# Simple root endpoint
@api_router.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Welcome to Pathfinder API - Full Mode", "status": "production_ready"}

# Health check endpoint  
@api_router.get("/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "healthy", "mode": "full"}
