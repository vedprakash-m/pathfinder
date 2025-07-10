#!/usr/bin/env python3
"""
Comprehensive fix for common Python code quality issues.
"""

import os
import re
from pathlib import Path


def fix_ruff_issues(file_path: str) -> None:
    """Fix common ruff issues."""
    with open(file_path, "r") as f:
        content = f.read()

    # Fix B904: raise ... from err
    content = re.sub(
        r"(\s+)raise\s+(\w+Error\([^)]+\))\s*$", r"\1raise \2 from e", content, flags=re.MULTILINE
    )

    # Fix E712: == False/True comparisons
    content = re.sub(r"(\w+\.?\w*)\s*==\s*False", r"not \1", content)
    content = re.sub(r"(\w+\.?\w*)\s*==\s*True", r"\1", content)

    # Fix F401: unused imports (basic patterns)
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        # Skip obvious unused imports that follow common patterns
        if (
            line.strip().startswith("import ")
            and any(unused in line for unused in ["sys", "os"])
            and "sys" not in content[content.find(line) + len(line) :]
            and "os" not in content[content.find(line) + len(line) :]
        ):
            continue
        fixed_lines.append(line)

    modified_content = "\n".join(fixed_lines)

    if modified_content != content:
        with open(file_path, "w") as f:
            f.write(modified_content)
        print(f"Fixed ruff issues in {file_path}")


def fix_type_issues(file_path: str) -> None:
    """Fix type annotation issues."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Add basic imports if not present
    imports_to_add = []
    if "Dict" in content and "from typing import" not in content:
        imports_to_add.append("Dict")
    if "List" in content and "from typing import" not in content:
        imports_to_add.append("List")
    if "Optional" in content and "from typing import" not in content:
        imports_to_add.append("Optional")
    if "Any" in content and "from typing import" not in content:
        imports_to_add.append("Any")

    if imports_to_add and "from typing import" not in content:
        import_line = f"from typing import {', '.join(set(imports_to_add))}\n"
        content = import_line + "\n" + content

    # Fix function signatures missing return types (conservative)
    def add_return_type(match):
        indent = match.group(1)
        def_part = match.group(2)
        args_part = match.group(3)
        colon_space = match.group(4)

        # Skip if already has return type
        if "->" in def_part + args_part:
            return match.group(0)

        # Add None return type for common patterns
        if "__init__" in def_part or "setup" in def_part or "cleanup" in def_part:
            return f"{indent}{def_part}{args_part} -> None{colon_space}"

        return match.group(0)  # Don't modify others

    content = re.sub(r"(\s+)(def\s+\w+)(\([^)]*\))(\s*):", add_return_type, content)

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Fixed type issues in {file_path}")


def main():
    """Main function to fix issues across files."""
    backend_dir = Path("/Users/vedprakashmishra/pathfinder/backend")

    # Get all Python files, excluding some problematic directories
    exclude_dirs = {
        "venv",
        "venv-3.11",
        "__pycache__",
        ".git",
        "htmlcov",
        "migration_backup",
        "alembic",
    }

    python_files = []
    for root, dirs, files in os.walk(backend_dir):
        # Remove excluded directories from the search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    print(f"Found {len(python_files)} Python files to process")

    # Process files
    for file_path in python_files[:20]:  # Process first 20 files as a test
        try:
            print(f"Processing: {file_path}")
            fix_ruff_issues(str(file_path))
            fix_type_issues(str(file_path))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue


if __name__ == "__main__":
    main()
