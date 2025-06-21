#!/bin/bash

# Pathfinder Local Validation Script
# Comprehensive pre-commit validation to catch issues before CI/CD
# Usage: ./scripts/local-validation.sh [--fix] [--quick]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
FIX_ISSUES=false
QUICK_MODE=false
VALIDATION_FAILED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_ISSUES=true
            shift
            ;;
        --quick)
            QUICK_MODE=true
            shift
            ;;
        *)
            echo "Usage: $0 [--fix] [--quick]"
            echo "  --fix   : Automatically fix issues where possible"
            echo "  --quick : Skip time-consuming checks"
            exit 1
            ;;
    esac
done

print_status() {
    local message="$1"
    local status="$2"
    
    case $status in
        "success")
            echo -e "   ${GREEN}✅ $message${NC}"
            ;;
        "error")
            echo -e "   ${RED}❌ $message${NC}"
            VALIDATION_FAILED=true
            ;;
        "warning")
            echo -e "   ${YELLOW}⚠️  $message${NC}"
            ;;
        "info")
            echo -e "   ${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

print_header() {
    echo -e "\n${BLUE}$1${NC}"
    echo "=================================="
}

# Ensure we're in the project root
if [ ! -f "pyproject.toml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

print_header "🔍 Pathfinder Local Validation"
echo "Mode: $([ "$FIX_ISSUES" = true ] && echo "Fix Issues" || echo "Check Only") | $([ "$QUICK_MODE" = true ] && echo "Quick" || echo "Full")"

# 1. Requirements.txt Validation
print_header "📦 Requirements.txt Validation"

if [ -f "backend/requirements.txt" ]; then
    print_status "Found backend/requirements.txt" "success"
    
    # Check for syntax errors (concatenated packages)
    echo "   Checking for syntax errors..."
    if grep -n "==[0-9].*[a-zA-Z].*==" backend/requirements.txt; then
        print_status "SYNTAX ERROR: Concatenated packages found in requirements.txt" "error"
        echo "   ❌ Found packages without newlines between them"
        if [ "$FIX_ISSUES" = true ]; then
            echo "   🔧 Auto-fixing concatenated packages..."
            # Fix common concatenation patterns
            sed -i.bak 's/\(==[0-9][^a-zA-Z]*\)\([a-zA-Z]\)/\1\n\2/g' backend/requirements.txt
            if [ $? -eq 0 ]; then
                print_status "Fixed concatenated packages" "success"
                rm -f backend/requirements.txt.bak
            else
                print_status "Failed to auto-fix - manual intervention required" "error"
            fi
        fi
    else
        print_status "Requirements.txt syntax: OK" "success"
    fi
    
    # Check for duplicate packages
    echo "   Checking for duplicate packages..."
    DUPLICATES=$(cut -d'=' -f1 backend/requirements.txt | grep -v '^#' | grep -v '^$' | sort | uniq -d)
    if [ -n "$DUPLICATES" ]; then
        print_status "Duplicate packages found: $DUPLICATES" "error"
    else
        print_status "No duplicate packages found" "success"
    fi
    
    # Test pip install simulation (using pkg_resources parsing)
    echo "   Testing pip install simulation..."
    cd backend
    if python3 -c "
import pkg_resources
import sys
errors = []
with open('requirements.txt') as f:
    for line_num, line in enumerate(f, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                pkg_resources.Requirement.parse(line)
            except Exception as e:
                errors.append(f'Line {line_num}: {line} - {e}')
if errors:
    for error in errors:
        print(error)
    sys.exit(1)
" 2>/dev/null; then
        print_status "Backend dependencies are installable" "success"
    else
        print_status "Backend dependencies have installation issues" "error"
        echo "   ❌ Check requirements.txt syntax"
    fi
    cd ..
    
    # Check for known problematic packages
    echo "   Checking for known problematic packages..."
    if grep -q "dependency-injector" backend/requirements.txt; then
        print_status "dependency-injector found - ensure Python 3.11 in CI/CD" "warning"
    fi
    
else
    print_status "Missing backend/requirements.txt" "error"
fi

# 2. Frontend Package.json Validation
print_header "📦 Frontend Package.json Validation"

if [ -f "frontend/package.json" ]; then
    print_status "Found frontend/package.json" "success"
    
    # Check for syntax errors
    echo "   Validating JSON syntax..."
    if python3 -c "import json; json.load(open('frontend/package.json'))" 2>/dev/null; then
        print_status "Package.json syntax: OK" "success"
    else
        print_status "Package.json has syntax errors" "error"
    fi
    
    # Check pnpm lock file
    if [ -f "frontend/pnpm-lock.yaml" ]; then
        print_status "pnpm-lock.yaml found" "success"
    else
        print_status "pnpm-lock.yaml missing - run 'pnpm install'" "warning"
    fi
    
else
    print_status "Missing frontend/package.json" "error"
fi

# 3. Backend Code Quality Validation
print_header "🎯 Backend Code Quality"

cd backend

# Check if Python environment is set up
if ! python3 -c "import fastapi" 2>/dev/null; then
    print_status "Backend dependencies not installed - installing for validation..." "warning"
    if [ "$FIX_ISSUES" = true ]; then
        python3 -m pip install -r requirements.txt >/dev/null 2>&1 || {
            print_status "Failed to install dependencies" "error"
            cd ..
            exit 1
        }
    else
        print_status "Install dependencies with: cd backend && pip install -r requirements.txt" "error"
        cd ..
        exit 1
    fi
fi

# NEW: Python Import Validation (Critical for CI/CD)
print_header "🐍 Python Import Validation"

echo "   Testing critical module imports..."
IMPORT_ERRORS=()

# Test main application imports
if ! python3 -c "from app.main import app" 2>/dev/null; then
    IMPORT_ERRORS+=("app.main - Main application import failed")
fi

# Test container imports (common source of forward reference issues)
if ! python3 -c "from app.core.container import Container" 2>/dev/null; then
    IMPORT_ERRORS+=("app.core.container - Dependency injection container import failed")
fi

# Test API router imports
if ! python3 -c "from app.api.router import api_router" 2>/dev/null; then
    IMPORT_ERRORS+=("app.api.router - API router import failed")
fi

# Test database imports
if ! python3 -c "from app.core.database import get_db" 2>/dev/null; then
    IMPORT_ERRORS+=("app.core.database - Database connection import failed")
fi

# Test repository imports
if ! python3 -c "from app.core.repositories.trip_repository import TripRepository" 2>/dev/null; then
    IMPORT_ERRORS+=("app.core.repositories.trip_repository - Trip repository import failed")
fi

# Test domain service imports
if ! python3 -c "from backend.domain.trip import TripDomainService" 2>/dev/null; then
    IMPORT_ERRORS+=("backend.domain.trip - Domain service import failed")
fi

if [ ${#IMPORT_ERRORS[@]} -eq 0 ]; then
    print_status "All critical imports: Passed" "success"
else
    print_status "Import failures detected (${#IMPORT_ERRORS[@]} modules)" "error"
    for error in "${IMPORT_ERRORS[@]}"; do
        echo "   ❌ $error"
    done
    echo "   💡 These import failures will cause CI/CD to fail immediately"
fi

# NEW: Forward Reference Detection
echo "   Checking for forward reference issues..."
FORWARD_REF_ISSUES=()

# Check container.py for forward references (common issue)
if [ -f "app/core/container.py" ]; then
    # Look for variables used before definition in dependency injection
    FORWARD_REFS=$(python3 -c "
import ast
import sys

class ForwardRefChecker(ast.NodeVisitor):
    def __init__(self):
        self.defined_vars = set()
        self.used_vars = []
        self.issues = []
    
    def visit_Assign(self, node):
        # Track variable definitions
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_vars.add(target.id)
        
        # Check if assignment uses undefined variables
        for name_node in ast.walk(node.value):
            if isinstance(name_node, ast.Name) and isinstance(name_node.ctx, ast.Load):
                if name_node.id not in self.defined_vars and name_node.id not in ['providers', 'containers']:
                    self.issues.append(f'Line {name_node.lineno}: {name_node.id} used before definition')
        
        self.generic_visit(node)

try:
    with open('app/core/container.py') as f:
        tree = ast.parse(f.read())
    
    checker = ForwardRefChecker()
    checker.visit(tree)
    
    for issue in checker.issues:
        print(issue)
except Exception as e:
    pass
" 2>/dev/null)

    if [ -n "$FORWARD_REFS" ]; then
        FORWARD_REF_ISSUES+=("container.py: $FORWARD_REFS")
    fi
fi

if [ ${#FORWARD_REF_ISSUES[@]} -eq 0 ]; then
    print_status "Forward reference check: Passed" "success"
else
    print_status "Forward reference issues detected" "error"
    for issue in "${FORWARD_REF_ISSUES[@]}"; do
        echo "   ❌ $issue"
    done
fi

# Code formatting with black (simplified and reliable)
echo "   Checking code formatting..."
if python3 -c "import black" 2>/dev/null; then
    # Simple black check with timeout
    if timeout 30s python3 -m black --check . >/dev/null 2>&1; then
        print_status "Code formatting (black): Passed" "success"
    else
        print_status "Code formatting issues detected" "error"
        if [ "$FIX_ISSUES" = true ]; then
            echo "   🔧 Auto-fixing with black..."
            python3 -m black . >/dev/null 2>&1
            print_status "Code formatted with black" "success"
        else
            echo "   ❌ Run: cd backend && python3 -m black ."
        fi
    fi
else
    print_status "Black not available for code formatting" "warning"
fi

# Import sorting
echo "   Checking import sorting..."
if python3 -c "import isort" 2>/dev/null; then
    if python3 -m isort --check-only --diff . 2>/dev/null | grep -q "Fixing"; then
        print_status "Import sorting issues detected" "error"
        if [ "$FIX_ISSUES" = true ]; then
            echo "   🔧 Auto-fixing imports..."
            python3 -m isort . >/dev/null 2>&1
            print_status "Imports sorted" "success"
        else
            echo "   ❌ Run: cd backend && python3 -m isort ."
        fi
    else
        print_status "Import sorting: Passed" "success"
    fi
fi

# Linting with flake8/ruff
echo "   Running linting..."
if command -v ruff &> /dev/null; then
    if ruff check . 2>/dev/null; then
        print_status "Linting (ruff): Passed" "success"
    else
        print_status "Linting issues detected" "error"
        echo "   ❌ Run: cd backend && ruff check . --fix"
    fi
elif python3 -c "import flake8" 2>/dev/null; then
    if python3 -m flake8 . --max-line-length=88 --extend-ignore=E203,W503 --exclude=venv,migrations 2>/dev/null; then
        print_status "Linting (flake8): Passed" "success"
    else
        print_status "Linting issues detected" "error"
        echo "   ❌ Run: cd backend && python3 -m flake8 . --max-line-length=88"
    fi
fi

# Type checking (if not quick mode)
if [ "$QUICK_MODE" = false ]; then
    echo "   Checking type annotations..."
    if python3 -c "import mypy" 2>/dev/null; then
        # Fix MyPy path issues by using explicit package bases
        if python3 -m mypy app/ --ignore-missing-imports --explicit-package-bases 2>/dev/null; then
            print_status "Type checking (mypy): Passed" "success"
        else
            print_status "Type checking issues detected" "warning"
            echo "   ⚠️  Run: cd backend && python3 -m mypy app/ --explicit-package-bases"
        fi
    else
        print_status "MyPy not available" "warning"
    fi
fi

# Check if import-linter is available for architecture validation
if ! python3 -c "import importlinter" 2>/dev/null; then
    echo "   Installing import-linter for architecture validation..."
    python3 -m pip install import-linter >/dev/null 2>&1 || true
fi

# Architecture governance
echo "   Checking import structure..."
if [ -f "../importlinter_contracts/layers.toml" ]; then
    if python3 -c "import importlinter" 2>/dev/null; then
        # Test import-linter configuration syntax and violations
        LINT_OUTPUT=$(lint-imports --config ../importlinter_contracts/layers.toml 2>&1)
        LINT_EXIT_CODE=$?
        
        if echo "$LINT_OUTPUT" | grep -q "Cannot mutate immutable namespace\|Error\|Traceback"; then
            print_status "Import-linter config syntax error" "error"
            echo "   ❌ Configuration file has syntax errors"
            echo "   📝 Error details: $(echo "$LINT_OUTPUT" | head -1)"
            VALIDATION_FAILED=true
        elif [ $LINT_EXIT_CODE -eq 0 ]; then
            print_status "Import structure: Passed" "success"
        else
            # Check if there are violations
            BROKEN_COUNT=$(echo "$LINT_OUTPUT" | grep -c "BROKEN" || echo "0")
            if [ "$BROKEN_COUNT" -gt 0 ]; then
                print_status "Import structure violations detected ($BROKEN_COUNT contracts broken)" "warning"
                echo "   ⚠️  Architecture violations found (non-blocking in CI/CD)"
                echo "   📝 Run: cd backend && lint-imports --config ../importlinter_contracts/layers.toml"
            else
                print_status "Import structure: Issues detected" "warning"
                echo "   ⚠️  Run: cd backend && lint-imports --config ../importlinter_contracts/layers.toml"
            fi
        fi
    else
        print_status "Import-linter not available" "warning"
        echo "   ℹ️  Install with: python3 -m pip install import-linter"
    fi
else
    print_status "Import linter configuration missing" "error"
    VALIDATION_FAILED=true
fi

# Infrastructure validation (NEW)
echo "   Checking infrastructure prerequisites..."
if [ -f "../scripts/resume-environment.sh" ]; then
    # Check if data layer exists (if Azure CLI available)
    if command -v az &> /dev/null && az account show >/dev/null 2>&1; then
        DATA_RG="pathfinder-db-rg"
        if az group exists --name "$DATA_RG" >/dev/null 2>&1; then
            SQL_COUNT=$(az sql server list --resource-group "$DATA_RG" --query "length([])" -o tsv 2>/dev/null || echo "0")
            if [ "$SQL_COUNT" -gt 0 ]; then
                print_status "Data layer SQL server exists" "success"
            else
                print_status "Missing SQL server in data layer - will cause deployment failure" "error"
                echo "   ❌ Run: ./scripts/deploy-data-layer.sh"
            fi
        else
            print_status "Data layer not deployed - will cause deployment failure" "error"
            echo "   ❌ Run: ./scripts/deploy-data-layer.sh"
        fi
    else
        print_status "Azure CLI not available - skipping infrastructure check" "warning"
    fi
else
    print_status "Infrastructure scripts missing" "warning"
fi

cd ..

# 4. Frontend Code Quality (if not quick mode)
if [ "$QUICK_MODE" = false ]; then
    print_header "🎯 Frontend Code Quality"
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_status "Frontend dependencies not installed" "warning"
        if [ "$FIX_ISSUES" = true ]; then
            echo "   🔧 Installing frontend dependencies..."
            pnpm install >/dev/null 2>&1 || npm install >/dev/null 2>&1
        else
            print_status "Install with: cd frontend && pnpm install" "info"
        fi
    fi
    
    # Type checking
    if [ -d "node_modules" ]; then
        echo "   Running TypeScript type checking..."
        if pnpm run type-check >/dev/null 2>&1 || npm run type-check >/dev/null 2>&1; then
            print_status "TypeScript type checking: Passed" "success"
        else
            print_status "TypeScript type checking failed" "error"
            echo "   ❌ Run: cd frontend && pnpm run type-check"
        fi
        
        # Linting (if available)
        echo "   Running ESLint..."
        if pnpm run lint >/dev/null 2>&1 || npm run lint >/dev/null 2>&1; then
            print_status "ESLint: Passed" "success"
        else
            print_status "ESLint issues detected" "warning"
            echo "   ⚠️  Run: cd frontend && pnpm run lint"
        fi
    fi
    
    cd ..
fi

# 5. Docker Build Validation
print_header "🐳 Docker Build Validation"

# Test backend Docker build
echo "   Testing backend Docker build..."
if ! command -v docker &> /dev/null; then
    print_status "Docker not available - skipping build test" "warning"
elif ! docker info >/dev/null 2>&1; then
    print_status "Docker daemon not running - skipping build test" "warning"
elif docker build -t pathfinder-backend-test ./backend >/dev/null 2>&1; then
    print_status "Backend Docker build: Passed" "success"
    docker rmi pathfinder-backend-test >/dev/null 2>&1 || true
else
    print_status "Backend Docker build failed" "error"
    echo "   ❌ Run: docker build -t test ./backend"
fi

# Test frontend Docker build (if not quick mode)
if [ "$QUICK_MODE" = false ]; then
    echo "   Testing frontend Docker build..."
    if ! command -v docker &> /dev/null; then
        print_status "Docker not available - skipping build test" "warning"
    elif ! docker info >/dev/null 2>&1; then
        print_status "Docker daemon not running - skipping build test" "warning"
    elif docker build -t pathfinder-frontend-test ./frontend >/dev/null 2>&1; then
        print_status "Frontend Docker build: Passed" "success"
        docker rmi pathfinder-frontend-test >/dev/null 2>&1 || true
    else
        print_status "Frontend Docker build failed" "error"
        echo "   ❌ Run: docker build -t test ./frontend"
    fi
fi

# 6. GitHub Actions Validation (NEW)
print_header "🔧 GitHub Actions Validation"

echo "   Checking workflow syntax..."
for workflow in .github/workflows/*.yml; do
    if [ -f "$workflow" ]; then
        WORKFLOW_NAME=$(basename "$workflow")
        # Check for basic YAML syntax
        if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
            print_status "$WORKFLOW_NAME: Valid YAML" "success"
        else
            print_status "$WORKFLOW_NAME: Invalid YAML syntax" "error"
        fi
        
        # Check for missing action references
        if grep -q "uses:.*/.github/actions/" "$workflow"; then
            MISSING_ACTIONS=$(grep "uses:.*/.github/actions/" "$workflow" | sed 's/.*uses: *//' | sed 's/@.*//' | while read action; do
                if [ ! -d "$action" ]; then
                    echo "$action"
                fi
            done)
            if [ -n "$MISSING_ACTIONS" ]; then
                print_status "$WORKFLOW_NAME: Missing action references" "error"
                echo "   ❌ Missing: $MISSING_ACTIONS"
            fi
        fi
    fi
done

# Check for action directories that don't exist but are referenced
echo "   Checking for orphaned action references..."
if find .github/workflows -name "*.yml" -exec grep -l "/.github/actions/" {} \; | wc -l | grep -q "0"; then
    print_status "No custom GitHub Actions referenced" "success"
else
    print_status "Custom GitHub Actions found - verify they exist" "warning"
fi

# 7. Git Status Check
print_header "📝 Git Status Check"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_status "Uncommitted changes detected" "warning"
    echo "   ⚠️  Consider committing changes before pushing"
    git status --short
else
    print_status "Working directory clean" "success"
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ]; then
    print_status "On main branch - changes will trigger CI/CD" "info"
else
    print_status "On branch: $CURRENT_BRANCH" "info"
fi

# NEW: Enhanced Test Execution (Exact CI/CD Match)
print_header "🧪 Test Execution (CI/CD Environment Match)"

echo "   Setting up test environment (matching CI/CD)..."
# Set exact same environment variables as CI/CD
export ENVIRONMENT=testing
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export AUTH0_DOMAIN="test-domain.auth0.com"
export AUTH0_AUDIENCE="test-audience"
export AUTH0_CLIENT_ID="test-client-id"
export AUTH0_CLIENT_SECRET="test-client-secret"
export OPENAI_API_KEY="sk-test-key-for-testing"
export GOOGLE_MAPS_API_KEY="test-maps-key-for-testing"

# Install test dependencies if missing
echo "   Ensuring test dependencies are available..."
MISSING_DEPS=()
for dep in pytest pytest-asyncio httpx pytest-mock coverage; do
    if ! python3 -c "import ${dep//-/_}" 2>/dev/null; then
        MISSING_DEPS+=($dep)
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    if [ "$FIX_ISSUES" = true ]; then
        echo "   🔧 Installing missing test dependencies: ${MISSING_DEPS[*]}"
        python3 -m pip install "${MISSING_DEPS[@]}" >/dev/null 2>&1
    else
        print_status "Missing test dependencies: ${MISSING_DEPS[*]}" "error"
        echo "   💡 Install: pip install ${MISSING_DEPS[*]}"
    fi
fi

# Test conftest.py import (critical failure point)
echo "   Testing conftest.py import (critical CI/CD failure point)..."
if python3 -c "import sys; sys.path.append('tests'); import conftest" 2>/dev/null; then
    print_status "conftest.py import: Passed" "success"
else
    print_status "conftest.py import failed - will cause CI/CD failure" "error"
    echo "   ❌ This is the exact error causing CI/CD failure"
    echo "   🔧 Fix imports in conftest.py and related modules"
fi

# Run tests with exact CI/CD command and environment
echo "   Running tests with coverage (exact CI/CD command)..."
if python3 -c "import pytest, coverage" 2>/dev/null; then
    # Use exact same command as CI/CD
    if coverage run -m pytest tests/ -v --tb=short 2>/dev/null; then
        print_status "Test execution: Passed" "success"
        
        # Generate coverage report (same as CI/CD)
        COVERAGE_OUTPUT=$(coverage report 2>/dev/null)
        if echo "$COVERAGE_OUTPUT" | grep -q "TOTAL.*[0-9][0-9]%"; then
            COVERAGE_PERCENT=$(echo "$COVERAGE_OUTPUT" | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
            if [ "$COVERAGE_PERCENT" -ge 70 ]; then
                print_status "Test coverage: ${COVERAGE_PERCENT}% (above 70% threshold)" "success"
            else
                print_status "Test coverage: ${COVERAGE_PERCENT}% (below 70% threshold)" "warning"
            fi
        else
            print_status "Coverage report generated" "success"
        fi
    else
        print_status "Test execution failed (same failure as CI/CD)" "error"
        echo "   ❌ This matches the CI/CD failure pattern"
        echo "   🔧 Fix import errors and environment setup"
        echo "   📝 Run: cd backend && ENVIRONMENT=testing coverage run -m pytest tests/ -v"
    fi
else
    print_status "Test framework not available" "error"
    echo "   💡 Install: pip install pytest pytest-asyncio coverage"
fi

# Summary
print_header "📊 Validation Summary"

if [ "$VALIDATION_FAILED" = true ]; then
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo "Some issues were detected that will cause CI/CD failures."
    if [ "$FIX_ISSUES" = true ]; then
        echo "Auto-fixes were attempted. Please review changes and run validation again."
    else
        echo "Run with --fix to automatically fix issues where possible."
    fi
    echo ""
    echo "To run individual checks:"
    echo "  Backend quality: cd backend && ruff format . && ruff check . && mypy app/"
    echo "  Frontend quality: cd frontend && pnpm run type-check && pnpm run lint"
    echo "  Docker builds: docker build -t test ./backend && docker build -t test ./frontend"
    exit 1
else
    echo -e "${GREEN}✅ ALL VALIDATIONS PASSED${NC}"
    echo "Your code is ready for CI/CD pipeline!"
    echo ""
    echo "Next steps:"
    echo "  1. Commit your changes: git add . && git commit -m 'Your message'"
    echo "  2. Push to trigger CI/CD: git push origin $CURRENT_BRANCH"
    echo ""
    echo "The CI/CD pipeline will run the same checks and deploy if successful."
fi 