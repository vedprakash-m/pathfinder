#!/usr/bin/env python3
"""
Fix mismatched braces and parentheses in API files.
"""

import os
import re

def fix_brace_mismatch(content):
    """Fix cases where { and } are used instead of ( and )."""
    
    # Fix return statements with braces instead of parens
    # Pattern: return { -> return (
    content = re.sub(r'return\s*\{', 'return {', content)
    
    # But fix function calls that should use parentheses
    # Pattern: function_name{ -> function_name(
    content = re.sub(r'(\w+)\s*\{', r'\1(', content)
    
    # Fix closing braces that should be parentheses in function calls
    lines = content.split('\n')
    fixed_lines = []
    paren_stack = []
    
    for line_num, line in enumerate(lines):
        original_line = line
        
        # Track opening chars
        for i, char in enumerate(line):
            if char == '(':
                paren_stack.append(('(', line_num, i))
            elif char == '{':
                # Check context - if it's after = or return, it's a dict
                before = line[:i].strip()
                if (before.endswith('=') or before.endswith('return') or 
                    'dict(' in before or '{' in before):
                    paren_stack.append(('{', line_num, i))
                else:
                    # Probably should be a parenthesis
                    line = line[:i] + '(' + line[i+1:]
                    paren_stack.append(('(', line_num, i))
            elif char == ')':
                if paren_stack and paren_stack[-1][0] == '(':
                    paren_stack.pop()
            elif char == '}':
                if paren_stack:
                    last_open = paren_stack[-1][0]
                    if last_open == '(':
                        # This } should probably be )
                        line = line[:i] + ')' + line[i+1:]
                        paren_stack.pop()
                    elif last_open == '{':
                        paren_stack.pop()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_specific_patterns(content):
    """Fix specific known problematic patterns."""
    
    # Fix HTTPException with wrong braces
    content = re.sub(
        r'HTTPException\s*\(\s*\{([^}]+)\}\s*\)',
        r'HTTPException(\1)',
        content,
        flags=re.DOTALL
    )
    
    # Fix function return values
    content = re.sub(
        r'return\s+(\w+)\s*\(\s*\{([^}]+)\}\s*\)',
        r'return \1(\2)',
        content,
        flags=re.DOTALL
    )
    
    return content

def fix_indentation_errors(content):
    """Fix basic indentation errors."""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # If line is not empty and has no indentation but previous line ends with :
        if (line.strip() and not line.startswith((' ', '\t')) and 
            i > 0 and lines[i-1].strip().endswith(':')):
            # Add 4 spaces indentation
            line = '    ' + line
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file_targeted(file_path):
    """Apply targeted fixes to a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes in order
        content = fix_brace_mismatch(content)
        content = fix_specific_patterns(content)
        content = fix_indentation_errors(content)
        
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
    """Fix problematic API files."""
    
    # List of files with brace/parenthesis issues
    problem_files = [
        "backend/app/api/itineraries.py",
        "backend/app/api/exports.py", 
        "backend/app/api/llm_analytics.py",
        "backend/app/api/health.py",
        "backend/app/api/feedback.py",
        "backend/app/api/assistant.py",
        "backend/app/api/families.py",
        "backend/app/api/test.py",
        "backend/app/api/consensus.py",
        "backend/app/api/analytics.py",
        "backend/app/api/polls.py",
        "backend/app/api/coordination.py",
        "backend/app/api/reservations.py"
    ]
    
    fixed_count = 0
    
    for file_path in problem_files:
        if os.path.exists(file_path):
            print(f"Fixing {file_path}...")
            if fix_file_targeted(file_path):
                print(f"  ✅ Applied fixes")
                fixed_count += 1
            else:
                print(f"  ⚠️ No changes needed")
        else:
            print(f"  ❌ File not found")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()
