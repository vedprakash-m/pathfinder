"""
HTTP Functions Module

Azure Functions HTTP triggers for the Pathfinder API.
"""
from functions.http.assistant import bp as assistant_bp
from functions.http.auth import bp as auth_bp
from functions.http.collaboration import bp as collaboration_bp
from functions.http.families import bp as families_bp
from functions.http.health import bp as health_bp
from functions.http.itineraries import bp as itineraries_bp
from functions.http.signalr import bp as signalr_bp
from functions.http.trips import bp as trips_bp

__all__ = [
    "health_bp",
    "auth_bp",
    "trips_bp",
    "families_bp",
    "itineraries_bp",
    "collaboration_bp",
    "assistant_bp",
    "signalr_bp",
]
