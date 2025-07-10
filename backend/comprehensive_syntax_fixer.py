#!/usr/bin/env python3
"""
Comprehensive Syntax Fixer for Pathfinder Backend
Fixes all critical syntax errors preventing production deployment
"""

import re
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class PathfinderSyntaxFixer:
    """Comprehensive syntax fixer for Pathfinder backend API files."""
    
    def __init__(self, backend_dir: str = "/Users/vedprakashmishra/pathfinder/backend"):
        self.backend_dir = Path(backend_dir)
        self.api_dir = self.backend_dir / "app" / "api"
        self.fixes_applied = []
        
    def fix_function_signature_parentheses(self, filepath: Path) -> bool:
        """Fix missing parentheses in function signatures."""
        print(f"🔧 Fixing function signature parentheses in {filepath.name}")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        original_content = content
        
        # Fix specific pattern: current_user=Depends(require_role("admin")):  ):
        content = re.sub(
            r'current_user=Depends\(require_role\("admin"\)\):\s*\)\s*:',
            r'current_user=Depends(require_role("admin"))):',
            content
        )
        
        # Fix broader pattern: extra ):  at end of function definitions
        content = re.sub(
            r'\):\s*\)\s*:',
            r'):',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed function signature parentheses in {filepath.name}")
            return True
        return False
    
    def fix_mismatched_braces(self, filepath: Path) -> bool:
        """Fix mismatched braces in dictionary/JSON responses."""
        print(f"🔧 Fixing mismatched braces in {filepath.name}")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        original_content = content
        
        # Pattern: return {"key": value,  # Missing closing brace
        # Look for opening { followed by content but no closing }
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check for unclosed dictionary returns
            if 'return {' in line and '}' not in line:
                # Look ahead to find if the brace is closed
                j = i + 1
                brace_count = line.count('{') - line.count('}')
                while j < len(lines) and brace_count > 0:
                    brace_count += lines[j].count('{') - lines[j].count('}')
                    j += 1
                
                # If we reached end without closing, add closing brace
                if brace_count > 0:
                    # Find the last meaningful line and add closing brace
                    last_content_line = i
                    while last_content_line < len(lines) - 1 and lines[last_content_line + 1].strip():
                        last_content_line += 1
                    
                    if last_content_line < len(lines):
                        lines[last_content_line] += '}'
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed mismatched braces in {filepath.name}")
            return True
        return False
    
    def fix_indentation_issues(self, filepath: Path) -> bool:
        """Fix indentation issues."""
        print(f"🔧 Fixing indentation in {filepath.name}")
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        original_lines = lines[:]
        
        # Fix unexpected indentation
        for i, line in enumerate(lines):
            # If line has unexpected indent, try to fix it
            if line.lstrip() != line and line.strip():
                # Check if previous line suggests this should be indented
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if not (prev_line.endswith(':') or prev_line.endswith('(') or prev_line.endswith('{')):
                        # This line shouldn't be indented
                        lines[i] = line.lstrip()
        
        if lines != original_lines:
            with open(filepath, 'w') as f:
                f.writelines(lines)
            print(f"✅ Fixed indentation in {filepath.name}")
            return True
        return False
    
    def fix_type_annotations(self, filepath: Path) -> bool:
        """Fix Python 3.11 type annotation compatibility issues."""
        print(f"🔧 Fixing type annotations in {filepath.name}")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        original_content = content
        
        # Add future import for annotations if not present
        if 'from __future__ import annotations' not in content:
            # Insert after existing imports
            lines = content.split('\n')
            import_insert_pos = 0
            
            # Find the best place to insert
            for i, line in enumerate(lines):
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    import_insert_pos = i + 1
                elif line.strip() and not line.strip().startswith('#'):
                    break
            
            lines.insert(import_insert_pos, 'from __future__ import annotations')
            content = '\n'.join(lines)
        
        # Fix Dict[str, Any] -> dict[str, Any] issues
        content = re.sub(r'Dict\[([^]]+)\]', r'dict[\1]', content)
        content = re.sub(r'List\[([^]]+)\]', r'list[\1]', content)
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed type annotations in {filepath.name}")
            return True
        return False
    
    def fix_specific_file_issues(self, filepath: Path) -> bool:
        """Fix specific issues for known problematic files."""
        filename = filepath.name
        
        if filename == "admin_broken.py":
            return self.fix_admin_broken(filepath)
        elif filename == "exports.py":
            return self.fix_exports(filepath)
        # Add more specific fixes as needed
        
        return False
    
    def fix_admin_broken(self, filepath: Path) -> bool:
        """Fix specific issues in admin_broken.py."""
        print(f"🔧 Fixing admin_broken.py specific issues")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        original_content = content
        
        # Fix the specific line 49 issue
        content = re.sub(
            r'async def clear_cache\(current_user=Depends\(require_role\("admin"\)\):\s*\)\s*:',
            r'async def clear_cache(current_user=Depends(require_role("admin"))):',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed admin_broken.py specific issues")
            return True
        return False
    
    def fix_exports(self, filepath: Path) -> bool:
        """Fix specific issues in exports.py."""
        print(f"🔧 Fixing exports.py specific issues")
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        original_content = content
        
        # Fix the specific line 66 issue - missing closing parenthesis
        content = re.sub(
            r'current_user: dict = Depends\(require_permissions\(\["trips: read"\]\),',
            r'current_user: dict = Depends(require_permissions(["trips: read"])),',
            content
        )
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✅ Fixed exports.py specific issues")
            return True
        return False
    
    def validate_file_syntax(self, filepath: Path) -> bool:
        """Validate that a file has correct Python syntax."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            compile(content, str(filepath), 'exec')
            return True
        except SyntaxError as e:
            print(f"❌ Syntax error in {filepath.name}: {e}")
            return False
    
    def fix_file(self, filepath: Path) -> bool:
        """Apply all fixes to a single file."""
        print(f"\n🔧 Processing {filepath.name}")
        
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            return False
        
        fixed = False
        
        # Try specific fixes first
        if self.fix_specific_file_issues(filepath):
            fixed = True
        
        # Apply general fixes
        if self.fix_function_signature_parentheses(filepath):
            fixed = True
        
        if self.fix_mismatched_braces(filepath):
            fixed = True
        
        if self.fix_indentation_issues(filepath):
            fixed = True
        
        if self.fix_type_annotations(filepath):
            fixed = True
        
        # Validate the result
        if self.validate_file_syntax(filepath):
            print(f"✅ {filepath.name} - All syntax errors fixed")
            if fixed:
                self.fixes_applied.append(filepath.name)
            return True
        else:
            print(f"❌ {filepath.name} - Still has syntax errors")
            return False
    
    def run_import_validation(self) -> Tuple[bool, List[str]]:
        """Run import validation to check current status."""
        print("\n🔍 Running import validation...")
        
        try:
            result = subprocess.run(
                [sys.executable, 'local_validation.py'],
                cwd=self.backend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ All imports successful!")
                return True, []
            else:
                # Parse failed modules from output
                failed_modules = []
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('❌'):
                        failed_modules.append(line.strip())
                
                print(f"❌ {len(failed_modules)} modules still have issues")
                return False, failed_modules
        except Exception as e:
            print(f"❌ Error running validation: {e}")
            return False, []
    
    def fix_all_files(self) -> bool:
        """Fix all problematic files in the API directory."""
        print("🚀 Starting comprehensive syntax fixing...")
        
        # List of files with known issues
        problematic_files = [
            "admin_broken.py", "exports.py", "llm_analytics.py", "maps.py",
            "health.py", "trip_messages.py", "feedback.py", "assistant.py",
            "families.py", "ai_cost.py", "test.py", "consensus.py",
            "notifications.py", "analytics.py", "polls.py", "coordination.py",
            "reservations.py", "websocket.py", "trips.py", "auth.py",
            "itineraries.py", "admin.py", "router.py"
        ]
        
        # Also check core dependencies
        core_files = [
            self.backend_dir / "app" / "core" / "dependencies.py",
            self.backend_dir / "app" / "main.py"
        ]
        
        success_count = 0
        total_files = len(problematic_files) + len(core_files)
        
        # Fix API files
        for filename in problematic_files:
            filepath = self.api_dir / filename
            if filepath.exists():
                if self.fix_file(filepath):
                    success_count += 1
            else:
                print(f"⚠️ File not found: {filename}")
        
        # Fix core files
        for filepath in core_files:
            if filepath.exists():
                if self.fix_file(filepath):
                    success_count += 1
        
        print(f"\n📊 Results: {success_count}/{total_files} files fixed")
        
        # Run final validation
        validation_passed, failed_modules = self.run_import_validation()
        
        if validation_passed:
            print("\n🎉 SUCCESS: All syntax errors fixed!")
            print("✅ Ready for production deployment")
            return True
        else:
            print(f"\n⚠️ {len(failed_modules)} modules still have issues:")
            for module in failed_modules[:5]:  # Show first 5
                print(f"  {module}")
            return False

def main():
    """Main execution function."""
    print("🔧 Pathfinder Comprehensive Syntax Fixer")
    print("=" * 50)
    
    fixer = PathfinderSyntaxFixer()
    
    if fixer.fix_all_files():
        print("\n🚀 Ready for production deployment!")
        print("Run: ./scripts/resume-environment.sh")
    else:
        print("\n❌ Some issues remain. Check the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
