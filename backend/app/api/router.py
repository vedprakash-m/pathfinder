"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.trips import router as trips_router
from app.api.families import router as families_router
from app.api.itineraries import router as itineraries_router
from app.api.reservations import router as reservations_router
from app.api.notifications import router as notifications_router
from app.api.maps import router as maps_router
from app.api.websocket import router as websocket_router

api_router = APIRouter()

# Include all routers with their prefixes
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(trips_router, prefix="/trips", tags=["Trips"])
api_router.include_router(families_router, prefix="/families", tags=["Families"])
api_router.include_router(itineraries_router, prefix="/itineraries", tags=["Itineraries"])
api_router.include_router(reservations_router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(maps_router, prefix="/maps", tags=["Maps"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "healthy", "message": "Pathfinder API is running"}
