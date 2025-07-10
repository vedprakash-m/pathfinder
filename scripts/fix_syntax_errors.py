#!/usr/bin/env python3
"""
Fix syntax errors introduced by the previous ruff fix script.
"""

import os
import re
import subprocess
from pathlib import Path

def fix_malformed_function_definitions(file_path):
    """Fix malformed function definitions and parameters."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix malformed function parameter lines that end with trailing commas and noqa comments
    # Pattern: parameter_name: Type = Depends(something)  # noqa: B008,
    content = re.sub(
        r'(\s+\w+:\s*[^=]+\s*=\s*Depends\([^)]+\))\s*#\s*noqa:\s*B008,\s*(#\s*noqa:\s*B008)?,?\s*$',
        r'\1,',
        content,
        flags=re.MULTILINE
    )
    
    # Fix function definitions that are broken across lines incorrectly
    # Look for lines that end with Depends(...) # noqa: B008) # noqa: B008,
    content = re.sub(
        r'(\s+current_user:\s*[^=]+\s*=\s*Depends\([^)]+\))\s*#\s*noqa:\s*B008\)\s*#\s*noqa:\s*B008,?\s*$',
        r'\1,',
        content,
        flags=re.MULTILINE
    )
    
    # Fix closing parentheses that appear on their own line after malformed noqa comments
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has a malformed function parameter with trailing comma and noqa
        if (re.match(r'^\s+\w+:\s*[^=]+\s*=\s*Depends\([^)]+\)\s*#\s*noqa:\s*B008,\s*$', line) or
            re.match(r'^\s+\w+:\s*[^=]+\s*=\s*Depends\([^)]+\),\s*$', line)):
            # Clean up the line
            cleaned_line = re.sub(r'\s*#\s*noqa:\s*B008,?\s*$', '', line)
            if not cleaned_line.rstrip().endswith(','):
                cleaned_line = cleaned_line.rstrip() + ','
            fixed_lines.append(cleaned_line)
        elif line.strip() == '):' and i > 0:
            # This might be a closing parenthesis that should be on the previous line
            # Check if the previous line looks like a function parameter
            prev_line = fixed_lines[-1] if fixed_lines else ''
            if (prev_line.strip().endswith(',') and 
                ('Depends(' in prev_line or 'current_user:' in prev_line)):
                # Remove the comma from the previous line and close the function
                fixed_lines[-1] = prev_line.rstrip().rstrip(',')
                fixed_lines.append('):')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Fix docstrings that are incorrectly formatted
    content = re.sub(
        r'^(\s+)"""([^"]+)$',
        r'\1"""\2"""',
        content,
        flags=re.MULTILINE
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed syntax errors in {file_path}")
        return True
    return False

def fix_malformed_noqa_comments(file_path):
    """Fix malformed # noqa comments."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remove invalid noqa comments and duplicates
    content = re.sub(r'#\s*noqa:\s*B008,\s*#\s*noqa:\s*B008', '# noqa: B008', content)
    content = re.sub(r'#\s*noqa:\s*B008,\s*$', '# noqa: B008', content, flags=re.MULTILINE)
    content = re.sub(r'#\s*noqa:\s*B008\)\s*#\s*noqa:\s*B008', '# noqa: B008', content)
    
    # Fix invalid noqa directive format (should be code only)
    content = re.sub(r'#\s*noqa:\s*[^A-Z0-9\s,]+', '# noqa: B008', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed noqa comments in {file_path}")
        return True
    return False

def main():
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("Backend directory not found")
        return
    
    print("Fixing syntax errors and malformed noqa comments...")
    
    # Get all Python files that were mentioned in the error
    error_files = [
        "backend/app/api/admin.py",
        "backend/app/api/auth.py",
        "backend/app/api/ai_cost.py",
        "backend/app/api/assistant.py",
        "backend/app/api/consensus.py",
        "backend/app/api/families.py",
        "backend/app/api/coordination.py",
        "backend/app/api/exports.py",
        "backend/app/api/feedback.py",
        "backend/app/api/llm_analytics.py",
        "backend/app/api/notifications.py",
        "backend/app/api/itineraries.py",
        "backend/app/api/test.py",
        "backend/app/api/maps.py",
        "backend/app/api/trips.py",
        "backend/app/api/polls.py",
        "backend/app/api/trip_messages.py",
        "backend/app/api/websocket.py",
        "backend/app/api/reservations.py",
    ]
    
    fixed_count = 0
    for file_path in error_files:
        if os.path.exists(file_path):
            if fix_malformed_function_definitions(file_path):
                fixed_count += 1
            if fix_malformed_noqa_comments(file_path):
                fixed_count += 1
    
    print(f"Fixed {fixed_count} files")
    
    # Also scan for any other Python files with similar issues
    for py_file in backend_dir.rglob("*.py"):
        if py_file.is_file() and str(py_file) not in error_files:
            fix_malformed_noqa_comments(str(py_file))

if __name__ == "__main__":
    main()
