#!/usr/bin/env python3
"""
Phase 3.5: Fix Cosmos Model Dependencies
This script fixes the remaining dependencies in the Cosmos models directory.
"""

import os
from pathlib import Path

class CosmosModelFixer:
    """Tool for fixing cosmos model dependencies."""
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.cosmos_models_path = self.backend_path / "app" / "models" / "cosmos"
        
    def create_enum_definitions(self):
        """Create enum definitions that were removed with SQL models."""
        enum_definitions = '''"""
Enum definitions for Cosmos models.
These replace the enums that were in the removed SQL models.
"""

from enum import Enum


class ActivityType(str, Enum):
    """Activity type enumeration."""
    ACCOMMODATION = "accommodation"
    TRANSPORTATION = "transportation"
    DINING = "dining"
    ATTRACTION = "attraction"
    ACTIVITY = "activity"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class DifficultyLevel(str, Enum):
    """Activity difficulty level."""
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    EXPERT = "expert"


class ItineraryStatus(str, Enum):
    """Itinerary status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
'''
        
        enum_file = self.cosmos_models_path / "enums.py"
        with open(enum_file, 'w') as f:
            f.write(enum_definitions)
        
        print(f"✅ Created enum definitions: {enum_file}")
    
    def fix_cosmos_imports(self):
        """Fix imports in cosmos model files."""
        for model_file in self.cosmos_models_path.glob("*.py"):
            if model_file.name in ["__init__.py", "enums.py"]:
                continue
            
            try:
                with open(model_file, 'r') as f:
                    content = f.read()
                
                # Replace SQL model imports with local enum imports
                updated_content = content.replace(
                    "from app.models.itinerary import ActivityType, DifficultyLevel, ItineraryStatus",
                    "from app.models.cosmos.enums import ActivityType, DifficultyLevel, ItineraryStatus"
                )
                
                # Replace any other SQL model imports
                updated_content = updated_content.replace(
                    "from app.models.",
                    "# Removed SQL import: from app.models."
                )
                
                if updated_content != content:
                    with open(model_file, 'w') as f:
                        f.write(updated_content)
                    print(f"✅ Fixed imports in: {model_file}")
                
            except Exception as e:
                print(f"❌ Error fixing {model_file}: {e}")
    
    def update_cosmos_init(self):
        """Update cosmos models __init__.py."""
        init_file = self.cosmos_models_path / "__init__.py"
        
        init_content = '''"""
Cosmos DB model definitions.
These models are used for all database operations in the unified architecture.
"""

from app.models.cosmos.enums import ActivityType, DifficultyLevel, ItineraryStatus

__all__ = [
    "ActivityType",
    "DifficultyLevel", 
    "ItineraryStatus",
]
'''
        
        with open(init_file, 'w') as f:
            f.write(init_content)
        
        print(f"✅ Updated cosmos models __init__.py")
    
    def fix_services_cosmos_imports(self):
        """Fix imports in services/cosmos directory."""
        services_cosmos_path = self.backend_path / "app" / "services" / "cosmos"
        
        if not services_cosmos_path.exists():
            print("✅ No services/cosmos directory to fix")
            return
        
        for service_file in services_cosmos_path.glob("*.py"):
            if service_file.name.startswith("__"):
                continue
            
            try:
                with open(service_file, 'r') as f:
                    content = f.read()
                
                # Replace SQL model imports
                updated_content = content.replace(
                    "from app.models.itinerary import",
                    "from app.models.cosmos.enums import"
                )
                
                if updated_content != content:
                    with open(service_file, 'w') as f:
                        f.write(updated_content)
                    print(f"✅ Fixed service imports in: {service_file}")
                
            except Exception as e:
                print(f"❌ Error fixing service {service_file}: {e}")
    
    def execute_fix(self):
        """Execute the cosmos model fix."""
        print("🚀 Starting Phase 3.5: Fix Cosmos Model Dependencies")
        print("=" * 60)
        
        # Step 1: Create enum definitions
        self.create_enum_definitions()
        
        # Step 2: Fix cosmos model imports
        self.fix_cosmos_imports()
        
        # Step 3: Update __init__.py
        self.update_cosmos_init()
        
        # Step 4: Fix services cosmos imports
        self.fix_services_cosmos_imports()
        
        print("\n✅ Phase 3.5 Complete: Cosmos Model Dependencies Fixed!")

def main():
    """Main execution function."""
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_path):
        print(f"❌ Backend path not found: {backend_path}")
        return
    
    fixer = CosmosModelFixer(backend_path)
    fixer.execute_fix()

if __name__ == "__main__":
    main()
