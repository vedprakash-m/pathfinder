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


def check_dependency_isolation():
    """Check if all required dependencies are properly declared in requirements.txt."""
    print_colored("\n🔍 DEPENDENCY ISOLATION VALIDATION", 'blue')
    
    # Get currently imported modules from test runs
    import_script = """
import sys
import importlib
import pkgutil

# Test modules that are likely to have external dependencies
critical_test_modules = [
    'tests.test_monitoring',
    'tests.test_ai_service', 
    'tests.test_performance',
    'app.core.monitoring',
    'app.services.ai_service',
    'app.core.security'
]

imported_packages = set()

for module_name in critical_test_modules:
    try:
        module = importlib.import_module(module_name)
        # Get module's dependencies
        if hasattr(module, '__file__') and module.__file__:
            with open(module.__file__, 'r') as f:
                content = f.read()
                import re
                # Find import statements
                imports = re.findall(r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
                from_imports = re.findall(r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)', content, re.MULTILINE)
                all_imports = imports + from_imports
                for imp in all_imports:
                    # More comprehensive list of standard library and built-in modules to exclude
                    standard_lib = {
                        'os', 'sys', 'json', 're', 'time', 'datetime', 'typing', 'pathlib', 
                        'unittest', 'asyncio', 'collections', 'contextvars', 'tempfile', 
                        'uuid', 'enum', 'dataclasses', 'functools', 'contextlib', 'logging',
                        'abc', 'copy', 'itertools', 'warnings', 'weakref', 'threading',
                        'multiprocessing', 'concurrent', 'socket', 'urllib', 'http', 'email',
                        'mimetypes', 'base64', 'hashlib', 'hmac', 'secrets', 'ssl', 'calendar',
                        'decimal', 'fractions', 'random', 'statistics', 'math', 'cmath'
                    }
                    if not imp.startswith('app') and not imp.startswith('tests') and imp not in standard_lib:
                        imported_packages.add(imp)
        print(f'✅ {module_name}: checked')
    except Exception as e:
        print(f'❌ {module_name}: {str(e)[:80]}')

print(f'\\nExternal packages detected: {sorted(imported_packages)}')

# Check if these are in requirements.txt
with open('requirements.txt', 'r') as f:
    requirements_content = f.read()

missing_deps = []
# Special mapping for packages that have different import vs install names
package_mapping = {
    'jwt': 'python-jose',  # PyJWT vs python-jose
    'PIL': 'Pillow',
    'yaml': 'PyYAML'
}

for pkg in imported_packages:
    # Check the package or its mapped name
    check_name = package_mapping.get(pkg, pkg)
    if check_name not in requirements_content and pkg not in requirements_content:
        missing_deps.append(pkg)

if missing_deps:
    print(f'\\n❌ MISSING DEPENDENCIES: {missing_deps}')
    sys.exit(1)
else:
    print(f'\\n✅ All detected dependencies are declared in requirements.txt')
"""
    
    result = subprocess.run([
        "python3", "-c", import_script
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print_colored("✅ Dependency isolation check - PASSED", 'green')
        if result.stdout.strip():
            print(f"{result.stdout.strip()}")
        return True
    else:
        print_colored("❌ Dependency isolation check - FAILED", 'red')
        print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return False


def check_ci_cd_environment_parity():
    """Simulate CI/CD environment conditions to catch parity issues."""
    print_colored("\n🔍 CI/CD ENVIRONMENT PARITY CHECK", 'blue')
    
    # Check for pytest markers that might be missing
    marker_check_script = """
import pytest
import sys
import os

# Check if pytest.ini has proper marker configuration
if os.path.exists('pytest.ini'):
    with open('pytest.ini', 'r') as f:
        content = f.read()
        if 'markers' not in content:
            print('❌ pytest.ini missing markers configuration')
            print('This causes "Unknown pytest.mark" warnings in CI/CD')
            sys.exit(1)
        else:
            print('✅ pytest.ini has markers configuration')
else:
    print('❌ pytest.ini not found')
    sys.exit(1)

# Test that critical test files can be collected
test_files = [
    'tests/test_monitoring.py',
    'tests/test_ai_service.py', 
    'tests/test_ai_service_unit.py',
    'tests/test_ai_tasks_alt_simple.py'
]

for test_file in test_files:
    if os.path.exists(test_file):
        # Try to collect tests from this file
        exit_code = pytest.main(['--collect-only', test_file, '-q'])
        if exit_code != 0:
            print(f'❌ Test collection failed for {test_file}')
            sys.exit(1)
        else:
            print(f'✅ {test_file}: collection OK')
    else:
        print(f'❌ {test_file}: not found')

print('\\n✅ All critical test files can be collected successfully')
"""
    
    result = subprocess.run([
        "python3", "-c", marker_check_script
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print_colored("✅ CI/CD environment parity check - PASSED", 'green')
        if result.stdout.strip():
            print(f"{result.stdout.strip()}")
        return True
    else:
        print_colored("❌ CI/CD environment parity check - FAILED", 'red')
        print(f"Error: {result.stderr.strip()}")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
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

    # Dependency isolation check
    dependency_isolation_success = check_dependency_isolation()

    if not dependency_isolation_success:
        print_colored("\n🚨 CRITICAL: Dependency isolation issues detected!", 'red')
        print_colored("Fix dependency issues before running other tests", 'yellow')
        print_colored("Run: python comprehensive_e2e_validation.py for detailed analysis", 'blue')
        return 1

    # CI/CD environment parity check
    ci_cd_parity_success = check_ci_cd_environment_parity()

    if not ci_cd_parity_success:
        print_colored("\n🚨 CRITICAL: CI/CD environment parity issues detected!", 'red')
        print_colored("Fix environment issues before running other tests", 'yellow')
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
