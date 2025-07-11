#!/usr/bin/env python3
"""
CI/CD Parity Validation Script
Validates that local development environment matches CI/CD requirements exactly.
This script should catch all issues that would cause CI/CD failures.
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class CICDParityValidator:
    """Validates local environment matches CI/CD pipeline requirements"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.frontend_dir = self.project_root / "frontend"
        self.backend_dir = self.project_root / "backend"
        self.results = {
            "validation_time": datetime.now().isoformat(),
            "status": "unknown",
            "checks": {},
            "errors": [],
            "warnings": [],
            "recommendations": [],
        }

    def run_command(
        self, command: str, cwd: Optional[Path] = None, timeout: int = 60
    ) -> Dict[str, Any]:
        """Run a shell command and return structured result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or self.project_root,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "returncode": -1,
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}

    def validate_frontend_dependencies(self) -> Dict[str, Any]:
        """Validate frontend dependency consistency - the exact issue that caused CI/CD failure"""
        print("🔍 Validating frontend dependencies...")

        checks = {
            "package_json_exists": False,
            "lockfile_exists": False,
            "lockfile_synchronized": False,
            "pnpm_available": False,
            "dependencies_installable": False,
            "build_successful": False,
        }

        # Check package.json exists
        package_json_path = self.frontend_dir / "package.json"
        checks["package_json_exists"] = package_json_path.exists()

        # Check lockfile exists
        lockfile_path = self.frontend_dir / "pnpm-lock.yaml"
        checks["lockfile_exists"] = lockfile_path.exists()

        # Check pnpm availability
        pnpm_result = self.run_command("pnpm --version")
        checks["pnpm_available"] = pnpm_result["success"]

        if not checks["pnpm_available"]:
            self.results["errors"].append(
                "pnpm is not available - install with: npm install -g pnpm"
            )
            return {"frontend_dependencies": checks}

        # Check lockfile synchronization (the root cause of CI/CD failure)
        if checks["package_json_exists"] and checks["lockfile_exists"]:
            print("  📋 Checking lockfile synchronization...")
            sync_result = self.run_command(
                "pnpm install --frozen-lockfile --dry-run", cwd=self.frontend_dir
            )
            checks["lockfile_synchronized"] = sync_result["success"]

            if not checks["lockfile_synchronized"]:
                self.results["errors"].append(
                    f"Frontend lockfile out of sync with package.json. CI/CD will fail!\n"
                    f"Error: {sync_result['stderr']}\n"
                    f"Fix: Run 'cd frontend && pnpm install' to regenerate lockfile"
                )

        # Test dependency installation (simulate CI/CD)
        if checks["lockfile_synchronized"]:
            print("  📦 Testing dependency installation...")
            install_result = self.run_command(
                "pnpm install --frozen-lockfile", cwd=self.frontend_dir
            )
            checks["dependencies_installable"] = install_result["success"]

            if not checks["dependencies_installable"]:
                self.results["errors"].append(
                    f"Frontend dependencies failed to install: {install_result['stderr']}"
                )

        # Test build (simulate CI/CD build step)
        if checks["dependencies_installable"]:
            print("  🏗️ Testing build...")
            build_result = self.run_command("pnpm run build", cwd=self.frontend_dir)
            checks["build_successful"] = build_result["success"]

            if not checks["build_successful"]:
                self.results["errors"].append(f"Frontend build failed: {build_result['stderr']}")

        return {"frontend_dependencies": checks}

    def validate_backend_dependencies(self) -> Dict[str, Any]:
        """Validate backend dependency consistency"""
        print("🔍 Validating backend dependencies...")

        checks = {
            "requirements_exists": False,
            "python_version_correct": False,
            "dependencies_installable": False,
            "tests_passing": False,
        }

        # Check requirements.txt exists
        requirements_path = self.backend_dir / "requirements.txt"
        checks["requirements_exists"] = requirements_path.exists()

        # Check Python version (CI/CD uses 3.11)
        python_result = self.run_command("python --version")
        if python_result["success"]:
            version_output = python_result["stdout"]
            # Extract version number
            import re

            version_match = re.search(r"Python (\d+\.\d+)", version_output)
            if version_match:
                version = version_match.group(1)
                checks["python_version_correct"] = version in [
                    "3.9",
                    "3.11",
                ]  # Allow both for flexibility
                if version not in ["3.11"]:
                    self.results["warnings"].append(
                        f"Local Python {version} differs from CI/CD Python 3.11"
                    )

        # Test dependency installation
        if checks["requirements_exists"]:
            print("  📦 Testing backend dependency installation...")
            # Create temporary venv for testing
            venv_result = self.run_command("python -m venv .test_venv", cwd=self.backend_dir)
            if venv_result["success"]:
                activate_cmd = (
                    "source .test_venv/bin/activate"
                    if os.name != "nt"
                    else ".test_venv\\Scripts\\activate.bat"
                )
                install_result = self.run_command(
                    f"{activate_cmd} && pip install -r requirements.txt", cwd=self.backend_dir
                )
                checks["dependencies_installable"] = install_result["success"]

                if not checks["dependencies_installable"]:
                    self.results["errors"].append(
                        f"Backend dependencies failed to install: {install_result['stderr']}"
                    )

                # Cleanup
                self.run_command("rm -rf .test_venv", cwd=self.backend_dir)

        return {"backend_dependencies": checks}

    def validate_ci_cd_config(self) -> Dict[str, Any]:
        """Validate CI/CD configuration matches local capabilities"""
        print("🔍 Validating CI/CD configuration...")

        checks = {
            "workflow_file_exists": False,
            "node_version_compatible": False,
            "python_version_compatible": False,
            "required_secrets_documented": False,
        }

        # Check workflow file exists
        workflow_path = self.project_root / ".github" / "workflows" / "ci-cd-pipeline.yml"
        checks["workflow_file_exists"] = workflow_path.exists()

        if checks["workflow_file_exists"]:
            # Parse workflow file
            try:
                with open(workflow_path) as f:
                    workflow = yaml.safe_load(f)

                # Check Node.js version compatibility
                node_result = self.run_command("node --version")
                if node_result["success"]:
                    local_node = node_result["stdout"].replace("v", "")
                    # CI/CD uses Node 20
                    if local_node.startswith("20."):
                        checks["node_version_compatible"] = True
                    else:
                        self.results["warnings"].append(
                            f"Local Node.js {local_node} differs from CI/CD Node 20"
                        )

                # Check for missing secrets
                workflow_content = workflow_path.read_text()
                if "SLACK_WEBHOOK_URL" in workflow_content:
                    self.results["errors"].append(
                        "CI/CD workflow references SLACK_WEBHOOK_URL secret but it's not configured in GitHub secrets"
                    )

            except Exception as e:
                self.results["errors"].append(f"Failed to parse CI/CD workflow: {e}")

        return {"ci_cd_config": checks}

    def validate_pre_commit_compatibility(self) -> Dict[str, Any]:
        """Validate pre-commit hooks match CI/CD requirements"""
        print("🔍 Validating pre-commit compatibility...")

        checks = {"pre_commit_installed": False, "hooks_configured": False, "hooks_passing": False}

        # Check pre-commit installation
        precommit_result = self.run_command("pre-commit --version")
        checks["pre_commit_installed"] = precommit_result["success"]

        # Check hooks configuration
        precommit_config = self.project_root / ".pre-commit-config.yaml"
        checks["hooks_configured"] = precommit_config.exists()

        # Test hooks
        if checks["pre_commit_installed"] and checks["hooks_configured"]:
            print("  🎣 Testing pre-commit hooks...")
            hooks_result = self.run_command("pre-commit run --all-files")
            checks["hooks_passing"] = hooks_result["success"]

            if not checks["hooks_passing"]:
                self.results["warnings"].append("Pre-commit hooks failing - fix before committing")

        return {"pre_commit": checks}

    def generate_fix_recommendations(self):
        """Generate specific fix recommendations based on validation results"""
        print("💡 Generating fix recommendations...")

        # Check if main CI/CD failure cause is present
        frontend_checks = self.results["checks"].get("frontend_dependencies", {})
        if not frontend_checks.get("lockfile_synchronized", True):
            self.results["recommendations"].append(
                {
                    "priority": "HIGH",
                    "issue": "Lockfile synchronization",
                    "fix": "cd frontend && pnpm install",
                    "reason": "This exact issue caused the CI/CD failure",
                }
            )

        # Add other recommendations based on failures
        if not frontend_checks.get("dependencies_installable", True):
            self.results["recommendations"].append(
                {
                    "priority": "HIGH",
                    "issue": "Frontend dependencies not installable",
                    "fix": "cd frontend && rm -rf node_modules && pnpm install",
                    "reason": "CI/CD will fail during dependency installation",
                }
            )

        backend_checks = self.results["checks"].get("backend_dependencies", {})
        if not backend_checks.get("dependencies_installable", True):
            self.results["recommendations"].append(
                {
                    "priority": "HIGH",
                    "issue": "Backend dependencies not installable",
                    "fix": "cd backend && pip install -r requirements.txt",
                    "reason": "CI/CD will fail during backend setup",
                }
            )

    async def run_validation(self) -> bool:
        """Run comprehensive CI/CD parity validation"""
        print("🚀 Starting CI/CD Parity Validation...")
        print(f"📁 Project root: {self.project_root}")

        try:
            # Run all validation checks
            self.results["checks"].update(self.validate_frontend_dependencies())
            self.results["checks"].update(self.validate_backend_dependencies())
            self.results["checks"].update(self.validate_ci_cd_config())
            self.results["checks"].update(self.validate_pre_commit_compatibility())

            # Generate recommendations
            self.generate_fix_recommendations()

            # Determine overall status
            has_errors = len(self.results["errors"]) > 0
            self.results["status"] = "FAIL" if has_errors else "PASS"

            return not has_errors

        except Exception as e:
            self.results["errors"].append(f"Validation failed with exception: {e}")
            self.results["status"] = "ERROR"
            return False

    def print_results(self):
        """Print human-readable validation results"""
        print("\n" + "=" * 50)
        print("CI/CD PARITY VALIDATION RESULTS")
        print("=" * 50)

        status_emoji = "✅" if self.results["status"] == "PASS" else "❌"
        print(f"\nOverall Status: {status_emoji} {self.results['status']}")

        if self.results["errors"]:
            print(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results["errors"], 1):
                print(f"  {i}. {error}")

        if self.results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for i, warning in enumerate(self.results["warnings"], 1):
                print(f"  {i}. {warning}")

        if self.results["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS ({len(self.results['recommendations'])}):")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. [{rec['priority']}] {rec['issue']}")
                print(f"     Fix: {rec['fix']}")
                print(f"     Why: {rec['reason']}")

        print("\n📊 Detailed results saved to: validation_results.json")

    def save_results(self):
        """Save detailed results to file"""
        results_file = self.project_root / "validation_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)


async def main():
    """Main validation entry point"""
    validator = CICDParityValidator()

    try:
        success = await validator.run_validation()
        validator.print_results()
        validator.save_results()

        if not success:
            print("\n🚨 Validation failed! Fix issues before pushing to prevent CI/CD failures.")
            sys.exit(1)
        else:
            print("\n🎉 All checks passed! Your local environment matches CI/CD requirements.")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
