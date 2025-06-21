"""
Database configuration and session management.
"""

import logging
import uuid
from typing import AsyncGenerator

import azure.cosmos.aio as cosmos
from app.core.config import get_settings
from sqlalchemy import MetaData, String, TypeDecorator, create_engine
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise
    uses String with fixed length for other databases.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy database setup
engine = create_async_engine(
    settings.database_url_sqlalchemy,
    **settings.database_config,
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Database metadata and base
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Cosmos DB client
cosmos_client = None


async def init_db():
    """Initialize database connections."""
    global cosmos_client

    logger.info("Initializing database connections...")

    try:
        # Only initialize Cosmos DB if explicitly enabled
        if settings.COSMOS_DB_ENABLED:
            logger.info("Initializing Cosmos DB...")
            # Initialize Cosmos DB client
            cosmos_client = cosmos.CosmosClient(settings.COSMOS_DB_URL, settings.COSMOS_DB_KEY)

            # Ensure database and container exist
            database = await cosmos_client.create_database_if_not_exists(
                id=settings.COSMOS_DB_DATABASE
            )

            await database.create_container_if_not_exists(
                id=settings.COSMOS_DB_CONTAINER_ITINERARIES,
                partition_key="/tripId",
                offer_throughput=400,  # Minimum throughput for development
            )
            logger.info("Cosmos DB initialization completed")
        else:
            logger.info("Cosmos DB disabled - skipping initialization")
            cosmos_client = None

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_cosmos_client():
    """Get Cosmos DB client."""
    if cosmos_client is None:
        if settings.is_production:
            raise RuntimeError("Cosmos DB client not initialized")
        else:
            raise RuntimeError("Cosmos DB not available in development environment")
    return cosmos_client


async def get_cosmos_container():
    """Get Cosmos DB container."""
    client = await get_cosmos_client()
    database = client.get_database_client(settings.COSMOS_DB_DATABASE)
    return database.get_container_client(settings.COSMOS_DB_CONTAINER)


class DatabaseManager:
    """Database manager for handling connections and transactions."""

    def __init__(self):
        self.sql_engine = engine
        self.cosmos_client = None

    async def startup(self):
        """Startup database connections."""
        await init_db()
        self.cosmos_client = await get_cosmos_client()

    async def shutdown(self):
        """Shutdown database connections."""
        if self.cosmos_client:
            await self.cosmos_client.close()

        await self.sql_engine.dispose()

    async def health_check(self) -> dict:
        """Check database health."""
        health_status = {
            "sql_database": "unhealthy",
            "cosmos_db": "unhealthy",
        }

        try:
            # Check SQL database
            async with SessionLocal() as session:
                await session.execute("SELECT 1")
                health_status["sql_database"] = "healthy"
        except Exception as e:
            logger.error(f"SQL database health check failed: {e}")

        try:
            # Check Cosmos DB
            client = await get_cosmos_client()
            container = await get_cosmos_container()
            await container.read_item("health-check", "health-check")
        except Exception:
            # Expected if health check item doesn't exist
            health_status["cosmos_db"] = "healthy"

        return health_status


# Global database manager instance
db_manager = DatabaseManager()
