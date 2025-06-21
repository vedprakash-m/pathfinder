"""
Maps API endpoints for location services.
Provides endpoints for geocoding, route planning, and place search.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field

from app.core.zero_trust import require_permissions
from app.models.user import User
from app.services.maps_service import maps_service, Location, Place, Route

logger = logging.getLogger(__name__)

router = APIRouter()


class LocationRequest(BaseModel):
    """Request model for location operations."""

    address: str = Field(..., description="Address to geocode")


class LocationResponse(BaseModel):
    """Response model for location data."""

    lat: float
    lng: float
    address: str
    place_id: Optional[str] = None
    name: Optional[str] = None


class PlaceResponse(BaseModel):
    """Response model for place data."""

    place_id: str
    name: str
    address: str
    location: LocationResponse
    rating: Optional[float] = None
    price_level: Optional[int] = None
    types: List[str] = []
    opening_hours: Optional[Dict[str, Any]] = None
    photos: List[str] = []
    phone_number: Optional[str] = None
    website: Optional[str] = None


class RouteRequest(BaseModel):
    """Request model for route planning."""

    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Ending location")
    waypoints: Optional[List[str]] = Field(None, description="Optional waypoints")
    mode: str = Field("driving", description="Travel mode")
    optimize_waypoints: bool = Field(False, description="Optimize waypoint order")


class RouteStepResponse(BaseModel):
    """Response model for route steps."""

    instruction: str
    distance: str
    duration: str
    start_location: LocationResponse
    end_location: LocationResponse


class RouteResponse(BaseModel):
    """Response model for route data."""

    distance: str
    duration: str
    steps: List[RouteStepResponse]
    polyline: str
    start_address: str
    end_address: str


class PlaceSearchRequest(BaseModel):
    """Request model for place search."""

    query: str = Field(..., description="Search query")
    location: Optional[LocationResponse] = Field(None, description="Center location")
    radius: int = Field(50000, description="Search radius in meters")
    place_type: Optional[str] = Field(None, description="Type of place")


def _convert_location_to_response(location: Location) -> LocationResponse:
    """Convert Location dataclass to response model."""
    return LocationResponse(
        lat=location.lat,
        lng=location.lng,
        address=location.address,
        place_id=location.place_id,
        name=location.name,
    )


def _convert_place_to_response(place: Place) -> PlaceResponse:
    """Convert Place dataclass to response model."""
    return PlaceResponse(
        place_id=place.place_id,
        name=place.name,
        address=place.address,
        location=_convert_location_to_response(place.location),
        rating=place.rating,
        price_level=place.price_level,
        types=place.types or [],
        opening_hours=place.opening_hours,
        photos=place.photos or [],
        phone_number=place.phone_number,
        website=place.website,
    )


@router.post("/geocode", response_model=LocationResponse)
async def geocode_address(
    request_data: LocationRequest,
    request: Request,
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Geocode an address to get coordinates.

    Args:
        request: Location request with address
        current_user: Authenticated user

    Returns:
        Location with coordinates
    """
    try:
        location = await maps_service.geocode(request_data.address)

        if not location:
            raise HTTPException(
                status_code=404, detail=f"Location not found for address: {request.address}"
            )

        return _convert_location_to_response(location)

    except Exception as e:
        logger.error(f"Error geocoding address {request.address}: {e}")
        raise HTTPException(status_code=500, detail="Error geocoding address")


@router.get("/reverse-geocode", response_model=LocationResponse)
async def reverse_geocode_coordinates(
    request: Request,
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Reverse geocode coordinates to get address.

    Args:
        lat: Latitude
        lng: Longitude
        current_user: Authenticated user

    Returns:
        Location with address
    """
    try:
        location = await maps_service.reverse_geocode(lat, lng)

        if not location:
            raise HTTPException(
                status_code=404, detail=f"Address not found for coordinates: {lat}, {lng}"
            )

        return _convert_location_to_response(location)

    except Exception as e:
        logger.error(f"Error reverse geocoding coordinates {lat}, {lng}: {e}")
        raise HTTPException(status_code=500, detail="Error reverse geocoding coordinates")


@router.post("/route", response_model=RouteResponse)
async def get_route(
    request_data: RouteRequest,
    request: Request,
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Get route between locations.

    Args:
        request: Route request with origin, destination, and options
        current_user: Authenticated user

    Returns:
        Route information with steps and directions
    """
    try:
        route = await maps_service.get_route(
            origin=request_data.origin,
            destination=request_data.destination,
            waypoints=request_data.waypoints,
            mode=request_data.mode,
            optimize_waypoints=request_data.optimize_waypoints,
        )

        if not route:
            raise HTTPException(
                status_code=404,
                detail=f"Route not found from {request_data.origin} to {request_data.destination}",
            )

        # Convert route steps
        steps = [
            RouteStepResponse(
                instruction=step.instruction,
                distance=step.distance,
                duration=step.duration,
                start_location=_convert_location_to_response(step.start_location),
                end_location=_convert_location_to_response(step.end_location),
            )
            for step in route.steps
        ]

        return RouteResponse(
            distance=route.distance,
            duration=route.duration,
            steps=steps,
            polyline=route.polyline,
            start_address=route.start_address,
            end_address=route.end_address,
        )

    except Exception as e:
        logger.error(f"Error getting route from {request.origin} to {request.destination}: {e}")
        raise HTTPException(status_code=500, detail="Error getting route")


@router.post("/search-places", response_model=List[PlaceResponse])
async def search_places(
    request_data: PlaceSearchRequest,
    request: Request,
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Search for places using Google Places API.

    Args:
        request: Place search request
        current_user: Authenticated user

    Returns:
        List of places matching the search criteria
    """
    try:
        # Convert location if provided
        location = None
        if request_data.location:
            location = Location(
                lat=request_data.location.lat,
                lng=request_data.location.lng,
                address=request_data.location.address,
                place_id=request_data.location.place_id,
                name=request_data.location.name,
            )

        places = await maps_service.search_places(
            query=request_data.query,
            location=location,
            radius=request_data.radius,
            place_type=request_data.place_type,
        )

        return [_convert_place_to_response(place) for place in places]

    except Exception as e:
        logger.error(f"Error searching places for '{request_data.query}': {e}")
        raise HTTPException(status_code=500, detail="Error searching places")


@router.get("/place/{place_id}", response_model=PlaceResponse)
async def get_place_details(
    place_id: str,
    request: Request,
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Get detailed information about a specific place.

    Args:
        place_id: Google Places place ID
        current_user: Authenticated user

    Returns:
        Detailed place information
    """
    try:
        place = await maps_service.get_place_details(place_id)

        if not place:
            raise HTTPException(status_code=404, detail=f"Place not found: {place_id}")

        return _convert_place_to_response(place)

    except Exception as e:
        logger.error(f"Error getting place details for {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Error getting place details")


@router.get("/distance-matrix")
async def get_distance_matrix(
    request: Request,
    origins: str = Query(..., description="Comma-separated list of origin locations"),
    destinations: str = Query(..., description="Comma-separated list of destination locations"),
    mode: str = Query("driving", description="Travel mode"),
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Get distance and duration matrix between multiple origins and destinations.

    Args:
        origins: Comma-separated origin locations
        destinations: Comma-separated destination locations
        mode: Travel mode
        current_user: Authenticated user

    Returns:
        Distance matrix data
    """
    try:
        origins_list = [origin.strip() for origin in origins.split(",")]
        destinations_list = [dest.strip() for dest in destinations.split(",")]

        matrix = await maps_service.get_distance_matrix(
            origins=origins_list, destinations=destinations_list, mode=mode
        )

        if not matrix:
            raise HTTPException(status_code=404, detail="Distance matrix not available")

        return matrix

    except Exception as e:
        logger.error(f"Error getting distance matrix: {e}")
        raise HTTPException(status_code=500, detail="Error getting distance matrix")


@router.get("/nearby-attractions", response_model=List[PlaceResponse])
async def find_nearby_attractions(
    request: Request,
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(25000, description="Search radius in meters"),
    current_user: User = Depends(require_permissions("maps", "read")),
):
    """
    Find tourist attractions near a location.

    Args:
        lat: Latitude
        lng: Longitude
        radius: Search radius in meters
        current_user: Authenticated user

    Returns:
        List of nearby attractions
    """
    try:
        location = Location(lat=lat, lng=lng, address="")

        places = await maps_service.find_nearby_attractions(location=location, radius=radius)

        return [_convert_place_to_response(place) for place in places]

    except Exception as e:
        logger.error(f"Error finding nearby attractions: {e}")
        raise HTTPException(status_code=500, detail="Error finding nearby attractions")
