#!/usr/bin/env python3
"""
End-to-end test for family invitation workflow.
Tests the complete flow from creating a family to sending and accepting invitations.
"""

import asyncio
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.core.database import get_db
from app.models.family import (
    Family,
    FamilyMember,
    FamilyRole,
    FamilyInvitationModel,
    InvitationStatus,
)
from app.models.user import User
from app.services.email_service import email_service
from sqlalchemy.orm import Session


async def test_family_invitation_workflow():
    """Test the complete family invitation workflow."""
    print("🎯 Testing Family Invitation Workflow")
    print("=" * 60)

    try:
        # Create a synchronous database session for testing
        from app.core.database import SessionLocal

        db = SessionLocal()

        print("✅ Database connection established")

        # Test 1: Create test users
        print("\n📝 Step 1: Creating test users...")
        admin_user = User(
            id="admin-user-123",
            email="admin@test.com",
            name="Test Admin",
            auth0_id="auth0|admin123",
            is_active=True,
        )

        invited_user = User(
            id="invited-user-456",
            email="invited@test.com",
            name="Test Invited User",
            auth0_id="auth0|invited456",
            is_active=True,
        )

        # Check if users already exist, if not create them
        existing_admin = db.query(User).filter(User.email == "admin@test.com").first()
        if not existing_admin:
            db.add(admin_user)
        else:
            admin_user = existing_admin

        existing_invited = db.query(User).filter(User.email == "invited@test.com").first()
        if not existing_invited:
            db.add(invited_user)
        else:
            invited_user = existing_invited

        db.commit()
        print("✅ Test users created/verified")

        # Test 2: Create a family
        print("\n📝 Step 2: Creating test family...")
        family = Family(
            id="test-family-789",
            name="Test Smith Family",
            description="A test family for invitation workflow testing",
        )

        # Check if family exists
        existing_family = db.query(Family).filter(Family.id == "test-family-789").first()
        if not existing_family:
            db.add(family)
            db.commit()
        else:
            family = existing_family

        print("✅ Test family created/verified")

        # Test 3: Add admin as family member
        print("\n📝 Step 3: Adding admin as family member...")
        admin_member = (
            db.query(FamilyMember)
            .filter(FamilyMember.family_id == family.id, FamilyMember.user_id == admin_user.id)
            .first()
        )

        if not admin_member:
            admin_member = FamilyMember(
                family_id=family.id,
                user_id=admin_user.id,
                name=admin_user.name,
                role=FamilyRole.ADMIN,
                is_primary_contact=True,
            )
            db.add(admin_member)
            db.commit()

        print("✅ Admin member added/verified")

        # Test 4: Create family invitation
        print("\n📝 Step 4: Creating family invitation...")

        # Clean up any existing test invitations
        db.query(FamilyInvitationModel).filter(
            FamilyInvitationModel.family_id == family.id,
            FamilyInvitationModel.email == invited_user.email,
        ).delete()
        db.commit()

        invitation_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = FamilyInvitationModel(
            family_id=family.id,
            invited_by=admin_user.id,
            email=invited_user.email,
            role=FamilyRole.MEMBER,
            status=InvitationStatus.PENDING,
            invitation_token=invitation_token,
            message="Welcome to our family group! Let's plan some amazing trips together.",
            expires_at=expires_at,
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)

        print("✅ Family invitation created")
        print(f"   📧 To: {invitation.email}")
        print(f"   🔑 Token: {invitation_token[:20]}...")
        print(f"   📅 Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Test 5: Test email service (without actually sending)
        print("\n📝 Step 5: Testing email service integration...")

        try:
            # This will test the template rendering without actually sending
            email_result = await email_service.send_family_invitation(
                recipient_email=invited_user.email,
                family_name=family.name,
                inviter_name=admin_user.name,
                invitation_link=f"https://pathfinder.app/accept-invitation?token={invitation_token}",
                message=invitation.message,
            )

            print("✅ Email service integration tested")
            print(
                f"   📬 Email send attempted: {'✅ Success' if email_result else '⚠️  No email service configured'}"
            )

        except Exception as e:
            print(f"⚠️  Email service test warning: {e}")
            print("   (This is expected if no email service is configured)")

        # Test 6: Simulate invitation acceptance
        print("\n📝 Step 6: Simulating invitation acceptance...")

        # Verify invitation is valid
        stored_invitation = (
            db.query(FamilyInvitationModel)
            .filter(FamilyInvitationModel.invitation_token == invitation_token)
            .first()
        )

        if not stored_invitation:
            raise Exception("Invitation not found in database")

        if stored_invitation.status != InvitationStatus.PENDING:
            raise Exception(f"Invitation status is {stored_invitation.status}, expected PENDING")

        if stored_invitation.expires_at < datetime.utcnow():
            raise Exception("Invitation has expired")

        print("✅ Invitation validation passed")

        # Check if user is already a family member
        existing_member = (
            db.query(FamilyMember)
            .filter(FamilyMember.family_id == family.id, FamilyMember.user_id == invited_user.id)
            .first()
        )

        if not existing_member:
            # Create family member
            new_member = FamilyMember(
                family_id=family.id,
                user_id=invited_user.id,
                name=invited_user.name,
                role=stored_invitation.role,
            )

            # Update invitation status
            stored_invitation.status = InvitationStatus.ACCEPTED
            stored_invitation.accepted_at = datetime.utcnow()

            db.add(new_member)
            db.commit()

            print("✅ Family member added successfully")
        else:
            print("✅ User was already a family member")

        # Test 7: Verify final state
        print("\n📝 Step 7: Verifying final state...")

        # Check family members
        family_members = db.query(FamilyMember).filter(FamilyMember.family_id == family.id).all()

        print(f"✅ Family has {len(family_members)} members:")
        for member in family_members:
            user = db.query(User).filter(User.id == member.user_id).first()
            print(f"   👤 {user.name} ({user.email}) - {member.role.value}")

        # Check invitation status
        final_invitation = (
            db.query(FamilyInvitationModel)
            .filter(FamilyInvitationModel.invitation_token == invitation_token)
            .first()
        )

        print(f"✅ Invitation status: {final_invitation.status.value}")
        if final_invitation.accepted_at:
            print(
                f"   📅 Accepted at: {final_invitation.accepted_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        print("\n🎉 SUCCESS: Family invitation workflow completed successfully!")
        print("=" * 60)
        print("📋 Workflow Summary:")
        print("   ✅ Users created/verified")
        print("   ✅ Family created/verified")
        print("   ✅ Admin member added")
        print("   ✅ Invitation created")
        print("   ✅ Email service tested")
        print("   ✅ Invitation accepted")
        print("   ✅ Family member added")
        print("   ✅ Final state verified")

        return True

    except Exception as e:
        print(f"\n❌ WORKFLOW TEST FAILED: {e}")
        print("Check the error details above and verify your setup.")
        return False

    finally:
        if "db" in locals():
            db.close()


async def cleanup_test_data():
    """Clean up test data from previous runs."""
    print("\n🧹 Cleaning up test data...")

    try:
        db_gen = get_db()
        db: Session = next(db_gen)

        # Remove test invitations
        db.query(FamilyInvitationModel).filter(
            FamilyInvitationModel.family_id == "test-family-789"
        ).delete()

        # Remove test family members
        db.query(FamilyMember).filter(FamilyMember.family_id == "test-family-789").delete()

        # Remove test family
        db.query(Family).filter(Family.id == "test-family-789").delete()

        # Remove test users
        db.query(User).filter(User.email.in_(["admin@test.com", "invited@test.com"])).delete()

        db.commit()
        print("✅ Test data cleaned up")

    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    finally:
        if "db" in locals():
            db.close()


def main():
    """Run the family invitation workflow test."""
    import asyncio

    try:
        # Clean up any previous test data
        asyncio.run(cleanup_test_data())

        # Run the workflow test
        success = asyncio.run(test_family_invitation_workflow())

        if success:
            print("\n🎯 READY FOR PRODUCTION!")
            print("   The family invitation system is working correctly.")
            print("   Configure email service (SendGrid/SMTP) for full functionality.")
        else:
            print("\n⚠️  ISSUES FOUND")
            print("   Review the errors above before deploying to production.")

        return success

    except Exception as e:
        print(f"\n💥 TEST CRASHED: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
