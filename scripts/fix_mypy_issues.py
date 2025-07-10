#!/usr/bin/env python3
"""
Fix common mypy issues in the codebase.
"""

import re
from pathlib import Path


def fix_function_return_types(file_path: str) -> None:
    """Add return type annotations to functions missing them."""
    with open(file_path, "r") as f:
        content = f.read()

    # Pattern for functions missing return type annotations
    # This will catch patterns like: "def function_name(...)" but not "def function_name(...) -> ReturnType:"
    pattern = r"(\s+)(def\s+\w+\([^)]*\))(\s*):(\s*\n)"

    def replacement(match):
        indent = match.group(1)
        func_def = match.group(2)
        colon_space = match.group(3)
        newline = match.group(4)

        # Skip if it already has a return type
        if "->" in func_def:
            return match.group(0)

        # Skip __init__ methods as they should return None
        if "__init__" in func_def:
            return f"{indent}{func_def} -> None{colon_space}:{newline}"

        # For now, add None return type for safety
        return f"{indent}{func_def} -> None{colon_space}:{newline}"

    modified_content = re.sub(pattern, replacement, content)

    if modified_content != content:
        with open(file_path, "w") as f:
            f.write(modified_content)
        print(f"Fixed return types in {file_path}")


def fix_dict_type_annotations(file_path: str) -> None:
    """Fix missing type parameters for generic types like dict."""
    with open(file_path, "r") as f:
        content = f.read()

    # Add imports if needed
    if "from typing import" not in content and "import typing" not in content:
        content = f"from typing import Dict, List, Any, Optional\n\n{content}"

    # Replace bare dict with Dict[str, Any]
    content = re.sub(r"\bdict\b(?!\[)", "Dict[str, Any]", content)

    # Replace bare list with List[Any]
    content = re.sub(r"\blist\b(?!\[)", "List[Any]", content)

    with open(file_path, "w") as f:
        f.write(content)
    print(f"Fixed dict/list types in {file_path}")


def fix_optional_types(file_path: str) -> None:
    """Fix Optional type hints."""
    with open(file_path, "r") as f:
        content = f.read()

    # Find function parameters with default None values
    pattern = r"(\w+):\s*(\w+)\s*=\s*None"

    def replacement(match):
        param_name = match.group(1)
        param_type = match.group(2)
        return f"{param_name}: Optional[{param_type}] = None"

    modified_content = re.sub(pattern, replacement, content)

    if modified_content != content:
        with open(file_path, "w") as f:
            f.write(modified_content)
        print(f"Fixed Optional types in {file_path}")


def main():
    backend_dir = Path("/Users/vedprakashmishra/pathfinder/backend")

    # Get all Python files in the backend directory
    python_files = list(backend_dir.rglob("*.py"))

    # Focus on the most problematic files first
    priority_files = [
        "app/services/notification_service.py",
        "app/services/enhanced_chat.py",
        "app/services/file_service.py",
        "app/services/export_service.py",
        "app/core/config.py",
    ]

    # Process priority files first
    for priority_file in priority_files:
        file_path = backend_dir / priority_file
        if file_path.exists():
            print(f"Processing priority file: {file_path}")
            try:
                fix_function_return_types(str(file_path))
                fix_dict_type_annotations(str(file_path))
                fix_optional_types(str(file_path))
            except Exception as e:
                print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    main()
