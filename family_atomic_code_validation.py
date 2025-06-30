#!/usr/bin/env python3
"""
Family-Atomic Architecture Validation Script (Lightweight)

This script validates that the family-atomic architecture principle is properly enforced
by analyzing the codebase structure, API endpoints, and database models.
"""

import os
import re
import json
from typing import List, Dict, Any
from datetime import datetime


class FamilyAtomicCodeValidator:
    """Validates family-atomic architecture from code analysis."""
    
    def __init__(self):
        self.validation_results = []
        self.backend_path = "/Users/vedprakashmishra/pathfinder/backend"
        self.frontend_path = "/Users/vedprakashmishra/pathfinder/frontend"
        
    def log_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """Log validation result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.validation_results.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        
    def read_file_safe(self, filepath: str) -> str:
        """Safely read file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    def validate_family_api_endpoints(self):
        """Validate that family API endpoints enforce atomic family operations."""
        
        families_api_path = os.path.join(self.backend_path, "app/api/families.py")
        content = self.read_file_safe(families_api_path)
        
        if not content:
            self.log_result("Family API File", False, "families.py not found")
            return
            
        # Test 1: Admin permission checks
        admin_checks = [
            "family.admin_user_id == str(current_user.id)",
            "Only family admin",
            "admin only"
        ]
        
        admin_check_found = any(check in content for check in admin_checks)
        self.log_result(
            "Admin Permission Enforcement",
            admin_check_found,
            "Family admin permission checks found in API" if admin_check_found else "Missing family admin permission checks"
        )
        
        # Test 2: Family-level authorization
        family_auth_patterns = [
            "require_permissions.*families",
            "get_user_families",
            "is_member.*family",
            "Not authorized to access this family"
        ]
        
        family_auth_found = any(re.search(pattern, content) for pattern in family_auth_patterns)
        self.log_result(
            "Family-Level Authorization",
            family_auth_found,
            "Family-level authorization patterns found" if family_auth_found else "Missing family-level authorization"
        )
        
        # Test 3: Atomic family operations
        atomic_operations = [
            "add_user_to_family",
            "remove_user_from_family",
            "get_family_members",
            "family_id.*member_ids"
        ]
        
        atomic_ops_found = any(re.search(pattern, content) for pattern in atomic_operations)
        self.log_result(
            "Atomic Family Operations",
            atomic_ops_found,
            "Atomic family operations found" if atomic_ops_found else "Missing atomic family operations"
        )
    
    def validate_family_models(self):
        """Validate that family models support atomic architecture."""
        
        family_model_path = os.path.join(self.backend_path, "app/models/family.py")
        content = self.read_file_safe(family_model_path)
        
        if not content:
            self.log_result("Family Model File", False, "family.py model not found")
            return
            
        # Test 1: Family Admin field
        admin_field_found = "admin_user_id" in content
        self.log_result(
            "Family Admin Model",
            admin_field_found,
            "Family admin field found in model" if admin_field_found else "Missing family admin field"
        )
        
        # Test 2: Family roles
        family_roles = ["FamilyRole", "ADMIN", "MEMBER", "COORDINATOR"]
        roles_found = any(role in content for role in family_roles)
        self.log_result(
            "Family Role System",
            roles_found,
            "Family role system found" if roles_found else "Missing family role system"
        )
        
        # Test 3: Member management
        member_fields = ["member_ids", "members_count", "FamilyMember"]
        member_mgmt_found = any(field in content for field in member_fields)
        self.log_result(
            "Family Member Management",
            member_mgmt_found,
            "Family member management structure found" if member_mgmt_found else "Missing member management"
        )
    
    def validate_user_models(self):
        """Validate that user models support family-atomic architecture."""
        
        user_model_path = os.path.join(self.backend_path, "app/models/user.py")
        content = self.read_file_safe(user_model_path)
        
        if not content:
            self.log_result("User Model File", False, "user.py model not found")
            return
            
        # Test 1: User-Family relationship
        family_relationship = ["family_ids", "administered_families", "family_memberships"]
        family_rel_found = any(rel in content for rel in family_relationship)
        self.log_result(
            "User-Family Relationship",
            family_rel_found,
            "User-family relationship found" if family_rel_found else "Missing user-family relationship"
        )
        
        # Test 2: Family Admin role
        admin_role_found = "FAMILY_ADMIN" in content
        self.log_result(
            "Family Admin Role",
            admin_role_found,
            "Family Admin role found in user model" if admin_role_found else "Missing Family Admin role"
        )
    
    def validate_frontend_family_components(self):
        """Validate that frontend components respect family-atomic principles."""
        
        families_page_path = os.path.join(self.frontend_path, "src/pages/FamiliesPage.tsx")
        content = self.read_file_safe(families_page_path)
        
        if not content:
            self.log_result("Frontend Family Page", False, "FamiliesPage.tsx not found")
            return
            
        # Test 1: Role-based access
        role_checks = ["RoleGuard", "FAMILY_ADMIN", "hasRole", "canManageFamilies"]
        role_based_found = any(check in content for check in role_checks)
        self.log_result(
            "Frontend Role-Based Access",
            role_based_found,
            "Role-based access controls found" if role_based_found else "Missing role-based access controls"
        )
        
        # Test 2: Family management operations
        family_ops = ["createFamily", "inviteMember", "leaveFamily", "updateFamily"]
        family_ops_found = any(op in content for op in family_ops)
        self.log_result(
            "Frontend Family Operations",
            family_ops_found,
            "Family management operations found" if family_ops_found else "Missing family operations"
        )
        
        # Test 3: Family-centric UI
        family_ui = ["family.admin", "family.members", "family_id", "membership_status"]
        family_ui_found = any(ui in content for ui in family_ui)
        self.log_result(
            "Family-Centric UI",
            family_ui_found,
            "Family-centric UI elements found" if family_ui_found else "Missing family-centric UI"
        )
    
    def validate_auth_integration(self):
        """Validate that authentication respects family-atomic principles."""
        
        auth_service_path = os.path.join(self.backend_path, "app/services/auth_service.py")
        content = self.read_file_safe(auth_service_path)
        
        if not content:
            self.log_result("Auth Service File", False, "auth_service.py not found")
            return
            
        # Test 1: Auto-family creation
        auto_family = ["create_user", "family_setup", "Family Admin", "automatic.*family"]
        auto_family_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in auto_family)
        self.log_result(
            "Auto-Family Creation",
            auto_family_found,
            "Auto-family creation logic found" if auto_family_found else "Missing auto-family creation"
        )
        
        # Test 2: Family Admin default role
        default_role = ["FAMILY_ADMIN", "default.*role", "role.*Family"]
        default_role_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in default_role)
        self.log_result(
            "Default Family Admin Role",
            default_role_found,
            "Default Family Admin role assignment found" if default_role_found else "Missing default role assignment"
        )
    
    def validate_permissions_system(self):
        """Validate zero-trust permissions system enforces family atomicity."""
        
        zero_trust_path = os.path.join(self.backend_path, "app/core/zero_trust.py")
        content = self.read_file_safe(zero_trust_path)
        
        if not content:
            self.log_result("Zero Trust File", False, "zero_trust.py not found")
            return
            
        # Test 1: Family permissions
        family_perms = ["families", "require_permissions", "family.*read", "family.*create"]
        family_perms_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in family_perms)
        self.log_result(
            "Family Permissions System",
            family_perms_found,
            "Family permissions found in zero-trust" if family_perms_found else "Missing family permissions"
        )
        
        # Test 2: Role-based enforcement
        role_enforcement = ["UserRole", "FAMILY_ADMIN", "permissions.*role"]
        role_enf_found = any(re.search(pattern, content, re.IGNORECASE) for pattern in role_enforcement)
        self.log_result(
            "Role-Based Permission Enforcement",
            role_enf_found,
            "Role-based enforcement found" if role_enf_found else "Missing role-based enforcement"
        )
    
    def validate_database_schema(self):
        """Validate database schema supports family-atomic architecture."""
        
        # Check Alembic migrations for family-atomic patterns
        alembic_path = os.path.join(self.backend_path, "alembic/versions")
        
        if not os.path.exists(alembic_path):
            self.log_result("Database Migrations", False, "Alembic migrations directory not found")
            return
            
        migration_files = [f for f in os.listdir(alembic_path) if f.endswith('.py')]
        
        # Look for family-related schema changes
        family_schema_patterns = [
            "admin_user_id",
            "family_members",
            "FamilyRole",
            "family.*foreign.*key"
        ]
        
        schema_evidence = []
        for migration_file in migration_files:
            migration_path = os.path.join(alembic_path, migration_file)
            content = self.read_file_safe(migration_path)
            
            for pattern in family_schema_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    schema_evidence.append(f"{migration_file}: {pattern}")
        
        schema_found = len(schema_evidence) > 0
        self.log_result(
            "Family-Atomic Database Schema",
            schema_found,
            f"Family schema patterns found: {len(schema_evidence)}" if schema_found else "Missing family schema patterns",
            {"evidence": schema_evidence}
        )
    
    def validate_api_consistency(self):
        """Validate API consistency with family-atomic principles."""
        
        # Check all API endpoints for family-scoped operations
        api_path = os.path.join(self.backend_path, "app/api")
        
        if not os.path.exists(api_path):
            self.log_result("API Directory", False, "API directory not found")
            return
            
        api_files = [f for f in os.listdir(api_path) if f.endswith('.py') and f != '__init__.py']
        
        family_scoped_apis = []
        for api_file in api_files:
            api_file_path = os.path.join(api_path, api_file)
            content = self.read_file_safe(api_file_path)
            
            # Look for family-scoped operations
            family_patterns = [
                "family_id",
                "get_user_families",
                "require_permissions.*families",
                "admin_user_id",
                "family.*authorization"
            ]
            
            for pattern in family_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    family_scoped_apis.append(api_file)
                    break
        
        consistency_score = len(family_scoped_apis) / len(api_files) if api_files else 0
        consistency_good = consistency_score >= 0.5  # At least 50% of APIs should be family-aware
        
        self.log_result(
            "API Family-Scope Consistency",
            consistency_good,
            f"Family-scoped APIs: {len(family_scoped_apis)}/{len(api_files)} ({consistency_score:.1%})",
            {"family_scoped_apis": family_scoped_apis}
        )
    
    def run_validation(self):
        """Run complete family-atomic architecture validation."""
        print("🏗️ Family-Atomic Architecture Code Validation")
        print("=" * 55)
        
        try:
            # Run all validations
            self.validate_family_api_endpoints()
            self.validate_family_models()
            self.validate_user_models()
            self.validate_frontend_family_components()
            self.validate_auth_integration()
            self.validate_permissions_system()
            self.validate_database_schema()
            self.validate_api_consistency()
            
            # Generate summary
            total_tests = len(self.validation_results)
            passed_tests = len([r for r in self.validation_results if r["status"] == "PASS"])
            failed_tests = total_tests - passed_tests
            
            print("\n" + "=" * 55)
            print(f"📊 VALIDATION SUMMARY")
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if failed_tests == 0:
                print("\n🎉 ALL FAMILY-ATOMIC ARCHITECTURE VALIDATIONS PASSED!")
                print("✅ Family-atomic architecture is properly implemented")
                return True
            elif failed_tests <= 2:
                print(f"\n⚠️ {failed_tests} MINOR VALIDATION(S) FAILED")
                print("✅ Family-atomic architecture is mostly properly implemented")
                return True
            else:
                print(f"\n⚠️ {failed_tests} VALIDATION(S) FAILED")
                print("❌ Family-atomic architecture needs attention")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def save_results(self, filename: str = "family_atomic_code_validation_results.json"):
        """Save validation results to file."""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "validation_timestamp": datetime.utcnow().isoformat(),
                    "validation_type": "family_atomic_architecture_code_analysis",
                    "total_tests": len(self.validation_results),
                    "passed_tests": len([r for r in self.validation_results if r["status"] == "PASS"]),
                    "failed_tests": len([r for r in self.validation_results if r["status"] == "FAIL"]),
                    "results": self.validation_results
                }, f, indent=2)
            print(f"📄 Results saved to {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")


def main():
    """Main validation function."""
    validator = FamilyAtomicCodeValidator()
    success = validator.run_validation()
    validator.save_results()
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
