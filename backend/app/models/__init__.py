"""
Pathfinder Models - Unified Cosmos DB Architecture

This module provides access to all Cosmos DB models and documents used in Pathfinder.
Following the unified architecture pattern, all models are now Cosmos DB documents.
"""

# Import from unified Cosmos repository
from app.repositories.cosmos_unified import TripDocument, UserDocument

# Legacy imports for backward compatibility during migration
# These provide the expected interface for existing code
User = UserDocument
Trip = TripDocument

__all__ = [
    "UserDocument",
    "TripDocument",
    "User",  # Legacy compatibility
    "Trip",  # Legacy compatibility
]
