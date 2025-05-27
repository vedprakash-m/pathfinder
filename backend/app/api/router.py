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
from app.api.trip_messages import router as trip_messages_router
from app.api.health import router as health_router
from app.api.admin import router as admin_router
from app.api.exports import router as exports_router

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
api_router.include_router(trip_messages_router, prefix="/trips", tags=["Trip Messages"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(admin_router, prefix="/admin", tags=["Administration"])
api_router.include_router(exports_router, prefix="/exports", tags=["Data Export"])

# Simple root endpoint
@api_router.get("/")
async def root():
    """API root endpoint."""
    return {"message": "Welcome to Pathfinder API", "docs": "/docs"}
