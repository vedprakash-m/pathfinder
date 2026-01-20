"""
Pathfinder API - Azure Functions Entry Point

This is the main entry point for the Azure Functions application.
All HTTP, Queue, and Timer triggers are registered here via blueprints.
"""
import logging

import azure.functions as func

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Import HTTP blueprints
from functions.http.assistant import bp as assistant_bp
from functions.http.auth import bp as auth_bp
from functions.http.collaboration import bp as collaboration_bp
from functions.http.families import bp as families_bp
from functions.http.health import bp as health_bp
from functions.http.itineraries import bp as itineraries_bp
from functions.http.signalr import bp as signalr_bp
from functions.http.trips import bp as trips_bp

# Import Queue blueprints
from functions.queue.itinerary_generator import bp as itinerary_queue_bp
from functions.queue.notification_sender import bp as notification_queue_bp

# Import Timer blueprints
from functions.timer.cleanup import bp as cleanup_bp

# Create function app with anonymous auth level (we handle auth ourselves)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register all blueprints
app.register_blueprint(health_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(trips_bp)
app.register_blueprint(families_bp)
app.register_blueprint(itineraries_bp)
app.register_blueprint(collaboration_bp)
app.register_blueprint(assistant_bp)
app.register_blueprint(signalr_bp)
app.register_blueprint(itinerary_queue_bp)
app.register_blueprint(notification_queue_bp)
app.register_blueprint(cleanup_bp)
