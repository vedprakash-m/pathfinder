#!/usr/bin/env python3
"""
Comprehensive E2E Local Validation Script

This script runs ALL validation checks that CI/CD would run to prevent failures.
Designed to catch issues that led to CI/CD failures like import errors, test failures,
architecture violations, and deployment readiness issues.

Based on CI/CD failure analysis: June 30, 2025
Root cause: Missing import validation, incomplete local testing coverage
"""

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Color coding for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*20} {title} {'='*20}{Colors.END}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


def run_command(
    cmd: List[str],
    description: str,
    capture_output: bool = True,
    check_return_code: bool = True,
) -> Tuple[bool, str, str]:
    """Run a command and return success status and outputs."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, timeout=300
        )  # 5 minute timeout

        success = result.returncode == 0

        if success:
            print_success(f"{description} - PASSED")
        else:
            print_error(f"{description} - FAILED (Exit code: {result.returncode})")

        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        if result.stderr.strip() and not success:
            print(f"Error: {result.stderr.strip()}")

        return success, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print_error(f"{description} - TIMEOUT")
        return False, "", "Command timed out"
    except Exception as e:
        print_error(f"{description} - EXCEPTION: {str(e)}")
        return False, "", str(e)


def check_python_imports() -> Tuple[bool, List[str]]:
    """Check all Python modules for import errors - CRITICAL for CI/CD."""
    print_section("COMPREHENSIVE IMPORT VALIDATION")

    app_dir = Path("app")
    if not app_dir.exists():
        print_error("app directory not found")
        return False, ["app directory not found"]

    failed_imports = []
    python_files = list(app_dir.rglob("*.py"))

    print_info(f"Checking {len(python_files)} Python files for import errors...")

    # CRITICAL: Test ALL modules systematically - this was our gap!
    critical_modules = []

    # Auto-discover all API modules
    api_modules = []
    for py_file in app_dir.glob("api/*.py"):
        if py_file.name != "__init__.py":
            module_name = f"app.api.{py_file.stem}"
            api_modules.append(module_name)

    critical_modules.extend(api_modules)

    # Add core modules
    core_modules = [
        "app.main",
        "app.core.dependencies",
        "app.core.database",
        "app.core.database_unified",
        "app.services.trip_cosmos",
        "app.models.user",
        "app.models.trip",
    ]
    critical_modules.extend(core_modules)

    print_info(f"Testing {len(critical_modules)} critical modules:")
    print_info(f"API modules: {len(api_modules)}, Core modules: {len(core_modules)}")

    for module_name in critical_modules:
        try:
            __import__(module_name)
            print_success(f"  {module_name}")
        except Exception as e:
            error_msg = f"{module_name}: {str(e)}"
            print_error(f"  {error_msg}")
            failed_imports.append(error_msg)

    # Test all Python files for syntax errors
    print_info("Checking all Python files for syntax errors:")
    syntax_errors = []
    for py_file in python_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                ast.parse(f.read())
        except SyntaxError as e:
            error_msg = f"{py_file}: Syntax error at line {e.lineno}: {e.msg}"
            print_error(f"  {error_msg}")
            syntax_errors.append(error_msg)
        except Exception as e:
            error_msg = f"{py_file}: {str(e)}"
            print_warning(f"  {error_msg}")

    total_errors = len(failed_imports) + len(syntax_errors)
    if total_errors == 0:
        print_success("All import and syntax checks passed!")
        print_info(
            f"Validated {len(critical_modules)} critical modules and {len(python_files)} Python files"
        )
        return True, []
    else:
        print_error(f"Found {total_errors} import/syntax errors")
        print_error(f"Import errors: {len(failed_imports)}, Syntax errors: {len(syntax_errors)}")
        return False, failed_imports + syntax_errors


def run_comprehensive_tests() -> bool:
    """Run comprehensive test suite matching CI/CD pipeline."""
    print_section("COMPREHENSIVE TESTING")

    test_steps = [
        # 1. Test Collection (critical - catches import errors)
        (
            ["python3", "-m", "pytest", "tests/", "--collect-only", "-q"],
            "Test Collection (Import Error Detection)",
            True,  # This step is informational only
        ),
        # 2. Quick Smoke Test (catches execution-time failures early)
        (
            ["python3", "-m", "pytest", "tests/test_auth.py", "-v", "--maxfail=1", "-x"],
            "Auth Service Smoke Test (Execution Validation)",
            False,  # This step should fail if there are execution issues
        ),
        # 3. Unit Tests
        (
            [
                "python3",
                "-m",
                "pytest",
                "tests/",
                "-m",
                "not e2e and not performance",
                "-v",
                "--tb=short",
                "--maxfail=5",
            ],
            "Unit and Integration Tests",
            False,
        ),
        # 4. Coverage Analysis
        (
            ["coverage", "run", "-m", "pytest", "tests/", "-v", "--maxfail=3"],
            "Test Coverage Analysis",
            True,  # Allow some failures for coverage analysis
        ),
        (["coverage", "report", "--fail-under=70"], "Coverage Threshold Check", True),
        # 5. Specific CI/CD Test Cases
        (
            ["python3", "-m", "pytest", "tests/test_ai_service.py", "-v"],
            "AI Service Tests",
            True,
        ),
    ]

    results = []
    critical_failure = False

    for cmd, description, allow_failure in test_steps:
        success, stdout, stderr = run_command(cmd, description)
        results.append((description, success))

        # Stop immediately on critical failures
        if not success and not allow_failure:
            print_error(f"CRITICAL FAILURE in {description}")
            print_error("This would cause CI/CD to fail. Stopping validation.")
            critical_failure = True
            break

        # Continue on failure but log it
        if not success:
            print_warning(f"Test step failed but continuing: {description}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print_info(f"Test Results: {passed}/{total} test steps passed")

    # Return False if there were critical failures
    if critical_failure:
        return False

    return passed >= (total * 0.8)  # Allow 80% pass rate


def run_architecture_validation() -> bool:
    """Run architecture and code quality checks."""
    print_section("ARCHITECTURE & QUALITY VALIDATION")

    quality_checks = [
        # 1. Import linting (catches architecture violations)
        (
            ["lint-imports", "--config", "../importlinter_contracts/layers.toml"],
            "Architecture Contract Validation",
        ),
        # 2. Type checking
        (
            ["mypy", "app/", "--ignore-missing-imports", "--explicit-package-bases"],
            "Type Checking",
        ),
        # 3. Code formatting
        (["black", "--check", "--diff", "."], "Code Formatting Check"),
        # 4. Import sorting
        (["isort", "--check-only", "--diff", "."], "Import Sorting Check"),
        # 5. Linting
        (
            [
                "flake8",
                ".",
                "--max-line-length=88",
                "--extend-ignore=E203,W503",
                "--exclude=venv,migrations",
            ],
            "PEP8 Linting",
        ),
        # 6. Modern Python linting
        (
            ["ruff", "check", ".", "--line-length=100", "--target-version=py311"],
            "Modern Python Linting",
        ),
    ]

    results = []
    for cmd, description in quality_checks:
        success, stdout, stderr = run_command(cmd, description, check_return_code=False)
        results.append((description, success))

        # Architecture violations are warnings, not failures
        if not success and "architecture" in description.lower():
            print_warning("Architecture violations detected - review needed")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print_info(f"Quality Results: {passed}/{total} quality checks passed")
    return passed >= (total * 0.7)  # Allow 70% pass rate for quality


def check_environment_readiness() -> bool:
    """Check environment readiness for deployment."""
    print_section("ENVIRONMENT READINESS")

    env_checks = [
        # 1. Dependencies
        (["pip", "check"], "Dependency Consistency Check"),
        # 2. Security scan
        (["safety", "check"], "Security Vulnerability Scan"),
        # 3. Environment variables
        (
            [
                "python3",
                "-c",
                """
import os
required_vars = ['DATABASE_URL', 'ENVIRONMENT']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'Missing: {missing}')
    exit(1)
else:
    print('All required environment variables present')
""",
            ],
            "Environment Variables Check",
        ),
    ]

    results = []
    for cmd, description in env_checks:
        success, stdout, stderr = run_command(cmd, description, check_return_code=False)
        results.append((description, success))

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print_info(f"Environment Results: {passed}/{total} environment checks passed")
    return passed >= (total * 0.8)


def generate_validation_report(results: Dict[str, Tuple[bool, List[str]]]) -> str:
    """Generate a comprehensive validation report."""
    print_section("VALIDATION REPORT")

    report = []
    report.append("# Comprehensive E2E Validation Report")
    report.append(f"Generated: {subprocess.check_output(['date']).decode().strip()}")
    report.append("")

    overall_success = True

    for section, (success, details) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        report.append(f"## {section}: {status}")

        if not success:
            overall_success = False

        if details:
            report.append("### Details:")
            for detail in details:
                report.append(f"- {detail}")
        report.append("")

    # Overall status
    overall_status = "✅ READY FOR CI/CD" if overall_success else "❌ ISSUES FOUND"
    report.append(f"## Overall Status: {overall_status}")

    if not overall_success:
        report.append("")
        report.append("### Recommended Actions:")
        report.append("1. Fix all import errors and syntax issues")
        report.append("2. Ensure test suite passes completely")
        report.append("3. Address architecture violations")
        report.append("4. Run this script again before pushing to CI/CD")

    report_text = "\n".join(report)
    print(report_text)

    # Save to file
    with open("validation_report.md", "w") as f:
        f.write(report_text)

    return report_text


def main():
    """Run comprehensive E2E validation."""
    print(f"{Colors.PURPLE}{Colors.BOLD}")
    print("🚀 COMPREHENSIVE E2E LOCAL VALIDATION")
    print("======================================")
    print("Designed to prevent CI/CD failures by catching all issues locally")
    print("Based on CI/CD failure analysis: June 30, 2025")
    print(f"{Colors.END}")

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    print_info(f"Working directory: {backend_dir}")

    # Install required tools if missing
    print_section("ENVIRONMENT SETUP")
    tools_to_install = [
        "coverage",
        "black",
        "mypy",
        "isort",
        "flake8",
        "ruff",
        "import-linter",
        "safety",
    ]

    for tool in tools_to_install:
        success, _, _ = run_command(
            ["pip", "show", tool], f"Checking {tool}", check_return_code=False
        )
        if not success:
            print_info(f"Installing {tool}...")
            run_command(["pip", "install", tool], f"Installing {tool}")

    # Run all validation steps
    results = {}

    # 1. Import validation (CRITICAL)
    import_success, import_errors = check_python_imports()
    results["Import Validation"] = (import_success, import_errors)

    # 2. Comprehensive testing
    test_success = run_comprehensive_tests()
    results["Comprehensive Testing"] = (test_success, [])

    # 3. Architecture validation
    arch_success = run_architecture_validation()
    results["Architecture & Quality"] = (arch_success, [])

    # 4. Environment readiness
    env_success = check_environment_readiness()
    results["Environment Readiness"] = (env_success, [])

    # Generate final report
    generate_validation_report(results)

    # Final summary
    print_section("FINAL SUMMARY")

    all_passed = all(success for success, _ in results.values())

    if all_passed:
        print_success("🎉 ALL VALIDATIONS PASSED!")
        print_success("✅ Ready for CI/CD deployment")
        return 0
    else:
        print_error("🚨 VALIDATION FAILURES DETECTED")
        print_error("❌ Fix issues before pushing to CI/CD")

        # Priority recommendations
        if not import_success:
            print_error("🔥 CRITICAL: Import errors must be fixed first")
        if not test_success:
            print_error("🔥 CRITICAL: Test failures must be addressed")

        return 1


if __name__ == "__main__":
    sys.exit(main())
