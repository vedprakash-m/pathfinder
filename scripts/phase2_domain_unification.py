#!/usr/bin/env python3
"""
Phase 2: Domain Model Unification - Systematic Reconstruction Tool
This script implements the domain model unification phase of the architectural repair.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List

class DomainModelUnifier:
    """Tool for unifying domain models to Cosmos DB only."""
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.sql_models_path = self.backend_path / "app" / "models"
        self.cosmos_models_path = self.backend_path / "app" / "repositories" / "cosmos_unified.py"
        self.backup_path = self.backend_path / "architectural_repair_backup"
        
    def create_backup(self):
        """Create backup of current state before making changes."""
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
        
        self.backup_path.mkdir(exist_ok=True)
        
        # Backup SQL models
        if self.sql_models_path.exists():
            shutil.copytree(self.sql_models_path, self.backup_path / "sql_models")
        
        # Backup cosmos models
        if self.cosmos_models_path.exists():
            shutil.copy2(self.cosmos_models_path, self.backup_path / "cosmos_unified.py")
        
        print(f"✅ Backup created in {self.backup_path}")
    
    def analyze_sql_models(self) -> Dict[str, Dict]:
        """Analyze SQL models to understand what needs to be migrated."""
        models = {}
        
        if not self.sql_models_path.exists():
            return models
        
        for model_file in self.sql_models_path.glob("*.py"):
            if model_file.name.startswith("__"):
                continue
            
            try:
                with open(model_file, 'r') as f:
                    content = f.read()
                
                # Extract model information
                model_info = {
                    'file': str(model_file),
                    'has_sqlalchemy': 'from sqlalchemy' in content or 'import sqlalchemy' in content,
                    'has_relationships': 'relationship(' in content,
                    'has_foreign_keys': 'ForeignKey(' in content,
                    'classes': []
                }
                
                # Extract class names
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('class ') and '(Base)' in line:
                        class_name = line.strip().split('class ')[1].split('(')[0]
                        model_info['classes'].append(class_name)
                
                models[model_file.name] = model_info
                
            except Exception as e:
                print(f"❌ Error analyzing {model_file}: {e}")
        
        return models
    
    def check_cosmos_models(self) -> Dict:
        """Check existing Cosmos models."""
        if not self.cosmos_models_path.exists():
            return {}
        
        try:
            with open(self.cosmos_models_path, 'r') as f:
                content = f.read()
            
            cosmos_info = {
                'file': str(self.cosmos_models_path),
                'has_cosmos': 'CosmosDocument' in content,
                'document_classes': []
            }
            
            # Extract document class names
            lines = content.split('\n')
            for line in lines:
                if line.strip().startswith('class ') and 'CosmosDocument' in line:
                    class_name = line.strip().split('class ')[1].split('(')[0]
                    cosmos_info['document_classes'].append(class_name)
            
            return cosmos_info
            
        except Exception as e:
            print(f"❌ Error analyzing Cosmos models: {e}")
            return {}
    
    def remove_sql_models(self):
        """Remove SQL model files completely."""
        if not self.sql_models_path.exists():
            print("✅ No SQL models to remove")
            return
        
        # Get list of files to remove
        files_to_remove = []
        for model_file in self.sql_models_path.glob("*.py"):
            if model_file.name != "__init__.py":
                files_to_remove.append(model_file)
        
        print(f"📋 Removing {len(files_to_remove)} SQL model files:")
        for file_path in files_to_remove:
            print(f"   - {file_path.name}")
            file_path.unlink()
        
        # Update __init__.py to be empty
        init_file = self.sql_models_path / "__init__.py"
        if init_file.exists():
            with open(init_file, 'w') as f:
                f.write('"""SQL models removed during architectural unification."""\n')
        
        print("✅ SQL models removed successfully")
    
    def update_imports(self):
        """Update all imports to use Cosmos models only."""
        import_updates = [
            ("from app.models.user import User", "# SQL User model removed - use Cosmos UserDocument"),
            ("from app.models.family import Family", "# SQL Family model removed - use Cosmos FamilyDocument"),
            ("from app.models.trip import Trip", "# SQL Trip model removed - use Cosmos TripDocument"),
            ("from ..models.user import User", "# SQL User model removed - use Cosmos UserDocument"),
            ("from ..models.family import Family", "# SQL Family model removed - use Cosmos FamilyDocument"),
            ("from ..models.trip import Trip", "# SQL Trip model removed - use Cosmos TripDocument"),
        ]
        
        # Find all Python files that might have SQL model imports
        for py_file in self.backend_path.rglob("*.py"):
            if "architectural_repair_backup" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                modified = False
                for old_import, new_import in import_updates:
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        modified = True
                
                if modified:
                    with open(py_file, 'w') as f:
                        f.write(content)
                    print(f"   Updated imports in {py_file}")
                    
            except Exception as e:
                print(f"❌ Error updating imports in {py_file}: {e}")
    
    def generate_migration_report(self) -> str:
        """Generate detailed migration report."""
        sql_models = self.analyze_sql_models()
        cosmos_models = self.check_cosmos_models()
        
        report = []
        report.append("=" * 80)
        report.append("DOMAIN MODEL UNIFICATION REPORT")
        report.append("=" * 80)
        
        # SQL Models Analysis
        report.append(f"\n📊 SQL MODELS ANALYSIS:")
        report.append(f"   Total SQL Model Files: {len(sql_models)}")
        
        for filename, info in sql_models.items():
            report.append(f"\n   📁 {filename}:")
            report.append(f"      Classes: {info['classes']}")
            report.append(f"      Has SQLAlchemy: {info['has_sqlalchemy']}")
            report.append(f"      Has Relationships: {info['has_relationships']}")
            report.append(f"      Has Foreign Keys: {info['has_foreign_keys']}")
        
        # Cosmos Models Analysis
        report.append(f"\n📊 COSMOS MODELS ANALYSIS:")
        if cosmos_models:
            report.append(f"   Document Classes: {cosmos_models['document_classes']}")
            report.append(f"   Has CosmosDocument: {cosmos_models['has_cosmos']}")
        else:
            report.append("   No Cosmos models found")
        
        # Migration Strategy
        report.append(f"\n🔄 MIGRATION STRATEGY:")
        report.append("   1. Create backup of current state")
        report.append("   2. Remove all SQL model files")
        report.append("   3. Update imports to use Cosmos models")
        report.append("   4. Validate that Cosmos models have all required entities")
        report.append("   5. Update repository layer to use unified Cosmos access")
        
        return "\n".join(report)
    
    def execute_phase2(self):
        """Execute Phase 2: Domain Model Unification."""
        print("🚀 Starting Phase 2: Domain Model Unification")
        print("=" * 60)
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Generate migration report
        report = self.generate_migration_report()
        print(report)
        
        # Save report
        with open(self.backend_path / "phase2_migration_report.txt", 'w') as f:
            f.write(report)
        
        # Step 3: Remove SQL models
        print("\n🔄 Removing SQL models...")
        self.remove_sql_models()
        
        # Step 4: Update imports
        print("\n🔄 Updating imports...")
        self.update_imports()
        
        print("\n✅ Phase 2 Domain Model Unification Complete!")
        print("📋 Next Steps:")
        print("   1. Review Cosmos models for completeness")
        print("   2. Test basic application functionality")
        print("   3. Proceed to Phase 3: Service Layer Standardization")

def main():
    """Main execution function."""
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_path):
        print(f"❌ Backend path not found: {backend_path}")
        return
    
    unifier = DomainModelUnifier(backend_path)
    unifier.execute_phase2()

if __name__ == "__main__":
    main()
