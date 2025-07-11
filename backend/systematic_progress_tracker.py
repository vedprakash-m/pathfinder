#!/usr/bin/env python3
"""
Systematic fix approach for Pathfinder backend syntax errors
Fix core files first, then expand to secondary files
"""

import subprocess
import sys
from pathlib import Path


def test_syntax(filepath):
    """Test if a file has valid Python syntax."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        compile(content, str(filepath), "exec")
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def test_import(module_path):
    """Test if a module can be imported."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_path}"],
            capture_output=True,
            text=True,
            cwd="/Users/vedprakashmishra/pathfinder/backend",
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


def run_validation():
    """Run local validation and return results."""
    try:
        result = subprocess.run(
            [sys.executable, "local_validation.py"],
            capture_output=True,
            text=True,
            cwd="/Users/vedprakashmishra/pathfinder/backend",
        )

        output_lines = result.stdout.split("\n")
        success_count = sum(1 for line in output_lines if line.strip().startswith("✅"))
        fail_count = sum(1 for line in output_lines if line.strip().startswith("❌"))

        return success_count, fail_count, result.returncode == 0
    except Exception as e:
        return 0, 0, False


def main():
    """Track progress systematically."""
    print("🔧 Systematic Fix Progress Tracker")
    print("=" * 50)

    # Priority files to fix
    priority_files = [
        ("app/main.py", "app.main"),
        ("app/core/dependencies.py", "app.core.dependencies"),
        ("app/api/auth.py", "app.api.auth"),
        ("app/api/exports.py", "app.api.exports"),
        ("app/api/admin_broken.py", "app.api.admin_broken"),
    ]

    print("🎯 Testing priority files:")
    fixed_count = 0

    for file_path, module_path in priority_files:
        full_path = Path("/Users/vedprakashmishra/pathfinder/backend") / file_path

        # Test syntax
        syntax_ok, syntax_error = test_syntax(full_path)

        # Test import
        import_ok, import_error = test_import(module_path)

        if syntax_ok and import_ok:
            print(f"✅ {file_path} - WORKING")
            fixed_count += 1
        elif syntax_ok:
            print(
                f"⚠️ {file_path} - Syntax OK, Import Error: {import_error.split(':')[0] if ':' in import_error else import_error}"
            )
        else:
            print(f"❌ {file_path} - Syntax Error: {syntax_error}")

    print(f"\n📊 Priority Files Status: {fixed_count}/{len(priority_files)} working")

    # Run overall validation
    success, fail, passed = run_validation()
    print(f"📊 Overall Validation: {success} success, {fail} fail")

    return fixed_count, success


if __name__ == "__main__":
    main()
