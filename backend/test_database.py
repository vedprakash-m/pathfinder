#!/usr/bin/env python3
"""
Direct database test for family invitations
"""
import sqlite3
from pathlib import Path

# Path to the database
db_path = Path(__file__).parent / "pathfinder.db"


def test_database():
    """Test the database directly"""
    print("🧪 Testing Family Invitations Database")
    print("=" * 50)

    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if family_invitations table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='family_invitations'
        """
        )

        table_exists = cursor.fetchone()

        if table_exists:
            print("✅ family_invitations table exists")

            # Check table structure
            cursor.execute("PRAGMA table_info(family_invitations)")
            columns = cursor.fetchall()

            print("   Table columns:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")

            expected_columns = [
                "id",
                "family_id",
                "invited_by",
                "email",
                "role",
                "status",
                "invitation_token",
                "message",
                "expires_at",
                "accepted_at",
                "created_at",
                "updated_at",
            ]

            actual_columns = [col[1] for col in columns]
            missing_columns = [
                col for col in expected_columns if col not in actual_columns
            ]

            if not missing_columns:
                print("✅ All expected columns present")
            else:
                print(f"❌ Missing columns: {missing_columns}")

        else:
            print("❌ family_invitations table does not exist")

            # Check what tables do exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print("   Existing tables:")
            for table in tables:
                print(f"   - {table[0]}")

        # Check if families table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='families'
        """
        )

        families_exists = cursor.fetchone()
        print(
            f"{'✅' if families_exists else '❌'} families table {'exists' if families_exists else 'missing'}"
        )

        # Check alembic version
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='alembic_version'
        """
        )

        alembic_exists = cursor.fetchone()
        if alembic_exists:
            cursor.execute("SELECT version_num FROM alembic_version")
            version = cursor.fetchone()
            print(f"✅ Database version: {version[0] if version else 'Unknown'}")
        else:
            print("❌ No alembic version table found")

        conn.close()
        return table_exists is not None

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_database()

    if not success:
        print("\n💡 To fix this, run: alembic upgrade head")
    else:
        print("\n🎉 Database structure looks good!")
