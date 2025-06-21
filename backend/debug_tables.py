#!/usr/bin/env python3
"""
Debug script to check table creation in test environment.
"""
import asyncio
import os

# Set test environment
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["DISABLE_TELEMETRY"] = "true"

# Load test environment file
import dotenv

dotenv.load_dotenv("/Users/vedprakashmishra/pathfinder/backend/.env.test")

# Import ALL models to ensure they're registered with Base metadata
from app.core.database import Base
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def debug_tables():
    """Debug table creation."""
    try:
        print("Creating test database engine...")
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=True,  # Enable SQL logging
            poolclass=None,
        )

        print(f"Base.metadata.tables keys: {list(Base.metadata.tables.keys())}")

        print("Creating tables...")
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.run_sync(Base.metadata.create_all)

        print("Checking if tables exist...")
        async with engine.connect() as conn:
            # Check if users table exists
            try:
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table';")
                )
                tables = result.fetchall()
                print(f"Created tables: {[table[0] for table in tables]}")
            except Exception as e:
                print(f"Error checking tables: {e}")

        await engine.dispose()
        print("Debug completed successfully")
    except Exception as e:
        print(f"Error in debug_tables: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_tables())
