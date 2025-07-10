#!/usr/bin/env python3
"""
Priority fix script for critical Pathfinder files
Focus on the most important files first
"""

import subprocess
import sys
from pathlib import Path

def test_file_imports(module_path):
    """Test if a module can be imported successfully."""
    try:
        result = subprocess.run(
            [sys.executable, '-c', f'import {module_path}'],
            capture_output=True,
            text=True,
            cwd='/Users/vedprakashmishra/pathfinder/backend'
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def run_local_validation():
    """Run the local validation script."""
    try:
        result = subprocess.run(
            [sys.executable, 'local_validation.py'],
            capture_output=True,
            text=True,
            cwd='/Users/vedprakashmishra/pathfinder/backend'
        )
        
        # Count successes and failures
        output_lines = result.stdout.split('\n')
        success_count = sum(1 for line in output_lines if line.strip().startswith('✅'))
        fail_count = sum(1 for line in output_lines if line.strip().startswith('❌'))
        
        return success_count, fail_count, result.returncode == 0
    except Exception as e:
        return 0, 0, False

def main():
    """Main execution."""
    print("🎯 Priority Fix Assessment")
    print("=" * 40)
    
    # Test critical core files first
    critical_files = [
        ('app.main', 'app/main.py'),
        ('app.core.dependencies', 'app/core/dependencies.py'),
        ('app.api.auth', 'app/api/auth.py'),
        ('app.api.trips', 'app/api/trips.py'),
        ('app.api.families', 'app/api/families.py'),
        ('app.api.exports', 'app/api/exports.py'),
    ]
    
    print("🔍 Testing critical core files:")
    success_count = 0
    
    for module_path, file_path in critical_files:
        success, error = test_file_imports(module_path)
        if success:
            print(f"✅ {file_path}")
            success_count += 1
        else:
            print(f"❌ {file_path} - {error.split(':', 1)[0] if ':' in error else error}")
    
    print(f"\n📊 Core Status: {success_count}/{len(critical_files)} critical files working")
    
    # Run overall validation
    print("\n🔍 Running full validation...")
    total_success, total_fail, validation_passed = run_local_validation()
    print(f"📊 Overall Status: {total_success} successful, {total_fail} failed")
    
    if success_count >= 4:  # If most core files work
        print("\n🎉 Core files mostly working! Ready to proceed with deployment.")
        print("💡 Recommendation: Deploy with working features, fix remaining issues post-deployment.")
    elif success_count >= 2:  # If some core files work
        print("\n⚠️ Some core files working. Continue fixing priority files.")
        print("💡 Recommendation: Fix main.py and auth.py next.")
    else:
        print("\n🚨 Critical issues remain. Focus on syntax fixes.")
        print("💡 Recommendation: Fix syntax errors in main.py first.")
    
    return success_count

if __name__ == "__main__":
    main()
