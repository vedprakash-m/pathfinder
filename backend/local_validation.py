#!/usr/bin/env python3
"""
Enhanced Local Validation Script - Legacy Wrapper

This script now serves as a bridge to the comprehensive E2E validation.
It includes the original AI-focused checks plus critical import validation.

For complete validation, use: comprehensive_e2e_validation.py
"""

import subprocess
import sys
import os
from pathlib import Path


def print_colored(message: str, color: str):
    """Print colored output."""
    colors = {
        'green': '\033[92m',
        'red': '\033[91m', 
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{message}{colors['end']}")


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print_colored(f"✅ {description} - PASSED", 'green')
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    else:
        print_colored(f"❌ {description} - FAILED", 'red')
        print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return False


def check_critical_imports():
    """Check critical imports that caused CI/CD failures."""
    print_colored("\n🔍 COMPREHENSIVE IMPORT VALIDATION", 'blue')
    
    # Auto-discover ALL API modules instead of hardcoding
    api_modules = []
    import os
    api_dir = "app/api"
    if os.path.exists(api_dir):
        for file in os.listdir(api_dir):
            if file.endswith('.py') and file != '__init__.py':
                module_name = f"app.api.{file[:-3]}"
                api_modules.append(module_name)
    
    core_modules = [
        'app.core.dependencies',
        'app.main'
    ]
    
    critical_modules = api_modules + core_modules
    
    import_script = f"""
import sys
failed = []
api_modules = {api_modules}
core_modules = {core_modules}
modules = api_modules + core_modules

print(f'🔍 Testing {{len(modules)}} modules ({{len(api_modules)}} API + {{len(core_modules)}} core):')

for module_name in modules:
    try:
        __import__(module_name)
        print(f'✅ {{module_name}}: OK')
    except Exception as e:
        print(f'❌ {{module_name}}: {{str(e)[:80]}}...')
        failed.append((module_name, str(e)))

if failed:
    print(f'\\nFAILED: {{len(failed)}} critical modules')
    for module, error in failed:
        print(f'  {{module}}: {{error[:100]}}...')
    sys.exit(1)
else:
    print(f'\\n🎉 All {{len(modules)}} critical modules importing successfully!')
    print(f'   - API modules tested: {{len(api_modules)}}')
    print(f'   - Core modules tested: {{len(core_modules)}}')
"""
    
    result = subprocess.run([
        "python3", "-c", import_script
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print_colored("✅ Critical imports - PASSED", 'green')
        print(result.stdout)
        return True
    else:
        print_colored("❌ Critical imports - FAILED", 'red') 
        print(result.stderr)
        print(result.stdout)
        return False


def main():
    """Run enhanced local validation."""
    print_colored("🚀 Enhanced Local Validation (Legacy + Critical Checks)", 'blue')
    print("=" * 70)

    # Change to backend directory
    os.chdir("/Users/vedprakashmishra/pathfinder/backend")

    # Critical import check first (addresses CI/CD failure root cause)
    import_success = check_critical_imports()
    
    if not import_success:
        print_colored("\n🚨 CRITICAL: Import failures detected!", 'red')
        print_colored("Fix import errors before running other tests", 'yellow')
        print_colored("Run: python comprehensive_e2e_validation.py for detailed analysis", 'blue')
        return 1

    # Original validation steps (AI-focused)
    validation_steps = [
        # 1. Install dependencies
        (["pip3", "install", "-r", "requirements.txt"], "Installing dependencies"),
        
        # 2. Test collection (catches import errors in tests)
        (["python3", "-m", "pytest", "tests/", "--collect-only", "-q"], 
         "Test Collection (Import Error Detection)"),
        
        # 3. Run specific failing test first
        (["python3", "-m", "pytest", "tests/test_ai_service.py::test_ai_service_generate_itinerary", "-v"],
         "Running the specific CI/CD failing test"),
         
        # 4. Run all AI service tests
        (["python3", "-m", "pytest", "tests/test_ai_service.py", "-v"],
         "Running all tests in test_ai_service.py"),
         
        # 5. Run unit and integration tests  
        (["python3", "-m", "pytest", "tests/", "-m", "not e2e and not performance", 
          "-v", "--tb=short", "--maxfail=3"],
         "Running unit and integration tests (excluding e2e and performance)"),
         
        # 6. Check for import errors
        (["python3", "-c", 
          "from app.services.ai_service import AIService; print('AI Service imports successfully')"],
         "Checking AI service imports"),
         
        # 7. Check for syntax errors
        (["python3", "-m", "py_compile", "app/services/ai_service.py"],
         "Checking AI service syntax"),
         
        # 8. Run broader AI tests
        (["python3", "-m", "pytest", "tests/test_ai_service*.py", "-v", "--tb=short"],
         "Running all AI service related tests"),
    ]

    results = []

    for cmd, description in validation_steps:
        success = run_command(cmd, description)
        results.append((description, success))

        # If a critical step fails, note it but continue
        if not success and "specific CI/CD failing test" in description:
            print_colored("⚠️  Critical test failed, but continuing to identify all issues...", 'yellow')

    # Summary
    print("\n" + "=" * 70)
    print_colored("📊 VALIDATION SUMMARY", 'blue')
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total and import_success:
        print_colored("🎉 All validations passed! Ready for CI/CD", 'green')
        return 0
    else:
        print_colored("🚨 Some validations failed. Fix issues before pushing to CI/CD", 'red')
        print_colored("\n💡 For comprehensive analysis, run:", 'blue')
        print_colored("   python comprehensive_e2e_validation.py", 'blue')
        return 1


if __name__ == "__main__":
    sys.exit(main())
