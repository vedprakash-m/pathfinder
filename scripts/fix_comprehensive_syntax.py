#!/usr/bin/env python3
"""Comprehensive fix for all syntax errors in backend/app/api files."""

import glob
import os
import re

def fix_syntax_errors(file_path):
    """Fix various syntax errors in Python files."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix 1: Function definitions with missing closing parenthesis
    # Pattern: function(..., Depends(...) followed by : # noqa
    pattern1 = r'(\w+\([^)]*,\s*\w+\s*=\s*Depends\([^)]+\))\s*:\s*(#\s*noqa:\s*B008)'
    content = re.sub(pattern1, r'\1):  \2', content)
    
    # Fix 2: Function definitions with closing parenthesis in wrong place
    # Pattern: async def func(..., arg=Depends(...): # noqa
    pattern2 = r'(async def \w+\([^)]*=\s*Depends\([^)]+\)):\s*(#\s*noqa:\s*B008)'
    content = re.sub(pattern2, r'\1):  \2', content)
    
    # Fix 3: Mismatched braces and parentheses
    # Look for lines with just } that should be )
    lines = content.split('\n')
    fixed_lines = []
    paren_stack = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track opening parentheses
        for char in line:
            if char == '(':
                paren_stack.append(('(', i))
            elif char == ')':
                if paren_stack and paren_stack[-1][0] == '(':
                    paren_stack.pop()
        
        # Fix standalone } that should be )
        if stripped == '}':
            if paren_stack:
                # Replace } with ) and maintain indentation
                indent = len(line) - len(line.lstrip())
                line = ' ' * indent + ')'
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Fix 4: Unterminated function calls
    # Look for lines ending with ( without proper closure
    pattern3 = r'(\w+\s*=\s*Depends\([^)]*)\s*#\s*noqa:\s*B008'
    content = re.sub(pattern3, r'\1)  # noqa: B008', content)
    
    # Fix 5: Function definitions split across lines incorrectly
    # async def func(\n    args... without closing )
    pattern4 = r'(async def \w+\(\s*\n[^)]+)(\s*:\s*)'
    def fix_func_def(match):
        func_def = match.group(1)
        if not func_def.endswith(')'):
            func_def += ')'
        return func_def + match.group(2)
    
    content = re.sub(pattern4, fix_func_def, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix 6: Unterminated triple quotes
    # Count triple quotes and add missing ones
    triple_quote_count = content.count('"""')
    if triple_quote_count % 2 != 0:
        # Find the last """ and check if it needs a closing one
        lines = content.split('\n')
        in_docstring = False
        last_triple_quote_line = -1
        
        for i, line in enumerate(lines):
            if '"""' in line:
                count_in_line = line.count('"""')
                if count_in_line % 2 != 0:
                    in_docstring = not in_docstring
                last_triple_quote_line = i
        
        if in_docstring and last_triple_quote_line != -1:
            # Add closing triple quote after the last docstring line
            # Find a good place to insert it
            for i in range(last_triple_quote_line + 1, len(lines)):
                if lines[i].strip() == '' or not lines[i].strip().startswith('#'):
                    lines.insert(i, '    """')
                    break
            else:
                lines.append('    """')
            
            content = '\n'.join(lines)
    
    # Fix 7: Incorrect indentation issues
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix cases where we have unexpected indentation
        if i > 0 and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            # Check if previous line suggests this should be indented
            prev_line = lines[i-1].strip()
            if prev_line.endswith(':') or prev_line.endswith('('):
                # This line should probably be indented
                line = '    ' + line
        
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
    if not os.path.exists(api_dir):
        print(f"Directory {api_dir} does not exist")
        return
    
    python_files = glob.glob(f"{api_dir}/*.py")
    
    fixed_count = 0
    for file_path in python_files:
        try:
            if fix_syntax_errors(file_path):
                print(f"Fixed {file_path}")
                fixed_count += 1
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
    
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
