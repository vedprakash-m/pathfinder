"""
Cosmos service for unified database operations
"""
from app.repositories.cosmos_unified import UnifiedCosmosRepository

# Re-export as CosmosService for backward compatibility
CosmosService = UnifiedCosmosRepository

__all__ = ["CosmosService"]
