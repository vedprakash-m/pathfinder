"""
User model for Cosmos DB
"""
from app.repositories.cosmos_unified import UserDocument

# Re-export UserDocument from the unified repository
__all__ = ["UserDocument"]
