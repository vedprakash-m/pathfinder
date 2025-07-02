#!/usr/bin/env python3
"""
Schema Validation Test Script
Tests that our enhanced local validation can catch schema compatibility issues
"""

import subprocess
import sys
import os

def test_schema_validation():
    """Test that our schema validation catches the CI/CD issue"""
    print("🧪 Testing Schema Validation Detection")
    print("=" * 50)
    
    # Create a temporary test file with the problematic schema
    test_content = '''
from app.models.user import UserCreate

def test_broken_user_create():
    """This should fail schema validation"""
    user_data = UserCreate(
        email="test@example.com",
        auth0_id="auth0|test123",  # Missing required entra_id
        name="Test User"
    )
    assert user_data.email == "test@example.com"
'''
    
    with open('temp_broken_test.py', 'w') as f:
        f.write(test_content)
    
    try:
        # Test with the broken schema
        print("   🔍 Testing UserCreate with missing entra_id...")
        result = subprocess.run([
            'python3', '-c', '''
import sys
sys.path.append("/Users/vedprakashmishra/pathfinder/backend")
from app.models.user import UserCreate

try:
    # This should fail
    user_data = UserCreate(
        email="test@example.com",
        auth0_id="auth0|test123",  # Missing required entra_id
        name="Test User"
    )
    print("❌ FAILURE: Schema validation should have caught this!")
except Exception as e:
    print("✅ SUCCESS: Schema validation correctly caught the issue")
    print(f"   Error: {str(e)[:100]}...")
'''
        ], capture_output=True, text=True)
        
        print(result.stdout.strip())
        
        # Test with correct schema
        print("\n   🔍 Testing UserCreate with correct schema...")
        result2 = subprocess.run([
            'python3', '-c', '''
import sys
sys.path.append("/Users/vedprakashmishra/pathfinder/backend")
from app.models.user import UserCreate

try:
    # This should work
    user_data = UserCreate(
        email="test@example.com",
        entra_id="entra|test123",  # Required field included
        auth0_id="auth0|test123",   # Optional legacy field
        name="Test User"
    )
    print("✅ SUCCESS: Correct schema validation passed")
except Exception as e:
    print(f"❌ FAILURE: Correct schema should work: {e}")
'''
        ], capture_output=True, text=True)
        
        print(result2.stdout.strip())
        
    finally:
        # Clean up
        if os.path.exists('temp_broken_test.py'):
            os.remove('temp_broken_test.py')

if __name__ == "__main__":
    os.chdir("/Users/vedprakashmishra/pathfinder/backend")
    test_schema_validation()
