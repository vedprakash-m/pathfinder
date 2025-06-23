#!/usr/bin/env python3
"""
Fix database schema for tests - recreate with current model definitions
"""

import asyncio
import os
from app.core.database import Base, get_async_engine

async def recreate_database():
    """Recreate database with current schema."""
    
    # Remove existing database
    if os.path.exists("pathfinder.db"):
        os.remove("pathfinder.db")
        print("Removed existing database")
    
    # Get async engine
    engine = get_async_engine()
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables with current schema")
    
    await engine.dispose()
    print("Database schema fixed!")

if __name__ == "__main__":
    asyncio.run(recreate_database()) 