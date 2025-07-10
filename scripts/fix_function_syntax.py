#!/usr/bin/env python3
"""Simple fix for function definition syntax errors."""

import glob
import os
import re

def fix_function_syntax(file_path):
    """Fix function definition syntax errors."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix function definitions with missing closing parenthesis and incorrect placement of colon
    # Pattern: async def func(...=Depends(...) # noqa: B008):
    pattern = r'(async def \w+\([^)]*=\s*Depends\([^)]*\))\s*#\s*noqa:\s*B008\s*\):'
    content = re.sub(pattern, r'\1):  # noqa: B008', content)
    
    # Pattern: async def func(...=Depends(...) # noqa: B008):
    pattern2 = r'(async def \w+\([^)]*=\s*Depends\([^)]*\))\s*#\s*noqa:\s*B008\s*:'
    content = re.sub(pattern2, r'\1):  # noqa: B008', content)
    
    # Pattern: func(current_user=Depends(require_role("admin") # noqa: B008):
    pattern3 = r'(\w+\([^)]*=\s*Depends\([^)]*\))\s*#\s*noqa:\s*B008\s*\):'
    content = re.sub(pattern3, r'\1):  # noqa: B008', content)
    
    # Pattern: func(current_user=Depends(require_role("admin") # noqa: B008):
    pattern4 = r'(\w+\([^)]*=\s*Depends\([^)]*\))\s*#\s*noqa:\s*B008\s*:'
    content = re.sub(pattern4, r'\1):  # noqa: B008', content)
    
    # Fix missing closing parenthesis in Depends calls
    # Pattern: Depends(something) followed by # noqa without proper closing
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Look for lines with Depends calls that might be missing closing parens
        if 'Depends(' in line and '# noqa: B008' in line:
            # Count parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            
            if open_parens > close_parens:
                # We're missing closing parentheses
                missing = open_parens - close_parens
                # Insert the missing closing parens before # noqa
                if '# noqa: B008' in line:
                    line = line.replace('# noqa: B008', ')' * missing + ':  # noqa: B008')
                    if not line.rstrip().endswith(':'):
                        line = line.rstrip() + ':'
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    api_dir = "backend/app/api"
    python_files = glob.glob(f"{api_dir}/*.py")
    
    fixed_count = 0
    for file_path in python_files:
        try:
            if fix_function_syntax(file_path):
                print(f"Fixed {file_path}")
                fixed_count += 1
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
    
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
