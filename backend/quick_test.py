#!/usr/bin/env python3
"""
Targeted fixes for the most critical syntax errors in Pathfinder backend
"""

import subprocess
import sys
from pathlib import Path


def test_file_syntax(filepath):
    """Test if a file has valid Python syntax."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        compile(content, str(filepath), "exec")
        return True, None
    except SyntaxError as e:
        return False, str(e)


def main():
    """Fix critical files one by one."""
    backend_dir = Path("/Users/vedprakashmishra/pathfinder/backend")

    print("🔧 Testing individual files...")

    # Test the file we just fixed
    admin_broken = backend_dir / "app" / "api" / "admin_broken.py"
    valid, error = test_file_syntax(admin_broken)
    if valid:
        print(f"✅ {admin_broken.name} - Fixed!")
    else:
        print(f"❌ {admin_broken.name} - Still has error: {error}")

    # Test a few other critical files
    test_files = ["app/api/exports.py", "app/api/auth.py", "app/main.py"]

    for filepath in test_files:
        full_path = backend_dir / filepath
        if full_path.exists():
            valid, error = test_file_syntax(full_path)
            if valid:
                print(f"✅ {filepath} - OK")
            else:
                print(f"❌ {filepath} - Error: {error}")

    # Run the validation to see current status
    print("\n🔍 Running import validation...")
    try:
        result = subprocess.run(
            [sys.executable, "local_validation.py"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )

        # Count successful imports
        output_lines = result.stdout.split("\n")
        success_count = sum(1 for line in output_lines if line.strip().startswith("✅"))
        fail_count = sum(1 for line in output_lines if line.strip().startswith("❌"))

        print(f"📊 Import Status: {success_count} successful, {fail_count} failed")

        if result.returncode == 0:
            print("🎉 All imports working!")
        else:
            print(f"⚠️ Still have {fail_count} failing imports")

    except Exception as e:
        print(f"❌ Error running validation: {e}")


if __name__ == "__main__":
    main()
