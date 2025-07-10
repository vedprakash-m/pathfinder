#!/usr/bin/env python3
"""Fix syntax errors in backend/app/api files."""

import glob
import os
import re

def fix_function_definitions(file_path):
    """Fix malformed function definitions."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match function definitions with malformed syntax
    # Look for functions ending with ) # noqa: B008: instead of ): # noqa: B008
    pattern = r'(\w+\([^)]*\))\s*#\s*noqa:\s*B008\s*:'
    replacement = r'\1:  # noqa: B008'
    
    modified = re.sub(pattern, replacement, content)
    
    # Also fix case where the closing paren is missing
    pattern2 = r'(\w+\([^)]*)\s*#\s*noqa:\s*B008\s*:'
    replacement2 = r'\1):  # noqa: B008'
    
    modified = re.sub(pattern2, replacement2, modified)
    
    # Fix duplicate noqa comments
    pattern3 = r'#\s*noqa:\s*B008\s*#\s*noqa:\s*B008\s*:'
    replacement3 = r'# noqa: B008'
    
    modified = re.sub(pattern3, replacement3, modified)
    
    if modified != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        print(f"Fixed {file_path}")
        return True
    return False

def main():
    api_dir = "backend/app/api"
    if not os.path.exists(api_dir):
        print(f"Directory {api_dir} does not exist")
        return
    
    python_files = glob.glob(f"{api_dir}/*.py")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_function_definitions(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
