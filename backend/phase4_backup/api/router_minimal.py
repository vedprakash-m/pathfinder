from __future__ import annotations
"""
Minimal API router for foundation testing.
This file contains only essential, working endpoints during architectural repair.
"""

from fastapi import APIRouter

# Create minimal API router with only working endpoints
api_router = APIRouter()

# Simple root endpoint
@api_router.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Welcome to Pathfinder API - Minimal Mode", "status": "architectural_repair"}


# Health check endpoint  
@api_router.get("/health")
async def api_health():
    """API health check endpoint."""
    return {"status": "healthy", "mode": "minimal"}
