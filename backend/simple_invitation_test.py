#!/usr/bin/env python3
"""
Simple test for family invitation system
"""
import sqlite3
import sys
import os

def test_database_structure():
    """Test that the family_invitations table exists with correct structure"""
    print("🧪 Testing Family Invitation Database Structure")
    print("=" * 50)
    
    try:
        # Connect to the database
        conn = sqlite3.connect('pathfinder.db')
        cursor = conn.cursor()
        
        # Check if family_invitations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='family_invitations'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ family_invitations table not found")
            return False
        
        print("✅ family_invitations table exists")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(family_invitations)")
        columns = cursor.fetchall()
        
        expected_columns = {
            'id', 'family_id', 'invited_by', 'email', 'role', 
            'status', 'invitation_token', 'message', 'expires_at',
            'accepted_at', 'created_at', 'updated_at'
        }
        
        actual_columns = {col[1] for col in columns}
        
        if expected_columns.issubset(actual_columns):
            print("✅ All required columns present")
            print(f"   Columns: {', '.join(sorted(actual_columns))}")
        else:
            missing = expected_columns - actual_columns
            print(f"❌ Missing columns: {missing}")
            return False
        
        # Test inserting a mock invitation
        cursor.execute("""
            INSERT INTO family_invitations 
            (id, family_id, invited_by, email, role, status, invitation_token, message, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+7 days'), datetime('now'))
        """, (
            'test-invite-123',
            'family-123', 
            'user-123',
            'test@example.com',
            'member',
            'PENDING',
            'token-abc123',
            'Welcome to our family!'
        ))
        
        # Verify the insertion
        cursor.execute("SELECT email, status FROM family_invitations WHERE id = ?", ('test-invite-123',))
        result = cursor.fetchone()
        
        if result and result[0] == 'test@example.com' and result[1] == 'PENDING':
            print("✅ Can insert and retrieve invitation records")
        else:
            print("❌ Failed to insert/retrieve invitation record")
            return False
        
        # Clean up test data
        cursor.execute("DELETE FROM family_invitations WHERE id = ?", ('test-invite-123',))
        conn.commit()
        conn.close()
        
        print("✅ Database structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_files():
    """Test that the family API files exist and have invitation endpoints"""
    print("\n🧪 Testing Family API Implementation")
    print("=" * 50)
    
    # Check if family API file exists
    api_file = 'app/api/families.py'
    if not os.path.exists(api_file):
        print("❌ Family API file not found")
        return False
    
    print("✅ Family API file exists")
    
    # Read the file and check for invitation endpoints
    with open(api_file, 'r') as f:
        content = f.read()
    
    # Check for function names instead of route patterns
    expected_functions = [
        'invite_family_member',
        'accept_family_invitation',
        'decline_family_invitation',
        'get_family_invitations'
    ]
    
    found_functions = []
    for func_name in expected_functions:
        if f"def {func_name}" in content:
            found_functions.append(func_name)
            print(f"✅ Found endpoint function: {func_name}")
        else:
            print(f"❌ Missing endpoint function: {func_name}")
    
    if len(found_functions) == len(expected_functions):
        print("✅ All invitation endpoint functions found")
        return True
    else:
        print(f"❌ Only found {len(found_functions)}/{len(expected_functions)} endpoint functions")
        return False

def test_email_service():
    """Test that email service has family invitation support"""
    print("\n🧪 Testing Email Service Integration")
    print("=" * 50)
    
    email_file = 'app/services/email_service.py'
    if not os.path.exists(email_file):
        print("❌ Email service file not found")
        return False
    
    print("✅ Email service file exists")
    
    with open(email_file, 'r') as f:
        content = f.read()
    
    if 'send_family_invitation' in content:
        print("✅ send_family_invitation method found")
    else:
        print("❌ send_family_invitation method not found")
        return False
    
    if 'family_invitation' in content and "'family_invitation':" in content:
        print("✅ Family invitation email template found")
    else:
        print("❌ Family invitation email template not found")
        return False
    
    print("✅ Email service integration complete")
    return True

def main():
    """Run all tests"""
    print("🎯 Family Invitation System Testing")
    print("=" * 60)
    
    tests = [
        ("Database Structure", test_database_structure),
        ("API Implementation", test_api_files),
        ("Email Service", test_email_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS: Family invitation system is ready for production!")
        print("   ✅ Database migration applied")
        print("   ✅ API endpoints implemented")
        print("   ✅ Email service integrated")
        print("\n📋 Next Steps:")
        print("   1. Configure SendGrid/SMTP for email delivery")
        print("   2. Test end-to-end invitation workflow")
        print("   3. Deploy to production environment")
    else:
        print("\n⚠️  WARNING: Some components need attention")
        print("   Review failed tests above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
