"""
Trip models for Pathfinder - Cosmos DB Implementation

This module provides Trip model access following the unified Cosmos DB architecture.
All trip data is stored as TripDocument in the single Cosmos DB container.
"""

from app.repositories.cosmos_unified import TripDocument

# Main export for the trip model
Trip = TripDocument

__all__ = ["Trip", "TripDocument"]
