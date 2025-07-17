"""
User models for Pathfinder - Cosmos DB Implementation

This module provides User model access following the unified Cosmos DB architecture.
All user data is stored as UserDocument in the single Cosmos DB container.
"""

from app.repositories.cosmos_unified import UserDocument

# Main export for the user model
User = UserDocument

__all__ = ["User", "UserDocument"]
