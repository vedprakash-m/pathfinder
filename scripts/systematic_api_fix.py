#!/usr/bin/env python3
"""
Systematic fix for all remaining syntax errors in API files.
"""

import os
import re
import ast
import traceback

def fix_function_parameters(content):
    """Fix malformed function parameter syntax."""
    
    # Fix pattern: param): Type = Depends(...) -> param: Type = Depends(...)
    pattern1 = r'(\w+)\):\s*(\w+(?:\[\w+\])?)\s*=\s*(Depends\([^)]+\))'
    content = re.sub(pattern1, r'\1: \2 = \3', content)
    
    # Fix pattern: param): Type -> param: Type  
    pattern2 = r'(\w+)\):\s*(\w+(?:\[\w+\])?)'
    content = re.sub(pattern2, r'\1: \2', content)
    
    return content

def fix_function_definitions(content):
    """Fix function definition syntax issues."""
    
    # Fix missing closing parenthesis in function definitions
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for function definitions
        if re.match(r'\s*async def \w+\(', line):
            # Find the end of the function definition
            func_lines = [line]
            paren_count = line.count('(') - line.count(')')
            
            j = i + 1
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                func_lines.append(next_line)
                paren_count += next_line.count('(') - next_line.count(')')
                j += 1
            
            # Join the function definition and fix it
            func_def = '\n'.join(func_lines)
            
            # Fix common issues
            func_def = fix_function_parameters(func_def)
            
            # Ensure proper closing
            if paren_count == 0 and not func_def.rstrip().endswith(':'):
                func_def = func_def.rstrip() + ':'
            
            # Add the fixed lines
            fixed_lines.extend(func_def.split('\n'))
            i = j
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_mismatched_braces(content):
    """Fix mismatched braces and parentheses."""
    
    # Replace standalone } with )
    content = re.sub(r'^(\s*)}(\s*)$', r'\1)\2', content, flags=re.MULTILINE)
    
    return content

def fix_unterminated_strings(content):
    """Fix unterminated triple-quoted strings."""
    
    lines = content.split('\n')
    in_triple_quote = False
    quote_type = None
    
    for i, line in enumerate(lines):
        # Check for triple quotes
        if '"""' in line:
            count = line.count('"""')
            if count % 2 == 1:  # Odd number means toggle state
                if not in_triple_quote:
                    in_triple_quote = True
                    quote_type = '"""'
                else:
                    in_triple_quote = False
                    quote_type = None
        elif "'''" in line:
            count = line.count("'''")
            if count % 2 == 1:
                if not in_triple_quote:
                    in_triple_quote = True
                    quote_type = "'''"
                else:
                    in_triple_quote = False
                    quote_type = None
    
    # If we end with an unterminated string, add closing quotes
    if in_triple_quote and quote_type:
        content += f'\n{quote_type}'
    
    return content

def validate_syntax(file_path):
    """Check if file has valid Python syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def fix_file(file_path):
    """Fix a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_function_definitions(content)
        content = fix_mismatched_braces(content)
        content = fix_unterminated_strings(content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all API files."""
    api_dir = "backend/app/api"
    
    if not os.path.exists(api_dir):
        print(f"Directory {api_dir} not found")
        return
    
    # Get all Python files except __init__.py
    python_files = []
    for file in os.listdir(api_dir):
        if file.endswith('.py') and file != '__init__.py':
            python_files.append(os.path.join(api_dir, file))
    
    print(f"Found {len(python_files)} Python files to check")
    
    # Fix each file
    fixed_count = 0
    errors = []
    
    for file_path in python_files:
        print(f"\nChecking {file_path}...")
        
        # Check initial syntax
        valid, error = validate_syntax(file_path)
        if valid:
            print(f"  ✅ Already valid")
            continue
        
        print(f"  ❌ Syntax error: {error}")
        
        # Try to fix
        if fix_file(file_path):
            print(f"  🔧 Applied fixes")
            
            # Check if fix worked
            valid, error = validate_syntax(file_path)
            if valid:
                print(f"  ✅ Fixed successfully")
                fixed_count += 1
            else:
                print(f"  ❌ Still has errors: {error}")
                errors.append((file_path, error))
        else:
            print(f"  ⚠️  No changes made")
            errors.append((file_path, error))
    
    print(f"\n=== Summary ===")
    print(f"Fixed: {fixed_count} files")
    print(f"Errors remaining: {len(errors)} files")
    
    if errors:
        print(f"\nFiles with remaining errors:")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")

if __name__ == "__main__":
    main()
