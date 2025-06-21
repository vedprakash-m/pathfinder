#!/usr/bin/env python3
"""
Comprehensive local validation script to catch issues before CI/CD.
This script runs the same checks that CI/CD would run to prevent failures.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    else:
        print(f"❌ {description} - FAILED")
        print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return False

def main():
    """Run comprehensive local validation."""
    print("🚀 Starting Comprehensive Local Validation")
    print("=" * 50)
    
    # Change to backend directory
    os.chdir("/Users/vedprakashmishra/pathfinder/backend")
    
    # List of validation steps
    validation_steps = [
        # 1. Install dependencies
        (["pip", "install", "-r", "requirements.txt"], "Installing dependencies"),
        
        # 2. Run specific failing test first
        (["python", "-m", "pytest", "tests/test_ai_service.py::test_ai_service_generate_itinerary", "-v"], 
         "Running the specific CI/CD failing test"),
        
        # 3. Run all AI service tests
        (["python", "-m", "pytest", "tests/test_ai_service.py", "-v"], 
         "Running all tests in test_ai_service.py"),
        
        # 4. Check for test collection issues (no execution)
        (["python", "-m", "pytest", "tests/", "--collect-only"], 
         "Checking test collection for all tests"),
        
        # 5. Run tests with proper markers
        (["python", "-m", "pytest", "tests/", "-m", "not e2e and not performance", "-v", "--tb=short"], 
         "Running unit and integration tests (excluding e2e and performance)"),
        
        # 6. Check for import errors
        (["python", "-c", "from app.services.ai_service import AIService; print('AI Service imports successfully')"], 
         "Checking AI service imports"),
        
        # 7. Check for syntax errors
        (["python", "-m", "py_compile", "app/services/ai_service.py"], 
         "Checking AI service syntax"),
        
        # 8. Run a broader test to catch integration issues
        (["python", "-m", "pytest", "tests/test_ai_service*.py", "-v", "--tb=short"], 
         "Running all AI service related tests"),
    ]
    
    results = []
    
    for cmd, description in validation_steps:
        success = run_command(cmd, description)
        results.append((description, success))
        
        # If a critical step fails, we might want to continue to see all issues
        if not success and "specific CI/CD failing test" in description:
            print(f"⚠️  Critical test failed, but continuing to identify all issues...")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All validations passed! Ready for CI/CD")
        return 0
    else:
        print("🚨 Some validations failed. Fix issues before pushing to CI/CD")
        return 1

if __name__ == "__main__":
    sys.exit(main())
