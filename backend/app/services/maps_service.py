"""
Maps service for location-based operations.
Provides Google Maps API integration for geocoding, route planning, and place search.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Location data structure."""

    lat: float
    lng: float
    address: str
    place_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class RouteStep:
    """Route step information."""

    instruction: str
    distance: str
    duration: str
    start_location: Location
    end_location: Location


@dataclass
class Route:
    """Route information."""

    distance: str
    duration: str
    steps: List[RouteStep]
    polyline: str
    start_address: str
    end_address: str


@dataclass
class Place:
    """Place information from Google Places API."""

    place_id: str
    name: str
    address: str
    location: Location
    rating: Optional[float] = None
    price_level: Optional[int] = None
    types: List[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    photos: List[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None


class MapsService:
    """Google Maps service for location operations."""

    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def geocode(self, address: str) -> Optional[Location]:
        """
        Geocode an address to get coordinates.

        Args:
            address: Address to geocode

        Returns:
            Location object with coordinates or None if not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/geocode/json"
            params = {"address": address, "key": self.api_key}

            async with session.get(url, params=params) as response:
                data = await response.json()

                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    location = result["geometry"]["location"]

                    return Location(
                        lat=location["lat"],
                        lng=location["lng"],
                        address=result["formatted_address"],
                        place_id=result.get("place_id"),
                        name=address,
                    )

                logger.warning(f"Geocoding failed for {address}: {data['status']}")
                return None

        except Exception as e:
            logger.error(f"Error geocoding address {address}: {e}")
            return None

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[Location]:
        """
        Reverse geocode coordinates to get address.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Location object with address or None if not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/geocode/json"
            params = {"latlng": f"{lat},{lng}", "key": self.api_key}

            async with session.get(url, params=params) as response:
                data = await response.json()

                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]

                    return Location(
                        lat=lat,
                        lng=lng,
                        address=result["formatted_address"],
                        place_id=result.get("place_id"),
                    )

                logger.warning(f"Reverse geocoding failed for {lat},{lng}: {data['status']}")
                return None

        except Exception as e:
            logger.error(f"Error reverse geocoding {lat},{lng}: {e}")
            return None

    async def get_route(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None,
        mode: str = "driving",
        optimize_waypoints: bool = False,
    ) -> Optional[Route]:
        """
        Get route between locations.

        Args:
            origin: Starting location
            destination: Ending location
            waypoints: Optional intermediate waypoints
            mode: Travel mode (driving, walking, bicycling, transit)
            optimize_waypoints: Whether to optimize waypoint order

        Returns:
            Route object or None if route not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "key": self.api_key,
            }

            if waypoints:
                waypoints_str = "|".join(waypoints)
                if optimize_waypoints:
                    waypoints_str = f"optimize:true|{waypoints_str}"
                params["waypoints"] = waypoints_str

            async with session.get(url, params=params) as response:
                data = await response.json()

                if data["status"] == "OK" and data["routes"]:
                    route_data = data["routes"][0]
                    leg = route_data["legs"][0]

                    # Parse route steps
                    steps = []
                    for step_data in leg["steps"]:
                        step = RouteStep(
                            instruction=step_data["html_instructions"],
                            distance=step_data["distance"]["text"],
                            duration=step_data["duration"]["text"],
                            start_location=Location(
                                lat=step_data["start_location"]["lat"],
                                lng=step_data["start_location"]["lng"],
                                address="",
                            ),
                            end_location=Location(
                                lat=step_data["end_location"]["lat"],
                                lng=step_data["end_location"]["lng"],
                                address="",
                            ),
                        )
                        steps.append(step)

                    return Route(
                        distance=leg["distance"]["text"],
                        duration=leg["duration"]["text"],
                        steps=steps,
                        polyline=route_data["overview_polyline"]["points"],
                        start_address=leg["start_address"],
                        end_address=leg["end_address"],
                    )

                logger.warning(f"Route not found: {data['status']}")
                return None

        except Exception as e:
            logger.error(f"Error getting route from {origin} to {destination}: {e}")
            return None

    async def search_places(
        self,
        query: str,
        location: Optional[Location] = None,
        radius: int = 50000,
        place_type: Optional[str] = None,
    ) -> List[Place]:
        """
        Search for places using Google Places API.

        Args:
            query: Search query
            location: Center location for search
            radius: Search radius in meters
            place_type: Type of place (restaurant, lodging, tourist_attraction, etc.)

        Returns:
            List of Place objects
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/place/textsearch/json"
            params = {"query": query, "key": self.api_key}

            if location:
                params["location"] = f"{location.lat},{location.lng}"
                params["radius"] = radius

            if place_type:
                params["type"] = place_type

            async with session.get(url, params=params) as response:
                data = await response.json()

                places = []
                if data["status"] == "OK":
                    for result in data["results"]:
                        place_location = Location(
                            lat=result["geometry"]["location"]["lat"],
                            lng=result["geometry"]["location"]["lng"],
                            address=result.get("formatted_address", ""),
                            place_id=result["place_id"],
                            name=result["name"],
                        )

                        photos = []
                        if "photos" in result:
                            for photo in result["photos"][:3]:  # Limit to 3 photos
                                photo_url = f"{self.base_url}/place/photo?maxwidth=400&photoreference={photo['photo_reference']}&key={self.api_key}"
                                photos.append(photo_url)

                        place = Place(
                            place_id=result["place_id"],
                            name=result["name"],
                            address=result.get("formatted_address", ""),
                            location=place_location,
                            rating=result.get("rating"),
                            price_level=result.get("price_level"),
                            types=result.get("types", []),
                            photos=photos,
                        )
                        places.append(place)

                return places

        except Exception as e:
            logger.error(f"Error searching places for '{query}': {e}")
            return []

    async def get_place_details(self, place_id: str) -> Optional[Place]:
        """
        Get detailed information about a specific place.

        Args:
            place_id: Google Places place ID

        Returns:
            Place object with detailed information or None if not found
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "name,formatted_address,geometry,rating,price_level,types,opening_hours,photos,international_phone_number,website",
                "key": self.api_key,
            }

            async with session.get(url, params=params) as response:
                data = await response.json()

                if data["status"] == "OK":
                    result = data["result"]

                    place_location = Location(
                        lat=result["geometry"]["location"]["lat"],
                        lng=result["geometry"]["location"]["lng"],
                        address=result.get("formatted_address", ""),
                        place_id=place_id,
                        name=result["name"],
                    )

                    photos = []
                    if "photos" in result:
                        for photo in result["photos"][:5]:  # Limit to 5 photos
                            photo_url = f"{self.base_url}/place/photo?maxwidth=800&photoreference={photo['photo_reference']}&key={self.api_key}"
                            photos.append(photo_url)

                    opening_hours = None
                    if "opening_hours" in result:
                        opening_hours = {
                            "open_now": result["opening_hours"].get("open_now"),
                            "periods": result["opening_hours"].get("periods", []),
                            "weekday_text": result["opening_hours"].get("weekday_text", []),
                        }

                    return Place(
                        place_id=place_id,
                        name=result["name"],
                        address=result.get("formatted_address", ""),
                        location=place_location,
                        rating=result.get("rating"),
                        price_level=result.get("price_level"),
                        types=result.get("types", []),
                        opening_hours=opening_hours,
                        photos=photos,
                        phone_number=result.get("international_phone_number"),
                        website=result.get("website"),
                    )

                logger.warning(f"Place details not found for {place_id}: {data['status']}")
                return None

        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")
            return None

    async def get_distance_matrix(
        self, origins: List[str], destinations: List[str], mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Get distance and duration matrix between multiple origins and destinations.

        Args:
            origins: List of origin locations
            destinations: List of destination locations
            mode: Travel mode (driving, walking, bicycling, transit)

        Returns:
            Distance matrix data
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/distancematrix/json"
            params = {
                "origins": "|".join(origins),
                "destinations": "|".join(destinations),
                "mode": mode,
                "key": self.api_key,
            }

            async with session.get(url, params=params) as response:
                data = await response.json()

                if data["status"] == "OK":
                    return {
                        "origins": data["origin_addresses"],
                        "destinations": data["destination_addresses"],
                        "rows": data["rows"],
                    }

                logger.warning(f"Distance matrix failed: {data['status']}")
                return {}

        except Exception as e:
            logger.error(f"Error getting distance matrix: {e}")
            return {}

    async def find_nearby_attractions(
        self, location: Location, radius: int = 25000, place_types: Optional[List[str]] = None
    ) -> List[Place]:
        """
        Find tourist attractions near a location.

        Args:
            location: Center location
            radius: Search radius in meters
            place_types: Types of places to search for

        Returns:
            List of nearby attractions
        """
        if place_types is None:
            place_types = ["tourist_attraction", "museum", "park", "amusement_park", "zoo"]

        all_places = []

        try:
            session = await self._get_session()

            for place_type in place_types:
                url = f"{self.base_url}/place/nearbysearch/json"
                params = {
                    "location": f"{location.lat},{location.lng}",
                    "radius": radius,
                    "type": place_type,
                    "key": self.api_key,
                }

                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data["status"] == "OK":
                        for result in data["results"]:
                            place_location = Location(
                                lat=result["geometry"]["location"]["lat"],
                                lng=result["geometry"]["location"]["lng"],
                                address=result.get("vicinity", ""),
                                place_id=result["place_id"],
                                name=result["name"],
                            )

                            place = Place(
                                place_id=result["place_id"],
                                name=result["name"],
                                address=result.get("vicinity", ""),
                                location=place_location,
                                rating=result.get("rating"),
                                price_level=result.get("price_level"),
                                types=result.get("types", []),
                            )
                            all_places.append(place)

            # Remove duplicates and sort by rating
            unique_places = {p.place_id: p for p in all_places}.values()
            return sorted(unique_places, key=lambda p: p.rating or 0, reverse=True)

        except Exception as e:
            logger.error(f"Error finding nearby attractions: {e}")
            return []


# Global service instance
maps_service = MapsService()


async def cleanup_maps_service():
    """Cleanup function for maps service."""
    await maps_service.close()
