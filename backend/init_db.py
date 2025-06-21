#!/usr/bin/env python3
"""
Database initialization script
Creates the database and all tables based on SQLAlchemy models
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models import *  # Import all models


async def create_database():
    """Create all database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
    return True


if __name__ == "__main__":
    success = asyncio.run(create_database())
    sys.exit(0 if success else 1)
