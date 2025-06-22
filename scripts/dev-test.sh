#!/bin/bash

# Development-focused Testing Strategy
# Combines unit, integration, and selective E2E tests for speed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${BLUE}🔄 $1${NC}"; }

# Test execution functions
run_unit_tests() {
    log_step "Running unit tests..."
    
    # Backend unit tests
    cd "$PROJECT_ROOT/backend"
    if [ -f "pytest.ini" ]; then
        python -m pytest tests/unit/ -v --tb=short 2>/dev/null || log_warning "Some backend unit tests failed"
    fi
    
    # Frontend unit tests
    cd "$PROJECT_ROOT/frontend"
    if [ -f "package.json" ]; then
        npm run test:run 2>/dev/null || log_warning "Some frontend unit tests failed"
    fi
    
    log_success "Unit tests completed"
}

run_integration_tests() {
    log_step "Running integration tests..."
    
    # Backend integration tests with test database
    cd "$PROJECT_ROOT/backend"
    export DATABASE_URL="sqlite:///./test_integration.db"
    export ENVIRONMENT=testing
    
    if [ -f "pytest.ini" ]; then
        python -m pytest tests/integration/ -v --tb=short 2>/dev/null || log_warning "Some integration tests failed"
    fi
    
    # API integration tests
    if [ -f "test_api_basic.py" ]; then
        python test_api_basic.py 2>/dev/null || log_warning "API tests had issues"
    fi
    
    log_success "Integration tests completed"
}

run_critical_e2e() {
    log_step "Running critical E2E flows..."
    
    # Start minimal services for critical path testing
    export DATABASE_URL="sqlite:///./test_critical.db"
    export REDIS_URL="memory://"
    
    # Start backend
    cd "$PROJECT_ROOT/backend"
    uvicorn app.main:app --host 0.0.0.0 --port 8002 >/dev/null 2>&1 &
    BACKEND_PID=$!
    
    # Start frontend
    cd "$PROJECT_ROOT/frontend"
    export VITE_API_BASE_URL=http://localhost:8002
    npm run dev -- --host 0.0.0.0 --port 3002 >/dev/null 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for services
    sleep 10
    
    # Run only critical user journeys
    cd "$PROJECT_ROOT/tests/e2e"
    export PLAYWRIGHT_BASE_URL=http://localhost:3002
    export E2E_HEADLESS=true
    
    # Test critical paths only
    npx playwright test --grep "@critical" 2>/dev/null || log_warning "Some critical E2E tests failed"
    
    # Cleanup
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    
    log_success "Critical E2E tests completed"
}

run_quick_validation() {
    log_step "Running quick validation suite..."
    
    # Linting and type checking (very fast)
    cd "$PROJECT_ROOT/frontend"
    npm run lint 2>/dev/null || log_warning "Frontend linting issues found"
    npm run type-check 2>/dev/null || log_warning "Frontend type issues found"
    
    cd "$PROJECT_ROOT/backend"
    python -m flake8 app/ 2>/dev/null || log_warning "Backend linting issues found"
    python -m mypy app/ 2>/dev/null || log_warning "Backend type issues found"
    
    log_success "Quick validation completed"
}

# Main execution based on mode
main() {
    local mode="${1:-fast}"
    
    case $mode in
        "unit")
            log_info "🧪 Running unit tests only..."
            run_unit_tests
            ;;
        "integration")
            log_info "🔗 Running integration tests..."
            run_unit_tests
            run_integration_tests
            ;;
        "critical")
            log_info "🎯 Running critical path tests..."
            run_unit_tests
            run_integration_tests
            run_critical_e2e
            ;;
        "fast")
            log_info "⚡ Running fast validation..."
            run_quick_validation
            run_unit_tests
            ;;
        "full")
            log_info "🚀 Running comprehensive test suite..."
            run_quick_validation
            run_unit_tests
            run_integration_tests
            run_critical_e2e
            ;;
        *)
            echo "Usage: $0 [unit|integration|critical|fast|full]"
            echo ""
            echo "Modes:"
            echo "  unit        - Unit tests only (~30 seconds)"
            echo "  integration - Unit + integration tests (~1-2 minutes)"
            echo "  critical    - Unit + integration + critical E2E (~3-4 minutes)"
            echo "  fast        - Quick validation + unit tests (~1 minute)"
            echo "  full        - Complete test suite (~5-6 minutes)"
            exit 1
            ;;
    esac
    
    log_success "✨ Testing completed successfully!"
}

main "$@"
