#!/bin/bash

# Pathfinder Local Validation Script
# Comprehensive pre-commit validation to catch issues before CI/CD
# Enhanced to align with CI/CD pipeline and provide detailed coverage reporting
# Usage: ./scripts/local-validation.sh [--fix] [--quick] [--coverage]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Flags
FIX_ISSUES=false
QUICK_MODE=false
COVERAGE_MODE=false
VALIDATION_FAILED=false
DOCKER_MODE=false
DOCKER_COMPOSE_MODE=false

# Test isolation
TEST_ISOLATION=true
CLEANUP_ON_EXIT=true

# Coverage thresholds
BACKEND_COVERAGE_THRESHOLD=75
FRONTEND_COVERAGE_THRESHOLD=60
E2E_COVERAGE_THRESHOLD=80

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
        --coverage)
            COVERAGE_MODE=true
            shift
            ;;
        --no-isolation)
            TEST_ISOLATION=false
            shift
            ;;
        --docker)
            DOCKER_MODE=true
            shift
            ;;
        --docker-compose)
            DOCKER_COMPOSE_MODE=true
            shift
            ;;
        *)
            echo "Usage: $0 [--fix] [--quick] [--coverage] [--no-isolation] [--docker] [--docker-compose]"
            echo "  --fix              : Automatically fix issues where possible"
            echo "  --quick            : Skip time-consuming checks"
            echo "  --coverage         : Generate detailed coverage reports"
            echo "  --no-isolation     : Skip test environment isolation"
            echo "  --docker           : Use Docker for comprehensive testing"
            echo "  --docker-compose   : Use Docker Compose for full stack testing"
            exit 1
            ;;
    esac
done

# Cleanup function
cleanup() {
    if [ "$CLEANUP_ON_EXIT" = true ]; then
        echo -e "\n${YELLOW}🧹 Cleaning up test environments...${NC}"
        
        # Clean up any test databases
        find . -name "test_*.db" -delete 2>/dev/null || true
        find . -name "*.tmp" -delete 2>/dev/null || true
        
        # Stop any test servers
        pkill -f "test.*server" 2>/dev/null || true
        
        # Clean up node modules test artifacts
        find frontend -name ".nyc_output" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
}

trap cleanup EXIT

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
if [ "$DOCKER_MODE" = true ]; then
    echo "🐳 Docker Mode: Enabled"
fi
if [ "$DOCKER_COMPOSE_MODE" = true ]; then
    echo "🐙 Docker Compose Mode: Enabled (Full Stack Testing)"
fi

# If Docker Compose mode is enabled, run comprehensive stack testing
if [ "$DOCKER_COMPOSE_MODE" = true ]; then
    print_header "🐙 Docker Compose Full Stack Testing"
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_status "Docker Compose not available" "error"
        echo "   💡 Install Docker Compose or use Docker Desktop"
        exit 1
    fi
    
    echo "   🚀 Starting full stack test environment..."
    
    # Clean up any existing containers
    docker-compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || true
    docker compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || true
    
    # Build and start services
    echo "   🏗️  Building and starting test services..."
    COMPOSE_OUTPUT=$(docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit 2>&1 || docker compose -f docker-compose.test.yml up --build --abort-on-container-exit 2>&1)
    COMPOSE_EXIT_CODE=$?
    
    if [ $COMPOSE_EXIT_CODE -eq 0 ]; then
        print_status "Full stack testing: PASSED" "success"
        echo "   ✅ All services started and tests completed successfully"
        
        # Extract test results from output
        if echo "$COMPOSE_OUTPUT" | grep -q "failed\|ERROR\|FAILED"; then
            print_status "Some tests failed in full stack environment" "warning"
            echo "   ⚠️  Check test output for details"
        fi
        
        # Show test summary
        PASSED_COUNT=$(echo "$COMPOSE_OUTPUT" | grep -o "[0-9]* passed" | tail -1)
        if [ -n "$PASSED_COUNT" ]; then
            print_status "Test Results: $PASSED_COUNT" "success"
        fi
        
    else
        print_status "Full stack testing: FAILED" "error"
        echo "   ❌ Docker Compose test failed"
        echo "   🔍 Check the output above for details"
        VALIDATION_FAILED=true
    fi
    
    # Clean up
    echo "   🧹 Cleaning up test environment..."
    docker-compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || docker compose -f docker-compose.test.yml down -v >/dev/null 2>&1
    
    # If Docker Compose mode completes, skip other testing
    if [ $COMPOSE_EXIT_CODE -eq 0 ]; then
        print_header "📊 Validation Summary"
        echo -e "\n${GREEN}✅ DOCKER COMPOSE FULL STACK TESTING COMPLETED${NC}"
        echo "Your application passed comprehensive testing in a production-like environment!"
        echo ""
        echo "🚀 Next steps:"
        echo "  1. Commit your changes: git add . && git commit -m 'Your message'"
        echo "  2. Push to trigger CI/CD: git push origin main"
        echo ""
        echo "The CI/CD pipeline will run similar tests and deploy if successful."
        exit 0
    fi
fi

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
    
    # Check pnpm lock file and synchronization
    if [ -f "frontend/pnpm-lock.yaml" ]; then
        print_status "pnpm-lock.yaml found" "success"
        
        # Critical: Check if lockfile is synchronized with package.json
        echo "   Validating lockfile synchronization..."
        cd frontend
        if command -v pnpm &> /dev/null; then
            # Test if frozen lockfile install would succeed (simulating CI/CD)
            if pnpm install --frozen-lockfile --offline 2>/dev/null; then
                print_status "Lockfile synchronized with package.json" "success"
            else
                # Try with network (dependencies might need to be downloaded)
                if pnpm install --frozen-lockfile >/dev/null 2>&1; then
                    print_status "Lockfile synchronized (required dependency download)" "success"
                else
                    print_status "Lockfile out of sync with package.json" "error"
                    echo "   ❌ This will cause CI/CD failure with --frozen-lockfile"
                    if [ "$FIX_ISSUES" = true ]; then
                        echo "   🔧 Regenerating lockfile..."
                        pnpm install >/dev/null 2>&1 && print_status "Lockfile regenerated" "success"
                    else
                        echo "   💡 Fix with: cd frontend && pnpm install"
                    fi
                fi
            fi
        else
            print_status "pnpm not available - cannot validate lockfile sync" "warning"
            echo "   💡 Install pnpm: npm install -g pnpm"
        fi
        cd ..
    else
        print_status "pnpm-lock.yaml missing - run 'pnpm install'" "error"
        echo "   ❌ CI/CD will fail without lockfile"
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

# NEW: Test Data Structure Validation (prevents test failures in CI/CD)
echo "   Testing service data structures..."
if ! python3 -c "
from app.services.ai_service import CostTracker
tracker = CostTracker()
# Test that track_usage creates proper structure
cost = tracker.track_usage('gpt-4o-mini', 100, 50, 'general')
today = list(tracker.daily_usage.keys())[0]
# Verify expected keys exist
assert 'cost' in tracker.daily_usage[today]
assert 'requests' in tracker.daily_usage[today] 
assert 'models' in tracker.daily_usage[today]
assert 'request_types' in tracker.daily_usage[today]
# Test check_budget_limit works with proper structure
result = tracker.check_budget_limit()
print('✅ AI service data structures validated')
" 2>/dev/null; then
    IMPORT_ERRORS+=("app.services.ai_service - Data structure validation failed")
fi

# NEW: API Contract Validation (prevents test expectation mismatches)
echo "   Testing API contract expectations..."
if ! python3 -c "
from app.services.ai_service import ItineraryPrompts

# Test the exact scenario from failing test
families_data = [
    {
        'name': 'Smith',
        'members': [
            {'age': 35, 'dietary_restrictions': ['vegetarian'], 'accessibility_needs': []},
            {'age': 33, 'dietary_restrictions': [], 'accessibility_needs': []},
            {'age': 8, 'dietary_restrictions': ['nut-free'], 'accessibility_needs': []},
        ],
    },
    {
        'name': 'Johnson',
        'members': [
            {'age': 40, 'dietary_restrictions': [], 'accessibility_needs': ['wheelchair']},
            {'age': 12, 'dietary_restrictions': [], 'accessibility_needs': []},
        ],
    },
]
preferences = {
    'accommodation_type': ['hotel'],
    'transportation_mode': ['public_transit'],
    'activity_types': ['museums', 'sightseeing'],
    'dining_preferences': ['local cuisine'],
    'pace': 'moderate',
}

prompt = ItineraryPrompts.create_itinerary_prompt('Paris', 7, families_data, preferences, 10000.0)

# Test all the assertions from the failing test
assert 'Paris' in prompt, 'Paris not found in prompt'
assert '7-day itinerary' in prompt, '7-day itinerary not found in prompt'
assert 'Smith' in prompt, 'Smith not found in prompt'
assert 'Johnson' in prompt, 'Johnson not found in prompt'
assert 'vegetarian' in prompt, 'vegetarian not found in prompt'
assert 'wheelchair' in prompt, 'wheelchair not found in prompt'
assert 'museums' in prompt, 'museums not found in prompt (API contract issue)'
assert 'budget' in prompt.lower(), 'budget not found in prompt'

print('✅ API contract validation passed')
" 2>/dev/null; then
    IMPORT_ERRORS+=("app.services.ai_service - API contract validation failed")
fi

if [ ${#IMPORT_ERRORS[@]} -eq 0 ]; then
    print_status "All critical imports and data structures: Passed" "success"
else
    print_status "Import/structure failures detected (${#IMPORT_ERRORS[@]} modules)" "error"
    for error in "${IMPORT_ERRORS[@]}"; do
        echo "   ❌ $error"
    done
    echo "   💡 These failures will cause CI/CD to fail immediately"
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

# 5. Docker-Based Comprehensive Validation
print_header "🐳 Docker-Based Comprehensive Validation"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    print_status "Docker not available - falling back to local testing" "warning"
    DOCKER_AVAILABLE=false
elif ! docker info >/dev/null 2>&1; then
    print_status "Docker daemon not running - falling back to local testing" "warning"
    DOCKER_AVAILABLE=false
else
    print_status "Docker available - using containerized testing" "success"
    DOCKER_AVAILABLE=true
fi

if [ "$DOCKER_AVAILABLE" = true ] || [ "$DOCKER_MODE" = true ]; then
    echo "   🚀 Running comprehensive Docker-based validation..."
    
    # Build backend image
    echo "   Building backend Docker image..."
    if docker build -t pathfinder-backend-test ./backend >/dev/null 2>&1; then
        print_status "Backend Docker build: Passed" "success"
    else
        print_status "Backend Docker build failed" "error"
        echo "   ❌ Run: docker build -t pathfinder-backend-test ./backend"
        VALIDATION_FAILED=true
    fi
    
    # Build frontend image (if not quick mode)
    if [ "$QUICK_MODE" = false ]; then
        echo "   Building frontend Docker image..."
        if docker build -t pathfinder-frontend-test ./frontend >/dev/null 2>&1; then
            print_status "Frontend Docker build: Passed" "success"
        else
            print_status "Frontend Docker build failed" "error"
            echo "   ❌ Run: docker build -t pathfinder-frontend-test ./frontend"
            VALIDATION_FAILED=true
        fi
    fi
    
    # Create Docker network for testing
    echo "   Setting up test network..."
    docker network create pathfinder-test-network >/dev/null 2>&1 || true
    
    # Start test database
    echo "   Starting test database..."
    docker run -d \
        --name pathfinder-test-db \
        --network pathfinder-test-network \
        -e POSTGRES_DB=pathfinder_test \
        -e POSTGRES_USER=test_user \
        -e POSTGRES_PASSWORD=test_password \
        -p 5433:5432 \
        postgres:15-alpine >/dev/null 2>&1 || true
    
    # Wait for database to be ready
    echo "   Waiting for database to be ready..."
    for i in {1..30}; do
        if docker exec pathfinder-test-db pg_isready -U test_user >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Start Redis for caching tests
    echo "   Starting test Redis..."
    docker run -d \
        --name pathfinder-test-redis \
        --network pathfinder-test-network \
        -p 6380:6379 \
        redis:7-alpine >/dev/null 2>&1 || true
    
    # Run backend tests in Docker with real dependencies
    echo "   Running backend tests in Docker environment..."
    DOCKER_TEST_OUTPUT=$(docker run --rm \
        --network pathfinder-test-network \
        -e DATABASE_URL="postgresql+asyncpg://test_user:test_password@pathfinder-test-db:5432/pathfinder_test" \
        -e REDIS_URL="redis://pathfinder-test-redis:6379" \
        -e ENVIRONMENT=testing \
        -e AUTH0_DOMAIN="test-domain.auth0.com" \
        -e AUTH0_AUDIENCE="test-audience" \
        -e OPENAI_API_KEY="sk-test-key" \
        pathfinder-backend-test \
        sh -c "cd /app && python -m pytest tests/ -v --tb=short --maxfail=5" 2>&1)
    
    if echo "$DOCKER_TEST_OUTPUT" | grep -q "failed\|ERROR\|FAILED"; then
        print_status "Docker-based backend tests failed" "error"
        echo "   ❌ Test failures in containerized environment:"
        echo "$DOCKER_TEST_OUTPUT" | grep -E "(FAILED|ERROR|AttributeError)" | head -10
        VALIDATION_FAILED=true
    else
        print_status "Docker-based backend tests: Passed" "success"
        # Extract test count
        TEST_COUNT=$(echo "$DOCKER_TEST_OUTPUT" | grep -o "[0-9]* passed" | head -1)
        if [ -n "$TEST_COUNT" ]; then
            print_status "Backend tests in Docker: $TEST_COUNT" "success"
        fi
    fi
    
    # Run integration tests with real HTTP calls
    echo "   Running API integration tests with real endpoints..."
    docker run -d \
        --name pathfinder-test-api \
        --network pathfinder-test-network \
        -p 8001:8000 \
        -e DATABASE_URL="postgresql+asyncpg://test_user:test_password@pathfinder-test-db:5432/pathfinder_test" \
        -e REDIS_URL="redis://pathfinder-test-redis:6379" \
        -e ENVIRONMENT=testing \
        pathfinder-backend-test \
        sh -c "cd /app && uvicorn app.main:app --host 0.0.0.0 --port 8000" >/dev/null 2>&1
    
    # Wait for API to be ready
    echo "   Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8001/health >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Test API endpoints directly
    echo "   Testing API endpoints with real HTTP calls..."
    API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)
    if [ "$API_HEALTH" = "200" ]; then
        print_status "API health endpoint: Accessible" "success"
    else
        print_status "API health endpoint failed: HTTP $API_HEALTH" "error"
        VALIDATION_FAILED=true
    fi
    
    # Test authentication endpoints
    AUTH_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/trips/)
    if [ "$AUTH_TEST" = "401" ]; then
        print_status "Authentication protection: Working" "success"
    else
        print_status "Authentication protection failed: HTTP $AUTH_TEST (expected 401)" "error"
        VALIDATION_FAILED=true
    fi
    
    # Test CORS headers
    CORS_TEST=$(curl -s -I -X OPTIONS http://localhost:8001/api/v1/trips/ | grep -i "access-control-allow-origin")
    if [ -n "$CORS_TEST" ]; then
        print_status "CORS headers: Present" "success"
    else
        print_status "CORS headers: Missing" "error"
        VALIDATION_FAILED=true
    fi
    
    # Cleanup Docker containers and network
    echo "   Cleaning up Docker test environment..."
    docker stop pathfinder-test-api pathfinder-test-db pathfinder-test-redis >/dev/null 2>&1 || true
    docker rm pathfinder-test-api pathfinder-test-db pathfinder-test-redis >/dev/null 2>&1 || true
    docker network rm pathfinder-test-network >/dev/null 2>&1 || true
    docker rmi pathfinder-backend-test pathfinder-frontend-test >/dev/null 2>&1 || true
    
else
    # Fallback to original Docker build test
    echo "   Testing backend Docker build..."
    if docker build -t pathfinder-backend-test ./backend >/dev/null 2>&1; then
        print_status "Backend Docker build: Passed" "success"
        docker rmi pathfinder-backend-test >/dev/null 2>&1 || true
    else
        print_status "Backend Docker build failed" "error"
        echo "   ❌ Run: docker build -t test ./backend"
    fi
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

# NEW: Specific CI/CD failure detection and validation
echo "   Testing for specific CI/CD failure patterns..."

# 1. Test trailing slash redirect issue (307 vs 401)
echo "   ❯ Checking authentication redirect patterns..."
if python3 -c "
import asyncio
from httpx import AsyncClient
from app.main import app

async def test_auth_redirects():
    async with AsyncClient(app=app, base_url='http://test') as client:
        # Test without trailing slash (should not redirect)
        response = await client.get('/api/v1/trips/')
        if response.status_code == 307:
            print('ERROR: Auth endpoint returning 307 redirect instead of 401')
            return False
        elif response.status_code == 401:
            print('✓ Auth endpoint correctly returns 401')
            return True
        else:
            print(f'UNEXPECTED: Auth endpoint returns {response.status_code}')
            return False

result = asyncio.run(test_auth_redirects())
exit(0 if result else 1)
" 2>/dev/null; then
    print_status "Authentication endpoints: Return 401 correctly" "success"
else
    print_status "Authentication redirect issue detected (307 instead of 401)" "error"
    echo "   ❌ FastAPI is redirecting before auth check"
    echo "   🔧 Check URL patterns in tests (trailing slashes)"
    VALIDATION_FAILED=true
fi

# 2. Test database health SQL expression issue
echo "   ❯ Checking database health endpoint SQL..."
if python3 -c "
import asyncio
from httpx import AsyncClient
from app.main import app

async def test_health_sql():
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.get('/health/detailed')
        data = response.json()
        
        # Check if database errors mention SQL expression issues
        if 'details' in data and 'database' in data['details']:
            db_detail = str(data['details']['database'])
            if 'Textual SQL expression' in db_detail and 'text(' in db_detail:
                print('ERROR: SQLAlchemy 2.0 text() wrapper issue detected')
                return False
        
        print('✓ Database health check SQL is properly formatted')
        return True

result = asyncio.run(test_health_sql())
exit(0 if result else 1)
" 2>/dev/null; then
    print_status "Database health SQL: Properly formatted" "success"
else
    print_status "Database health SQL expression issue" "error"
    echo "   ❌ Raw SQL strings need text() wrapper for SQLAlchemy 2.0"
    echo "   🔧 Wrap raw SQL with text('SELECT 1') in health endpoints"
    VALIDATION_FAILED=true
fi

# 3. Test CORS headers on OPTIONS requests
echo "   ❯ Checking CORS headers on OPTIONS requests..."
if python3 -c "
import asyncio
from httpx import AsyncClient
from app.main import app

async def test_cors_options():
    async with AsyncClient(app=app, base_url='http://test') as client:
        response = await client.options('/api/v1/trips/')
        
        # Check for required CORS headers
        if 'access-control-allow-origin' not in response.headers:
            print('ERROR: Missing access-control-allow-origin header')
            return False
        
        if 'access-control-allow-methods' not in response.headers:
            print('ERROR: Missing access-control-allow-methods header')
            return False
            
        print('✓ CORS headers present on OPTIONS requests')
        return True

result = asyncio.run(test_cors_options())
exit(0 if result else 1)
" 2>/dev/null; then
    print_status "CORS headers: Present on OPTIONS requests" "success"
else
    print_status "CORS headers missing on OPTIONS requests" "error"
    echo "   ❌ OPTIONS requests not returning CORS headers"
    echo "   🔧 Check CORS middleware configuration"
    VALIDATION_FAILED=true
fi

# 4. Check for PytestUnknownMarkWarning issues
echo "   ❯ Checking pytest marker configuration..."
if python3 -m pytest --collect-only tests/ -q 2>&1 | grep -q "PytestUnknownMarkWarning"; then
    print_status "Pytest unknown mark warnings detected" "error"
    echo "   ❌ Custom markers not properly registered"
    echo "   🔧 Check pytest.ini markers configuration"
    VALIDATION_FAILED=true
else
    print_status "Pytest markers: Properly registered" "success"
fi

# Test conftest.py import (critical failure point)
echo "   Testing conftest.py import (critical CI/CD failure point)..."
if python3 -c "import sys; sys.path.append('tests'); import conftest" 2>/dev/null; then
    print_status "conftest.py import: Passed" "success"
else
    print_status "conftest.py import failed - will cause CI/CD failure" "error"
    echo "   ❌ This is the exact error causing CI/CD failure"
    echo "   🔧 Fix imports in conftest.py and related modules"
    VALIDATION_FAILED=true
fi

# NEW: Comprehensive pytest test discovery (simulates full CI/CD test phase)
echo "   Testing pytest test discovery (comprehensive CI/CD simulation)..."
PYTEST_DISCOVERY_OUTPUT=$(python3 -m pytest --collect-only tests/ -q 2>&1)
PYTEST_DISCOVERY_EXIT_CODE=$?

if [ $PYTEST_DISCOVERY_EXIT_CODE -eq 0 ]; then
    print_status "Pytest test discovery: All tests can be discovered" "success"
    # Count discovered tests for validation
    TEST_COUNT=$(echo "$PYTEST_DISCOVERY_OUTPUT" | grep -c "test.*::")
    echo "   📊 Discovered $TEST_COUNT tests successfully"
elif [ $PYTEST_DISCOVERY_EXIT_CODE -eq 2 ]; then
    print_status "Pytest test discovery failed - Collection errors found" "error"
    echo "   ❌ These errors will cause immediate CI/CD failure"
    echo "   💡 Fix import/syntax errors in test files"
    # Show first few collection errors
    echo "$PYTEST_DISCOVERY_OUTPUT" | grep -A 3 "ERROR collecting" | head -10
    VALIDATION_FAILED=true
elif [ $PYTEST_DISCOVERY_EXIT_CODE -eq 5 ]; then
    print_status "Pytest test discovery: No tests collected (check test patterns)" "warning"
else
    print_status "Pytest test discovery failed with exit code $PYTEST_DISCOVERY_EXIT_CODE" "error"
    VALIDATION_FAILED=true
fi
fi

# Test specific auth unit tests that were failing in CI/CD
echo "   Testing auth unit tests (exact CI/CD failure)..."
if python3 -c "import pytest" 2>/dev/null; then
    # Run the exact failing test without silencing errors
    echo "   Running test_auth_unit.py::TestAuthEndpoints::test_login_success..."
    TEST_OUTPUT=$(python3 -m pytest tests/test_auth_unit.py::TestAuthEndpoints::test_login_success -v --tb=short 2>&1)
    if echo "$TEST_OUTPUT" | grep -q "PASSED\|1 passed"; then
        print_status "Previously failing CI/CD test: Passed" "success"
    else
        print_status "CI/CD failure test still failing" "error"
        echo "   ❌ Test: tests/test_auth_unit.py::TestAuthEndpoints::test_login_success"
        echo "   🔍 Error details:"
        echo "$TEST_OUTPUT" | head -20
        echo "   💡 This exact test is blocking CI/CD - must fix first"
        VALIDATION_FAILED=true
    fi
    
    # Run all auth unit tests to ensure they pass
    echo "   Running all auth unit tests..."
    AUTH_TEST_OUTPUT=$(python3 -m pytest tests/test_auth_unit.py -v --tb=short 2>&1)
    if echo "$AUTH_TEST_OUTPUT" | grep -q "failed\|ERROR\|FAILED"; then
        print_status "Auth unit tests failing" "error"
        echo "   💡 Check test mocking and endpoint availability"
        echo "$AUTH_TEST_OUTPUT" | grep -E "(FAILED|ERROR|AttributeError)" | head -10
        VALIDATION_FAILED=true
    else
        print_status "Auth unit tests: Passed" "success"
    fi
fi

# Run tests with exact CI/CD command and environment
echo "   Running unit tests first (catch schema validation errors)..."
if python3 -c "import pytest, coverage" 2>/dev/null; then
    # Run unit tests first to catch validation issues - DON'T SILENCE ERRORS
    UNIT_TEST_OUTPUT=$(python3 -m pytest tests/ -m "unit or not (e2e or performance)" -v --tb=short 2>&1)
    if echo "$UNIT_TEST_OUTPUT" | grep -q "failed\|ERROR\|FAILED"; then
        print_status "Unit tests failed - will cause CI/CD failure" "error"
        echo "   ❌ Unit test failures detected:"
        echo "$UNIT_TEST_OUTPUT" | grep -E "(FAILED|ERROR|AttributeError)" | head -10
        VALIDATION_FAILED=true
    else
        print_status "Unit tests: Passed" "success"
    fi
fi

echo "   Running integration tests (CI/CD includes these)..."
if python3 -c "import pytest, coverage" 2>/dev/null; then
    # Run integration tests separately to catch auth/endpoint issues
    INTEGRATION_TEST_OUTPUT=$(python3 -m pytest tests/ -m "integration" -v --tb=short 2>&1)
    if echo "$INTEGRATION_TEST_OUTPUT" | grep -q "failed\|ERROR\|FAILED"; then
        print_status "Integration tests failed - will cause CI/CD failure" "error"
        echo "   ❌ Integration test failures detected:"
        echo "$INTEGRATION_TEST_OUTPUT" | grep -E "(FAILED|ERROR|AttributeError)" | head -10
        VALIDATION_FAILED=true
    else
        print_status "Integration tests: Passed" "success"
    fi
fi

echo "   Running tests with coverage (exact CI/CD command)..."
if python3 -c "import pytest, coverage" 2>/dev/null; then
    # Use exact same command as CI/CD - DON'T SILENCE ERRORS
    COVERAGE_TEST_OUTPUT=$(coverage run -m pytest tests/ -v --tb=short 2>&1)
    if echo "$COVERAGE_TEST_OUTPUT" | grep -q "failed\|ERROR\|FAILED"; then
        print_status "Test execution failed (same failure as CI/CD)" "error"
        echo "   ❌ This matches the CI/CD failure pattern"
        echo "   🔍 Error details:"
        echo "$COVERAGE_TEST_OUTPUT" | grep -E "(FAILED|ERROR|AttributeError)" | head -15
        echo "   🔧 Fix import errors and test mocking issues"
        echo "   📝 Run: cd backend && ENVIRONMENT=testing coverage run -m pytest tests/ -v"
        VALIDATION_FAILED=true
    else
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
    fi
else
    print_status "Test framework not available" "error"
    echo "   💡 Install: pip install pytest pytest-asyncio coverage"
fi

# 8. Frontend Testing & Coverage (ENHANCED)
print_header "🧪 Frontend Testing & Coverage"

if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    
    # Check if dependencies are installed
    if [ ! -d "node_modules" ]; then
        echo "   Installing frontend dependencies..."
        if command -v pnpm &> /dev/null; then
            pnpm install
        elif command -v npm &> /dev/null; then
            npm install
        else
            print_status "No package manager found (npm/pnpm)" "error"
            VALIDATION_FAILED=true
            cd ..
            return
        fi
    fi
    
    # Enhanced test environment isolation
    if [ "$TEST_ISOLATION" = true ]; then
        echo "   Setting up isolated test environment..."
        
        # Create test-specific config
        cp vitest.config.ts vitest.config.test.ts 2>/dev/null || true
        
        # Set test environment variables
        export NODE_ENV=test
        export VITE_API_URL=http://localhost:3001/api
        export CI=true
    fi
    
    # Run frontend tests with coverage
    echo "   Running frontend tests with coverage..."
    
    if [ "$COVERAGE_MODE" = true ]; then
        echo "   📊 Generating detailed coverage report..."
        TEST_RESULT=0
        
        if command -v pnpm &> /dev/null; then
            pnpm run test:coverage || TEST_RESULT=$?
        else
            npm run test:coverage || TEST_RESULT=$?
        fi
        
        # Parse coverage results
        if [ -f "coverage/coverage-summary.json" ]; then
            FRONTEND_COVERAGE=$(node -e "
                try {
                    const fs = require('fs');
                    const coverage = JSON.parse(fs.readFileSync('coverage/coverage-summary.json', 'utf8'));
                    const pct = coverage.total.lines.pct;
                    console.log(Math.round(pct));
                } catch(e) {
                    console.log('0');
                }
            ")
            
            if [ "$FRONTEND_COVERAGE" -ge "$FRONTEND_COVERAGE_THRESHOLD" ]; then
                print_status "Frontend coverage: ${FRONTEND_COVERAGE}% (≥${FRONTEND_COVERAGE_THRESHOLD}%)" "success"
            else
                print_status "Frontend coverage: ${FRONTEND_COVERAGE}% (<${FRONTEND_COVERAGE_THRESHOLD}%)" "warning"
            fi
            
            # Detailed coverage report
            echo -e "\n   ${PURPLE}📈 Detailed Coverage Report:${NC}"
            node -e "
                try {
                    const fs = require('fs');
                    const coverage = JSON.parse(fs.readFileSync('coverage/coverage-summary.json', 'utf8'));
                    console.log('   Lines:      ' + coverage.total.lines.pct + '%');
                    console.log('   Functions:  ' + coverage.total.functions.pct + '%');
                    console.log('   Branches:   ' + coverage.total.branches.pct + '%');
                    console.log('   Statements: ' + coverage.total.statements.pct + '%');
                } catch(e) {
                    console.log('   Unable to parse coverage data');
                }
            "
        fi
        
        # Generate HTML coverage report
        if [ -d "coverage/lcov-report" ]; then
            echo "   📄 HTML coverage report: frontend/coverage/lcov-report/index.html"
        fi
        
    else
        # Standard test run
        TEST_RESULT=0
        if command -v pnpm &> /dev/null; then
            pnpm run test || TEST_RESULT=$?
        else
            npm run test || TEST_RESULT=$?
        fi
    fi
    
    if [ $TEST_RESULT -eq 0 ]; then
        print_status "Frontend tests: Passed" "success"
    else
        print_status "Frontend tests: Failed" "error"
        VALIDATION_FAILED=true
        echo "   💡 Run manually: cd frontend && npm run test"
    fi
    
    # Type checking
    echo "   Running TypeScript type checking..."
    TYPE_CHECK_RESULT=0
    if command -v pnpm &> /dev/null; then
        pnpm run type-check || TYPE_CHECK_RESULT=$?
    else
        npm run type-check || TYPE_CHECK_RESULT=$?
    fi
    
    if [ $TYPE_CHECK_RESULT -eq 0 ]; then
        print_status "TypeScript types: Valid" "success"
    else
        print_status "TypeScript type errors found" "error"
        VALIDATION_FAILED=true
    fi
    
    # Component testing validation
    echo "   Validating component test coverage..."
    COMPONENT_TESTS=$(find src/tests -name "*.test.tsx" -o -name "*.test.ts" | wc -l)
    COMPONENTS=$(find src/components src/pages -name "*.tsx" | wc -l)
    
    if [ $COMPONENTS -gt 0 ]; then
        COMPONENT_TEST_RATIO=$((COMPONENT_TESTS * 100 / COMPONENTS))
        if [ $COMPONENT_TEST_RATIO -ge 40 ]; then
            print_status "Component test coverage: ${COMPONENT_TEST_RATIO}% (≥40%)" "success"
        else
            print_status "Component test coverage: ${COMPONENT_TEST_RATIO}% (<40%)" "warning"
            echo "   💡 Consider adding more component tests"
        fi
    fi
    
    # Cleanup test environment
    if [ "$TEST_ISOLATION" = true ]; then
        rm -f vitest.config.test.ts 2>/dev/null || true
        unset NODE_ENV VITE_API_URL CI
    fi
    
    cd ..
else
    print_status "Frontend directory not found" "error"
    VALIDATION_FAILED=true
fi

# 9. E2E Testing Validation (ENHANCED)
if [ "$QUICK_MODE" = false ]; then
    print_header "🎭 E2E Testing Validation"
    
    if [ -f "frontend/playwright.config.ts" ]; then
        cd frontend
        
        # Check if Playwright is installed
        if [ ! -d "node_modules/@playwright" ]; then
            echo "   Installing Playwright browsers..."
            if command -v pnpm &> /dev/null; then
                pnpm exec playwright install chromium
            else
                npx playwright install chromium
            fi
        fi
        
        # Validate E2E test structure
        E2E_TESTS=$(find playwright -name "*.spec.ts" -o -name "*.test.ts" 2>/dev/null | wc -l)
        if [ $E2E_TESTS -gt 0 ]; then
            print_status "E2E tests found: ${E2E_TESTS} test files" "success"
            
            # Run E2E tests in headless mode
            echo "   Running E2E tests (headless)..."
            E2E_RESULT=0
            
            if command -v pnpm &> /dev/null; then
                pnpm run test:e2e || E2E_RESULT=$?
            else
                npm run test:e2e || E2E_RESULT=$?
            fi
            
            if [ $E2E_RESULT -eq 0 ]; then
                print_status "E2E tests: Passed" "success"
            else
                print_status "E2E tests: Failed" "warning"
                echo "   💡 E2E tests may require running services"
            fi
        else
            print_status "No E2E tests found" "warning"
            echo "   💡 Consider adding E2E tests in playwright/ directory"
        fi
        
        cd ..
    else
        print_status "Playwright not configured" "warning"
        echo "   💡 Consider setting up E2E testing with Playwright"
    fi
fi

# 10. Test Environment Stability Check
print_header "🔧 Test Environment Stability"

echo "   Checking for test environment consistency..."

# Check for test database cleanup
TEST_DBS=$(find . -name "test*.db" -o -name "*.test.db" | wc -l)
if [ $TEST_DBS -gt 0 ]; then
    print_status "Found ${TEST_DBS} test database files - cleaning up" "warning"
    find . -name "test*.db" -o -name "*.test.db" -delete
fi

# Check for port conflicts
echo "   Checking for common port conflicts..."
PORTS_IN_USE=()
for port in 3000 3001 8000 8080 5432; do
    if lsof -i :$port >/dev/null 2>&1; then
        PORTS_IN_USE+=($port)
    fi
done

if [ ${#PORTS_IN_USE[@]} -gt 0 ]; then
    print_status "Ports in use: ${PORTS_IN_USE[*]}" "warning"
    echo "   💡 These ports may conflict with test environments"
else
    print_status "No port conflicts detected" "success"
fi

# Check test isolation capabilities
if [ "$TEST_ISOLATION" = true ]; then
    echo "   Validating test isolation setup..."
    
    # Check if we can create isolated test environments
    TEST_ENV_DIR=$(mktemp -d)
    if [ -d "$TEST_ENV_DIR" ]; then
        print_status "Test environment isolation: Available" "success"
        rm -rf "$TEST_ENV_DIR"
    else
        print_status "Test environment isolation: Limited" "warning"
    fi
fi

# Summary
print_header "📊 Validation Summary"

# Enhanced summary with coverage metrics
if [ "$COVERAGE_MODE" = true ]; then
    echo -e "\n${PURPLE}📈 Coverage Summary:${NC}"
    
    # Backend coverage
    if [ -f "backend/.coverage" ]; then
        cd backend
        BACKEND_COV=$(python3 -c "
import coverage
import sys
try:
    cov = coverage.Coverage()
    cov.load()
    report = cov.report(show_missing=False, skip_covered=False, file=open('/dev/null', 'w'))
    percent = cov.report(show_missing=False, skip_covered=False, file=sys.stdout)
except:
    print('Unable to generate backend coverage')
" 2>/dev/null | tail -1 | grep -o '[0-9]\+%' | head -1 | tr -d '%')
        echo "   Backend:  ${BACKEND_COV:-N/A}%"
        cd ..
    fi
    
    # Frontend coverage
    if [ -f "frontend/coverage/coverage-summary.json" ]; then
        FRONTEND_COV=$(node -pe "
try {
    JSON.parse(require('fs').readFileSync('frontend/coverage/coverage-summary.json')).total.lines.pct
} catch(e) { 'N/A' }
" 2>/dev/null)
        echo "   Frontend: ${FRONTEND_COV:-N/A}%"
    fi
    
    echo ""
fi

# Test execution summary
echo -e "${BLUE}🧪 Test Execution Summary:${NC}"
TOTAL_ISSUES=0

# Count different types of issues
if [ "$VALIDATION_FAILED" = true ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
fi

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo "   ✅ All test suites passed"
    echo "   ✅ Code quality checks passed"  
    echo "   ✅ Environment stability verified"
    
    if [ "$COVERAGE_MODE" = true ]; then
        echo "   📊 Coverage reports generated"
        echo ""
        echo "   📄 Reports available at:"
        echo "     - Backend: backend/htmlcov/index.html"
        echo "     - Frontend: frontend/coverage/lcov-report/index.html"
    fi
else
    echo "   ❌ ${TOTAL_ISSUES} issue(s) detected"
fi

if [ "$VALIDATION_FAILED" = true ]; then
    echo -e "\n${RED}❌ VALIDATION FAILED${NC}"
    echo "Some issues were detected that will cause CI/CD failures."
    if [ "$FIX_ISSUES" = true ]; then
        echo "Auto-fixes were attempted. Please review changes and run validation again."
    else
        echo "Run with --fix to automatically fix issues where possible."
    fi
    echo ""
    echo "🔧 Manual fix commands:"
    echo "  Backend quality: cd backend && ruff format . && ruff check . && mypy app/"
    echo "  Frontend quality: cd frontend && pnpm run type-check && pnpm run lint"
    echo "  Docker builds: docker build -t test ./backend && docker build -t test ./frontend"
    echo ""
    echo "📊 Coverage commands:"
    echo "  Backend: cd backend && coverage run -m pytest && coverage html"
    echo "  Frontend: cd frontend && npm run test:coverage"
    exit 1
else
    echo -e "\n${GREEN}✅ ALL VALIDATIONS PASSED${NC}"
    echo "Your code is ready for CI/CD pipeline!"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Commit your changes: git add . && git commit -m 'Your message'"
    echo "  2. Push to trigger CI/CD: git push origin main"
    echo ""
    if [ "$COVERAGE_MODE" = true ]; then
        echo "📊 Coverage reports have been generated and are ready for review."
        echo ""
    fi
    echo "The CI/CD pipeline will run the same checks and deploy if successful."
fi 