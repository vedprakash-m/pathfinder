"""
Queue Functions Module

Azure Functions queue triggers for async processing.
"""
from functions.queue.itinerary_generator import bp as itinerary_generator_bp
from functions.queue.notification_sender import bp as notification_sender_bp

__all__ = [
    "itinerary_generator_bp",
    "notification_sender_bp",
]
