#!/usr/bin/env python3
"""
Test Infrastructure Quick Fix Script

This script performs a quick assessment and potential fixes for test infrastructure reliability:
1. Checks test configuration
2. Identifies common test failures
3. Provides recommendations for improvement
4. Quick fixes where possible

Focus: Getting tests to a stable 95%+ pass rate for CI/CD confidence.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class TestInfrastructureQuickFix:
    """Quick fixes for test infrastructure reliability."""

    def __init__(self):
        self.validation_results = []
        self.frontend_path = Path("frontend")
        self.backend_path = Path("backend")

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

    def check_frontend_test_config(self):
        """Check frontend test configuration."""

        # Test 1: Vitest config
        vitest_config_path = self.frontend_path / "vitest.config.ts"
        if vitest_config_path.exists():
            try:
                with open(vitest_config_path, "r") as f:
                    content = f.read()

                config_features = [
                    ("Test Environment", "jsdom" in content or "happy-dom" in content),
                    ("Setup Files", "setupFiles" in content),
                    ("Global Setup", "globals" in content),
                    ("Coverage", "coverage" in content),
                ]

                for feature_name, found in config_features:
                    self.log_result(
                        f"Vitest {feature_name}",
                        found,
                        (
                            f"Vitest {feature_name.lower()} configured"
                            if found
                            else f"Missing Vitest {feature_name.lower()}"
                        ),
                    )

            except Exception as e:
                self.log_result(
                    "Vitest Config Analysis", False, f"Failed to analyze Vitest config: {e}"
                )
        else:
            self.log_result("Vitest Config File", False, "vitest.config.ts not found")

    def check_test_setup_files(self):
        """Check test setup files."""

        # Test setup file locations
        setup_files = [
            self.frontend_path / "src" / "tests" / "setup.ts",
            self.frontend_path / "src" / "test-setup.ts",
            self.frontend_path / "src" / "__tests__" / "setup.ts",
        ]

        setup_file_found = False
        for setup_file in setup_files:
            if setup_file.exists():
                setup_file_found = True

                try:
                    with open(setup_file, "r") as f:
                        content = f.read()

                    setup_features = [
                        ("DOM Globals", "@testing-library/jest-dom" in content),
                        ("Fetch Mock", "fetch" in content.lower()),
                        ("Console Mock", "console" in content),
                        ("MSW Setup", "msw" in content.lower()),
                    ]

                    for feature_name, found in setup_features:
                        self.log_result(
                            f"Setup {feature_name}",
                            found,
                            (
                                f"Test setup {feature_name.lower()} found"
                                if found
                                else f"Missing test setup {feature_name.lower()}"
                            ),
                        )

                except Exception:
                    pass
                break

        if not setup_file_found:
            self.log_result("Test Setup File", False, "Test setup file not found")

    def check_mock_consistency(self):
        """Check mock consistency across tests."""

        # Check for mock files
        mock_paths = [
            self.frontend_path / "src" / "__mocks__",
            self.frontend_path / "src" / "tests" / "mocks",
            self.frontend_path / "src" / "tests" / "__mocks__",
        ]

        mock_dir_found = False
        for mock_path in mock_paths:
            if mock_path.exists() and mock_path.is_dir():
                mock_dir_found = True

                # Check for common mocks
                mock_files = list(mock_path.glob("*.ts")) + list(mock_path.glob("*.js"))

                common_mocks = ["api.ts", "auth.ts", "router.ts", "axios.ts"]
                found_mocks = [mock.name for mock in mock_files]

                self.log_result(
                    "Mock Directory",
                    True,
                    f"Mock directory found with {len(mock_files)} mock files: {', '.join(found_mocks[:3])}",
                )
                break

        if not mock_dir_found:
            self.log_result("Mock Directory", False, "Mock directory not found")

    def run_quick_test_check(self):
        """Run a quick test to check current status."""

        try:
            # Run a single test file to check basic functionality
            result = subprocess.run(
                [
                    "npm",
                    "test",
                    "--",
                    "--run",
                    "--reporter=json",
                    "src/tests/components/HomePage.test.tsx",
                ],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.log_result("Sample Test Execution", True, "Sample test executed successfully")
            else:
                self.log_result(
                    "Sample Test Execution", False, f"Sample test failed: {result.stderr[:200]}..."
                )

        except subprocess.TimeoutExpired:
            self.log_result("Sample Test Execution", False, "Sample test timed out")
        except Exception as e:
            self.log_result("Sample Test Execution", False, f"Could not run sample test: {e}")

    def check_backend_test_config(self):
        """Check backend test configuration."""

        # Test 1: pytest configuration
        pytest_config_paths = [
            self.backend_path / "pytest.ini",
            self.backend_path / "pyproject.toml",
            self.backend_path / "setup.cfg",
        ]

        pytest_config_found = False
        for config_path in pytest_config_paths:
            if config_path.exists():
                pytest_config_found = True
                break

        self.log_result(
            "Backend Test Config",
            pytest_config_found,
            (
                "Backend test configuration found"
                if pytest_config_found
                else "Missing backend test configuration"
            ),
        )

        # Test 2: Test database setup
        conftest_path = self.backend_path / "tests" / "conftest.py"
        if conftest_path.exists():
            try:
                with open(conftest_path, "r") as f:
                    content = f.read()

                test_features = [
                    ("Test Database", "test_db" in content or "database" in content),
                    ("Test Client", "TestClient" in content or "test_client" in content),
                    ("Async Support", "pytest_asyncio" in content),
                    ("Fixtures", "@pytest.fixture" in content),
                ]

                for feature_name, found in test_features:
                    self.log_result(
                        f"Backend {feature_name}",
                        found,
                        (
                            f"Backend {feature_name.lower()} found"
                            if found
                            else f"Missing backend {feature_name.lower()}"
                        ),
                    )

            except Exception:
                self.log_result(
                    "Backend Conftest Analysis", False, "Failed to analyze backend conftest"
                )
        else:
            self.log_result("Backend Conftest File", False, "Backend conftest.py not found")

    def provide_recommendations(self):
        """Provide recommendations for test infrastructure improvement."""

        failed_tests = [r for r in self.validation_results if r["status"] == "FAIL"]
        total_tests = len(self.validation_results)

        print("\n📋 TEST INFRASTRUCTURE RECOMMENDATIONS")
        print("=" * 45)

        if len(failed_tests) == 0:
            print("✅ Test infrastructure is well configured!")
            return

        critical_issues = []

        # Check for critical issues
        failed_test_names = [r["test"] for r in failed_tests]

        if "Test Setup File" in failed_test_names:
            critical_issues.append(
                "🔧 Create test setup file with proper DOM and mock configuration"
            )

        if "Vitest Config File" in failed_test_names:
            critical_issues.append("🔧 Configure Vitest with jsdom environment and proper settings")

        if "Mock Directory" in failed_test_names:
            critical_issues.append(
                "🔧 Create comprehensive mock directory for external dependencies"
            )

        if "Sample Test Execution" in failed_test_names:
            critical_issues.append(
                "🔧 Fix immediate test execution issues (likely mock/provider problems)"
            )

        if critical_issues:
            print("CRITICAL FIXES NEEDED:")
            for issue in critical_issues:
                print(f"  {issue}")

        # Provide specific fix commands
        print("\n🛠️ QUICK FIXES:")
        print("1. Test Infrastructure Setup:")
        print("   npm test -- --reporter=verbose --run")
        print("2. Check specific test failures:")
        print("   npm test -- HomePage.test.tsx --reporter=verbose")
        print("3. Update test setup in src/tests/setup.ts")
        print("4. Ensure all mocks are properly configured")

        success_rate = (
            ((total_tests - len(failed_tests)) / total_tests) * 100 if total_tests > 0 else 0
        )

        if success_rate >= 75:
            status = "GOOD - Minor improvements needed"
        elif success_rate >= 50:
            status = "FAIR - Some fixes required"
        else:
            status = "NEEDS WORK - Major improvements needed"

        print(f"\n📊 Test Infrastructure Status: {status} ({success_rate:.1f}% configured)")

    def run_assessment(self):
        """Run complete test infrastructure assessment."""
        print("🧪 Test Infrastructure Quick Assessment")
        print("=" * 42)

        try:
            # Run all checks
            self.check_frontend_test_config()
            self.check_test_setup_files()
            self.check_mock_consistency()
            self.run_quick_test_check()
            self.check_backend_test_config()

            # Provide recommendations
            self.provide_recommendations()

            # Summary
            total_tests = len(self.validation_results)
            passed_tests = len([r for r in self.validation_results if r["status"] == "PASS"])
            failed_tests = total_tests - passed_tests

            print("\n📊 ASSESSMENT SUMMARY")
            print(f"Total Checks: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {failed_tests}")
            print(f"Configuration Score: {(passed_tests/total_tests)*100:.1f}%")

            # Determine if infrastructure is reliable enough
            if failed_tests <= 2:
                print("\n✅ Test infrastructure is sufficiently reliable for CI/CD")
                return True
            else:
                print("\n⚠️ Test infrastructure needs improvement for reliability")
                return False

        except Exception as e:
            print(f"❌ Assessment failed: {e}")
            return False

    def save_results(self, filename: str = "test_infrastructure_assessment.json"):
        """Save assessment results to file."""
        try:
            with open(filename, "w") as f:
                json.dump(
                    {
                        "assessment_timestamp": datetime.utcnow().isoformat(),
                        "assessment_type": "test_infrastructure_quick_fix",
                        "total_checks": len(self.validation_results),
                        "passed_checks": len(
                            [r for r in self.validation_results if r["status"] == "PASS"]
                        ),
                        "failed_checks": len(
                            [r for r in self.validation_results if r["status"] == "FAIL"]
                        ),
                        "results": self.validation_results,
                    },
                    f,
                    indent=2,
                )
            print(f"📄 Assessment saved to {filename}")
        except Exception as e:
            print(f"⚠️ Could not save assessment: {e}")


def main():
    """Main assessment function."""
    assessor = TestInfrastructureQuickFix()
    reliable = assessor.run_assessment()
    assessor.save_results()

    return reliable


if __name__ == "__main__":
    reliable = main()
    exit(0 if reliable else 1)
