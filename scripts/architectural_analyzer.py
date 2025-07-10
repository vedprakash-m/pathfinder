#!/usr/bin/env python3
"""
Architectural Analysis Tool - Deep Root Cause Analysis
Analyzes the codebase to identify architectural conflicts and provide repair guidance.
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ArchitecturalAnalyzer:
    """Comprehensive architectural analysis tool."""
    
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.conflicts = defaultdict(list)
        self.import_graph = defaultdict(set)
        self.sql_imports = set()
        self.cosmos_imports = set()
        self.domain_imports = set()
        self.api_files = {}
        
    def analyze_file(self, file_path: Path) -> Dict:
        """Analyze a single Python file for architectural patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            analysis = {
                'file': str(file_path),
                'sql_imports': [],
                'cosmos_imports': [],
                'domain_imports': [],
                'imports': [],
                'syntax_valid': True,
                'architectural_patterns': []
            }
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append(alias.name)
                        self.categorize_import(alias.name, analysis)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis['imports'].append(node.module)
                        self.categorize_import(node.module, analysis)
            
            # Identify architectural patterns
            self.identify_patterns(analysis)
            
            return analysis
            
        except SyntaxError as e:
            return {
                'file': str(file_path),
                'syntax_valid': False,
                'error': str(e),
                'architectural_patterns': []
            }
        except Exception as e:
            return {
                'file': str(file_path),
                'syntax_valid': False,
                'error': f"Analysis error: {str(e)}",
                'architectural_patterns': []
            }
    
    def categorize_import(self, import_name: str, analysis: Dict):
        """Categorize imports into architectural patterns."""
        if any(pattern in import_name for pattern in ['sqlalchemy', 'app.models', 'app.core.database']):
            analysis['sql_imports'].append(import_name)
            self.sql_imports.add(import_name)
        
        if any(pattern in import_name for pattern in ['cosmos', 'app.repositories.cosmos_unified', 'app.core.database_unified']):
            analysis['cosmos_imports'].append(import_name)
            self.cosmos_imports.add(import_name)
        
        if any(pattern in import_name for pattern in ['domain.', 'app.application']):
            analysis['domain_imports'].append(import_name)
            self.domain_imports.add(import_name)
    
    def identify_patterns(self, analysis: Dict):
        """Identify architectural patterns in the file."""
        patterns = []
        
        # Check for mixed patterns
        if analysis['sql_imports'] and analysis['cosmos_imports']:
            patterns.append('SQL_COSMOS_CONFLICT')
        
        if analysis['sql_imports'] and analysis['domain_imports']:
            patterns.append('SQL_DOMAIN_CONFLICT')
        
        if analysis['cosmos_imports'] and analysis['domain_imports']:
            patterns.append('COSMOS_DOMAIN_INTEGRATION')
        
        if len(analysis['sql_imports']) > 0:
            patterns.append('SQL_PATTERN')
        
        if len(analysis['cosmos_imports']) > 0:
            patterns.append('COSMOS_PATTERN')
        
        if len(analysis['domain_imports']) > 0:
            patterns.append('DOMAIN_PATTERN')
        
        analysis['architectural_patterns'] = patterns
    
    def analyze_api_layer(self) -> Dict:
        """Analyze all API files for architectural conflicts."""
        api_path = self.backend_path / 'app' / 'api'
        api_analysis = {
            'total_files': 0,
            'working_files': 0,
            'broken_files': 0,
            'files': [],
            'conflicts': defaultdict(int),
            'patterns': defaultdict(int)
        }
        
        for file_path in api_path.glob('*.py'):
            if file_path.name.startswith('__'):
                continue
                
            analysis = self.analyze_file(file_path)
            api_analysis['files'].append(analysis)
            api_analysis['total_files'] += 1
            
            if analysis['syntax_valid']:
                api_analysis['working_files'] += 1
            else:
                api_analysis['broken_files'] += 1
            
            # Count patterns
            for pattern in analysis['architectural_patterns']:
                api_analysis['patterns'][pattern] += 1
                
                if 'CONFLICT' in pattern:
                    api_analysis['conflicts'][pattern] += 1
        
        return api_analysis
    
    def analyze_dependencies(self) -> Dict:
        """Analyze dependency injection patterns."""
        dep_analysis = {
            'dependency_files': [],
            'di_patterns': [],
            'conflicts': []
        }
        
        # Check core dependencies
        dep_file = self.backend_path / 'app' / 'core' / 'dependencies.py'
        if dep_file.exists():
            analysis = self.analyze_file(dep_file)
            dep_analysis['dependency_files'].append(analysis)
            
            # Check for DI conflicts
            if 'SQL_COSMOS_CONFLICT' in analysis['architectural_patterns']:
                dep_analysis['conflicts'].append('Mixed SQL/Cosmos dependency injection')
        
        # Check container DI
        container_file = self.backend_path / 'app' / 'core' / 'container.py'
        if container_file.exists():
            analysis = self.analyze_file(container_file)
            dep_analysis['dependency_files'].append(analysis)
            dep_analysis['di_patterns'].append('CONTAINER_DI')
        
        return dep_analysis
    
    def analyze_models(self) -> Dict:
        """Analyze model definitions for conflicts."""
        model_analysis = {
            'sql_models': [],
            'cosmos_models': [],
            'conflicts': []
        }
        
        # Check SQL models
        models_path = self.backend_path / 'app' / 'models'
        if models_path.exists():
            for file_path in models_path.glob('*.py'):
                if file_path.name.startswith('__'):
                    continue
                analysis = self.analyze_file(file_path)
                if 'SQL_PATTERN' in analysis['architectural_patterns']:
                    model_analysis['sql_models'].append(analysis)
        
        # Check Cosmos models
        cosmos_file = self.backend_path / 'app' / 'repositories' / 'cosmos_unified.py'
        if cosmos_file.exists():
            analysis = self.analyze_file(cosmos_file)
            if 'COSMOS_PATTERN' in analysis['architectural_patterns']:
                model_analysis['cosmos_models'].append(analysis)
        
        # Identify conflicts
        if model_analysis['sql_models'] and model_analysis['cosmos_models']:
            model_analysis['conflicts'].append('DUAL_MODEL_DEFINITIONS')
        
        return model_analysis
    
    def generate_report(self) -> str:
        """Generate comprehensive architectural analysis report."""
        report = []
        report.append("=" * 80)
        report.append("PATHFINDER ARCHITECTURAL ANALYSIS REPORT")
        report.append("=" * 80)
        
        # API Layer Analysis
        api_analysis = self.analyze_api_layer()
        report.append(f"\n📁 API LAYER ANALYSIS:")
        report.append(f"   Total Files: {api_analysis['total_files']}")
        report.append(f"   Working Files: {api_analysis['working_files']}")
        report.append(f"   Broken Files: {api_analysis['broken_files']}")
        report.append(f"   Success Rate: {api_analysis['working_files']/api_analysis['total_files']*100:.1f}%")
        
        # Pattern Analysis
        report.append(f"\n🏗️ ARCHITECTURAL PATTERNS:")
        for pattern, count in api_analysis['patterns'].items():
            report.append(f"   {pattern}: {count} files")
        
        # Conflict Analysis
        report.append(f"\n⚠️ ARCHITECTURAL CONFLICTS:")
        for conflict, count in api_analysis['conflicts'].items():
            report.append(f"   {conflict}: {count} files")
        
        # Dependency Analysis
        dep_analysis = self.analyze_dependencies()
        report.append(f"\n🔗 DEPENDENCY INJECTION ANALYSIS:")
        report.append(f"   DI Files Found: {len(dep_analysis['dependency_files'])}")
        report.append(f"   DI Patterns: {dep_analysis['di_patterns']}")
        report.append(f"   DI Conflicts: {dep_analysis['conflicts']}")
        
        # Model Analysis
        model_analysis = self.analyze_models()
        report.append(f"\n📊 MODEL DEFINITION ANALYSIS:")
        report.append(f"   SQL Models: {len(model_analysis['sql_models'])}")
        report.append(f"   Cosmos Models: {len(model_analysis['cosmos_models'])}")
        report.append(f"   Model Conflicts: {model_analysis['conflicts']}")
        
        # Recommendations
        report.append(f"\n🎯 ARCHITECTURAL RECOMMENDATIONS:")
        if api_analysis['conflicts']:
            report.append("   1. CRITICAL: Resolve architectural conflicts in API layer")
            report.append("   2. Adopt single architectural pattern (Cosmos + Domain-Driven)")
            report.append("   3. Remove SQL dependencies completely")
            report.append("   4. Standardize dependency injection patterns")
        
        # Broken Files Detail
        if api_analysis['broken_files'] > 0:
            report.append(f"\n🚨 BROKEN FILES DETAIL:")
            for file_analysis in api_analysis['files']:
                if not file_analysis['syntax_valid']:
                    report.append(f"   ❌ {file_analysis['file']}")
                    if 'error' in file_analysis:
                        report.append(f"      Error: {file_analysis['error']}")
        
        return "\n".join(report)
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run comprehensive architectural analysis."""
        return {
            'api_analysis': self.analyze_api_layer(),
            'dependency_analysis': self.analyze_dependencies(),
            'model_analysis': self.analyze_models(),
            'report': self.generate_report()
        }

def main():
    """Main execution function."""
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_path):
        print(f"❌ Backend path not found: {backend_path}")
        sys.exit(1)
    
    analyzer = ArchitecturalAnalyzer(backend_path)
    results = analyzer.run_comprehensive_analysis()
    
    print(results['report'])
    
    # Save detailed results
    import json
    with open('architectural_analysis_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: architectural_analysis_results.json")

if __name__ == "__main__":
    main()
