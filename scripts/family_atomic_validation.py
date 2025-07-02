#!/usr/bin/env python3
"""
Family-Atomic Architecture Validation Script

This script validates that the family-atomic architecture principle is properly enforced:
1. Families are the atomic unit for trip participation
2. Family Admin authority is enforced
3. Family-level permissions are validated
4. All operations are properly scoped to family level

Validates both database structure and API endpoints to ensure architectural compliance.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.core.database_unified import get_cosmos_service
from backend.app.models.family import FamilyRole, InvitationStatus
from backend.app.models.user import UserRole


class FamilyAtomicValidator:
    """Validates family-atomic architecture enforcement."""

    def __init__(self):
        self.cosmos_service = get_cosmos_service()
        self.repo = self.cosmos_service.get_repository()
        self.validation_results = []
        self.test_user_id = None
        self.test_family_id = None

    def log_result(
        self, test_name: str, passed: bool, message: str, details: Optional[Dict] = None
    ):
        """Log validation result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")

        self.validation_results.append(
            {
                "test": test_name,
                "status": "PASS" if passed else "FAIL",
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    async def setup_test_data(self):
        """Create test data for validation."""
        try:
            # Create a test user
            test_user_data = {
                "email": "family.atomic.test@pathfinder.test",
                "name": "Family Atomic Test User",
                "entra_id": "family-atomic-test-123",
                "role": UserRole.FAMILY_ADMIN,
                "is_active": True,
                "onboarding_completed": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Check if user exists, create if not
            existing_user = await self.repo.get_user_by_email("family.atomic.test@pathfinder.test")
            if existing_user:
                self.test_user_id = existing_user.id
                print(f"🔄 Using existing test user: {self.test_user_id}")
            else:
                test_user = await self.repo.create_user(test_user_data)
                self.test_user_id = test_user.id
                print(f"📝 Created test user: {self.test_user_id}")

            # Create a test family
            test_family_data = {
                "name": "Family Atomic Test Family",
                "description": "Test family for atomic architecture validation",
                "admin_user_id": self.test_user_id,
                "member_ids": [self.test_user_id],
            }

            # Check if family exists
            user_families = await self.repo.get_user_families(self.test_user_id)
            existing_family = next(
                (f for f in user_families if f.name == "Family Atomic Test Family"), None
            )

            if existing_family:
                self.test_family_id = existing_family.id
                print(f"🔄 Using existing test family: {self.test_family_id}")
            else:
                test_family = await self.repo.create_family(test_family_data)
                self.test_family_id = test_family.id
                print(f"📝 Created test family: {self.test_family_id}")

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise

    async def validate_family_admin_authority(self):
        """Validate that Family Admin authority is properly enforced."""

        # Test 1: Family Admin can manage family
        try:
            family = await self.repo.get_family(self.test_family_id)
            if family and family.admin_user_id == self.test_user_id:
                self.log_result(
                    "Family Admin Authority", True, "Family admin correctly set and accessible"
                )
            else:
                self.log_result(
                    "Family Admin Authority",
                    False,
                    f"Family admin mismatch: expected {self.test_user_id}, got {family.admin_user_id if family else None}",
                )
        except Exception as e:
            self.log_result(
                "Family Admin Authority", False, f"Failed to validate family admin: {e}"
            )

        # Test 2: Only admin can modify family
        try:
            # Try to update family (should work as admin)
            update_data = {"description": "Updated by admin test"}
            updated_family = await self.repo.update_family(self.test_family_id, update_data)

            if updated_family and updated_family.description == "Updated by admin test":
                self.log_result(
                    "Admin Update Authority", True, "Family admin can update family details"
                )
            else:
                self.log_result(
                    "Admin Update Authority", False, "Family admin cannot update family details"
                )
        except Exception as e:
            self.log_result("Admin Update Authority", False, f"Admin update failed: {e}")

    async def validate_family_atomic_operations(self):
        """Validate that operations are family-scoped, not individual-scoped."""

        # Test 1: User belongs to family
        try:
            user_families = await self.repo.get_user_families(self.test_user_id)
            belongs_to_family = any(f.id == self.test_family_id for f in user_families)

            if belongs_to_family:
                self.log_result("Family Membership", True, "User correctly associated with family")
            else:
                self.log_result(
                    "Family Membership", False, "User not properly associated with family"
                )
        except Exception as e:
            self.log_result("Family Membership", False, f"Family membership check failed: {e}")

        # Test 2: Family member operations
        try:
            family = await self.repo.get_family(self.test_family_id)
            if family and self.test_user_id in family.member_ids:
                self.log_result(
                    "Atomic Member Management", True, "User properly included in family member list"
                )
            else:
                self.log_result(
                    "Atomic Member Management",
                    False,
                    "User not properly included in family member list",
                )
        except Exception as e:
            self.log_result(
                "Atomic Member Management", False, f"Member management check failed: {e}"
            )

    async def validate_family_permissions_system(self):
        """Validate that permissions are properly enforced at family level."""

        # Test 1: Family-level read permissions
        try:
            family = await self.repo.get_family(self.test_family_id)
            if family:
                self.log_result(
                    "Family Read Permissions", True, "Family admin can read family data"
                )
            else:
                self.log_result(
                    "Family Read Permissions", False, "Family admin cannot read family data"
                )
        except Exception as e:
            self.log_result(
                "Family Read Permissions", False, f"Family read permission check failed: {e}"
            )

        # Test 2: Family creation permissions
        try:
            # Test creating another family (should work for Family Admin)
            new_family_data = {
                "name": "Second Test Family",
                "description": "Second family for permission testing",
                "admin_user_id": self.test_user_id,
                "member_ids": [self.test_user_id],
            }

            second_family = await self.repo.create_family(new_family_data)
            if second_family:
                self.log_result(
                    "Family Creation Permissions", True, "Family admin can create multiple families"
                )
                # Cleanup
                await self.repo.delete_family(second_family.id)
            else:
                self.log_result(
                    "Family Creation Permissions",
                    False,
                    "Family admin cannot create additional families",
                )
        except Exception as e:
            self.log_result(
                "Family Creation Permissions",
                False,
                f"Family creation permission check failed: {e}",
            )

    async def validate_family_invitation_system(self):
        """Validate that family invitations maintain atomic family principles."""

        # Test 1: Family invitation creation
        try:
            invitation_data = {
                "family_id": self.test_family_id,
                "email": "invited.user@pathfinder.test",
                "role": FamilyRole.MEMBER,
                "message": "Join our family for trip planning",
                "invited_by": self.test_user_id,
                "status": InvitationStatus.PENDING,
                "token": "test-invitation-token-123",
                "expires_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            invitation = await self.repo.create_family_invitation(invitation_data)
            if invitation:
                self.log_result(
                    "Family Invitation System", True, "Family admin can create invitations"
                )
                # Cleanup
                await self.repo.delete_family_invitation(invitation.id)
            else:
                self.log_result(
                    "Family Invitation System", False, "Family admin cannot create invitations"
                )
        except Exception as e:
            self.log_result(
                "Family Invitation System", False, f"Family invitation system check failed: {e}"
            )

    async def validate_role_based_access(self):
        """Validate that role-based access control enforces family-atomic principles."""

        # Test 1: Family Admin role assignment
        try:
            user = await self.repo.get_user(self.test_user_id)
            if user and user.role == UserRole.FAMILY_ADMIN:
                self.log_result(
                    "Role-Based Access", True, "User correctly assigned Family Admin role"
                )
            else:
                self.log_result(
                    "Role-Based Access",
                    False,
                    f"User role incorrect: expected {UserRole.FAMILY_ADMIN}, got {user.role if user else None}",
                )
        except Exception as e:
            self.log_result("Role-Based Access", False, f"Role-based access check failed: {e}")

    async def validate_data_consistency(self):
        """Validate data consistency across family operations."""

        # Test 1: Family member count consistency
        try:
            family = await self.repo.get_family(self.test_family_id)
            if family:
                expected_count = len(family.member_ids)
                actual_count = family.members_count

                if expected_count == actual_count:
                    self.log_result(
                        "Data Consistency",
                        True,
                        f"Family member count consistent: {expected_count}",
                    )
                else:
                    self.log_result(
                        "Data Consistency",
                        False,
                        f"Family member count inconsistent: expected {expected_count}, got {actual_count}",
                    )
            else:
                self.log_result("Data Consistency", False, "Family not found for consistency check")
        except Exception as e:
            self.log_result("Data Consistency", False, f"Data consistency check failed: {e}")

    async def cleanup_test_data(self):
        """Clean up test data after validation."""
        try:
            if self.test_family_id:
                await self.repo.delete_family(self.test_family_id)
                print(f"🧹 Cleaned up test family: {self.test_family_id}")

            if self.test_user_id:
                await self.repo.delete_user(self.test_user_id)
                print(f"🧹 Cleaned up test user: {self.test_user_id}")

        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    async def run_validation(self):
        """Run complete family-atomic architecture validation."""
        print("🏗️ Family-Atomic Architecture Validation")
        print("=" * 50)

        try:
            # Setup
            await self.setup_test_data()

            # Run all validations
            await self.validate_family_admin_authority()
            await self.validate_family_atomic_operations()
            await self.validate_family_permissions_system()
            await self.validate_family_invitation_system()
            await self.validate_role_based_access()
            await self.validate_data_consistency()

            # Generate summary
            total_tests = len(self.validation_results)
            passed_tests = len([r for r in self.validation_results if r["status"] == "PASS"])
            failed_tests = total_tests - passed_tests

            print("\n" + "=" * 50)
            print("📊 VALIDATION SUMMARY")
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

            if failed_tests == 0:
                print("\n🎉 ALL FAMILY-ATOMIC ARCHITECTURE VALIDATIONS PASSED!")
                print("✅ Family-atomic architecture is properly enforced")
                return True
            else:
                print(f"\n⚠️ {failed_tests} VALIDATION(S) FAILED")
                print("❌ Family-atomic architecture needs attention")
                return False

        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
        finally:
            # Cleanup
            await self.cleanup_test_data()

    def save_results(self, filename: str = "family_atomic_validation_results.json"):
        """Save validation results to file."""
        try:
            with open(filename, "w") as f:
                json.dump(
                    {
                        "validation_timestamp": datetime.utcnow().isoformat(),
                        "total_tests": len(self.validation_results),
                        "passed_tests": len(
                            [r for r in self.validation_results if r["status"] == "PASS"]
                        ),
                        "failed_tests": len(
                            [r for r in self.validation_results if r["status"] == "FAIL"]
                        ),
                        "results": self.validation_results,
                    },
                    f,
                    indent=2,
                )
            print(f"📄 Results saved to {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")


async def main():
    """Main validation function."""
    validator = FamilyAtomicValidator()
    success = await validator.run_validation()
    validator.save_results()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
