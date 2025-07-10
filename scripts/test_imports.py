#!/usr/bin/env python3
"""
Import validation test for Phase 4 API reconstruction
"""
import sys
import os
sys.path.insert(0, '/Users/vedprakashmishra/pathfinder/backend')

# Test critical imports
test_imports = [
    "from app.models.cosmos.user import UserDocument",
    "from app.models.cosmos.enums import UserRole, TripStatus",
    "from app.models.cosmos.message import MessageType",
    "from app.services.cosmos_service import CosmosService",
    "from app.schemas.trip import TripCreate, TripResponse",
    "from app.schemas.family import FamilyCreate, FamilyResponse",
    "from app.schemas.common import SuccessResponse, ErrorResponse",
    "from app.api.auth import router as auth_router",
    "from app.api.trips import router as trips_router",
    "from app.api.families import router as families_router"
]

print("🧪 Testing Critical Imports")
print("=" * 50)

success_count = 0
total_count = len(test_imports)

for import_stmt in test_imports:
    try:
        exec(import_stmt)
        print(f"✅ {import_stmt}")
        success_count += 1
    except Exception as e:
        print(f"❌ {import_stmt}")
        print(f"   Error: {e}")

print("=" * 50)
print(f"📊 Results: {success_count}/{total_count} imports successful")

if success_count == total_count:
    print("🎉 All imports successful! API reconstruction complete.")
else:
    print(f"⚠️  {total_count - success_count} import errors need fixing.")
