#!/usr/bin/env python3
"""
Quick script to fix common ruff issues found by pre-commit hooks.
"""

import os
import re
import subprocess
from pathlib import Path


def add_noqa_for_fastapi_depends(file_path: Path):
    """Add # noqa: B008 comments for FastAPI Depends() usage"""
    try:
        content = file_path.read_text()
        
        # Pattern to match FastAPI dependency injection
        patterns = [
            # Match function parameters with Depends()
            (r'(\s+\w+.*?=\s*Depends\([^)]+\))(?!\s*#\s*noqa)', r'\1  # noqa: B008'),
            # Match complex Depends patterns
            (r'(\s+.*?=\s*Depends\(.*?\))(?!\s*#\s*noqa)', r'\1  # noqa: B008'),
        ]
        
        modified = False
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                content = new_content
                modified = True
        
        if modified:
            file_path.write_text(content)
            print(f"Fixed B008 issues in {file_path}")
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def fix_import_order():
    """Fix import order using isort"""
    try:
        subprocess.run(['python', '-m', 'isort', 'backend/', '--profile', 'black'], check=True)
        print("Fixed import order with isort")
    except subprocess.CalledProcessError as e:
        print(f"Error running isort: {e}")


def fix_unused_variables(file_path: Path):
    """Fix simple unused variable issues by prefixing with underscore"""
    try:
        content = file_path.read_text()
        
        # Common patterns for unused variables
        patterns = [
            # Loop variables not used
            (r'for (\w+) in ', lambda m: f'for _{m.group(1)} in ' if len(m.group(1)) == 1 else m.group(0)),
            # Assignment to unused variables in common cases
            (r'(\s+)(\w+) = ([^=\n]+)(\s*#.*F841)', r'\1_\2 = \3\4'),
        ]
        
        modified = False
        for pattern, replacement in patterns:
            if callable(replacement):
                new_content = re.sub(pattern, replacement, content)
            else:
                new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                modified = True
        
        if modified:
            file_path.write_text(content)
            print(f"Fixed unused variables in {file_path}")
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def main():
    """Main function to fix ruff issues"""
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("Backend directory not found")
        return
    
    # Get all Python files in the backend
    python_files = list(backend_dir.rglob("*.py"))
    
    # Focus on API files first since they have the most B008 issues
    api_files = [f for f in python_files if "/api/" in str(f)]
    
    print(f"Processing {len(api_files)} API files for FastAPI Depends issues...")
    for file_path in api_files:
        add_noqa_for_fastapi_depends(file_path)
    
    # Fix import order
    print("Fixing import order...")
    fix_import_order()
    
    print("Done!")


if __name__ == "__main__":
    main()
