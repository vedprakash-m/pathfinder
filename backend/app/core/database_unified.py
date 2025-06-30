"""
Unified database service using Cosmos DB per Tech Spec requirements.

This module replaces the hybrid SQL/Cosmos approach with a unified Cosmos DB solution
as specified in the Tech Spec: "Single Cosmos DB account (SQL API) in serverless mode"
"""

import logging
from typing import Optional

from app.core.config import get_settings
from app.repositories.cosmos_unified import unified_cosmos_repo, UnifiedCosmosRepository

settings = get_settings()
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Unified database service using Cosmos DB.
    
    This replaces get_db() dependency with get_cosmos_service() per Tech Spec.
    """
    
    def __init__(self):
        """Initialize the database service."""
        self.cosmos_repo = unified_cosmos_repo
        logger.info("Database service initialized with unified Cosmos DB")
    
    def get_repository(self) -> UnifiedCosmosRepository:
        """Get the unified Cosmos DB repository."""
        return self.cosmos_repo
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            if not self.cosmos_repo.container:
                # In simulation mode, always return True
                return True
            
            # Try a simple query to test connectivity
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.entity_type = 'user'"
            await self.cosmos_repo._query_documents(query)
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Global database service instance
db_service = DatabaseService()


def get_cosmos_service() -> DatabaseService:
    """
    Dependency to get the unified database service.
    
    This replaces get_db() from the SQL-based approach.
    """
    return db_service


def get_cosmos_repository() -> UnifiedCosmosRepository:
    """
    Dependency to get the unified Cosmos DB repository directly.
    
    Use this when you need direct repository access.
    """
    return unified_cosmos_repo
