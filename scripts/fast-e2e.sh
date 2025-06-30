#!/bin/bash

# Fast E2E Testing - Native services with minimal Docker
# Startup time: ~30 seconds vs 2-3 minutes with full Docker

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
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

# Cleanup function
cleanup() {
    log_step "Cleaning up..."
    
    # Stop native processes
    if [ -f "$PROJECT_ROOT/backend/.server.pid" ]; then
        kill $(cat "$PROJECT_ROOT/backend/.server.pid") 2>/dev/null || true
        rm -f "$PROJECT_ROOT/backend/.server.pid"
    fi
    
    if [ -f "$PROJECT_ROOT/frontend/.server.pid" ]; then
        kill $(cat "$PROJECT_ROOT/frontend/.server.pid") 2>/dev/null || true
        rm -f "$PROJECT_ROOT/frontend/.server.pid"
    fi
    
    # Stop minimal Docker services
    docker-compose -f "$PROJECT_ROOT/docker-compose.minimal.yml" down --remove-orphans 2>/dev/null || true
}

trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if we can use Docker for databases only
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not available - will use SQLite for testing"
        export USE_SQLITE=true
    fi
    
    log_success "Prerequisites check completed"
}

# Start minimal external services (only databases)
start_external_services() {
    if [ "${USE_SQLITE:-false}" = "true" ]; then
        log_info "Using SQLite - no external services needed"
        return 0
    fi
    
    log_step "Starting minimal external services..."
    
    # Create minimal compose file on the fly
    cat > "$PROJECT_ROOT/docker-compose.minimal.yml" << 'EOF'
version: '3.8'
services:
  test-db:
    image: mongo:7.0
    ports:
      - "27019:27017"
    environment:
      - MONGO_INITDB_DATABASE=pathfinder_test
    volumes:
      - test-db-data:/data/db
    command: mongod --noauth --quiet

  test-redis:
    image: redis:7-alpine
    ports:
      - "6381:6379"
    command: redis-server --save "" --appendonly no --maxmemory 100mb

volumes:
  test-db-data:
EOF

    docker-compose -f "$PROJECT_ROOT/docker-compose.minimal.yml" up -d
    
    # Quick health check (max 15 seconds)
    log_step "Waiting for database to be ready..."
    for i in {1..15}; do
        # Get container ID more reliably
        DB_CONTAINER=$(docker-compose -f "$PROJECT_ROOT/docker-compose.minimal.yml" ps -q test-db)
        if [ -n "$DB_CONTAINER" ] && docker exec "$DB_CONTAINER" mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
            log_success "Database ready"
            break
        fi
        if [ $i -eq 15 ]; then
            log_warning "Database health check failed, continuing with SQLite fallback"
            export USE_SQLITE=true
            break
        fi
        echo -n "."
        sleep 1
    done
}

# Start backend natively
start_backend() {
    log_step "Starting backend service..."
    
    cd "$PROJECT_ROOT/backend"
    
    # Set test environment variables
    export ENVIRONMENT=testing
    export DEBUG=true
    export SECRET_KEY=fast_e2e_test_secret
    export CSRF_SECRET_KEY=fast_e2e_test_csrf_secret
    
    if [ "${USE_SQLITE:-false}" = "true" ]; then
        export DATABASE_URL="sqlite:///./test_e2e.db"
        export REDIS_URL="memory://"
        export COSMOS_DB_ENABLED=false
        log_info "Using SQLite database and in-memory Redis"
    else
        export DATABASE_URL="mongodb://localhost:27019/pathfinder_test"
        export REDIS_URL="redis://localhost:6381"
        export COSMOS_DB_ENABLED=false
        log_info "Using MongoDB and Redis containers"
    fi
    
    # Mock external services
    export AZURE_TENANT_ID=mock-tenant.local
    export OPENAI_API_KEY=sk-mock-key
    export AI_ENABLED=false
    export EMAIL_ENABLED=false
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        log_step "Creating Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt >/dev/null 2>&1
    else
        source venv/bin/activate
        log_info "Using existing Python virtual environment"
    fi
    
    # Initialize database
    if [ "${USE_SQLITE:-false}" = "true" ]; then
        log_step "Initializing SQLite database..."
        python init_db.py >/dev/null 2>&1 || log_warning "Database initialization had issues"
    fi
    
    # Start server in background
    log_step "Starting backend server..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 --log-level error >/dev/null 2>&1 &
    echo $! > .server.pid
    
    # Wait for backend to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8001/health >/dev/null 2>&1; then
            log_success "Backend ready at http://localhost:8001"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Backend failed to start"
            exit 1
        fi
        sleep 1
    done
}

# Start frontend natively
start_frontend() {
    log_step "Starting frontend service..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Set test environment variables
    export VITE_API_BASE_URL=http://localhost:8001
    export VITE_API_URL=http://localhost:8001
    export VITE_AUTH0_DOMAIN=mock-auth.local
    export VITE_AUTH0_CLIENT_ID=fast_e2e_test_client
    export VITE_ENVIRONMENT=testing
    export NODE_ENV=development
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_step "Installing frontend dependencies..."
        npm install >/dev/null 2>&1
    fi
    
    # Start dev server in background
    npm run dev -- --host 0.0.0.0 --port 3001 >/dev/null 2>&1 &
    echo $! > .server.pid
    
    # Wait for frontend to be ready
    for i in {1..60}; do
        if curl -s http://localhost:3001 >/dev/null 2>&1; then
            log_success "Frontend ready at http://localhost:3001"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Frontend failed to start"
            exit 1
        fi
        sleep 1
    done
}

# Run E2E tests
run_tests() {
    log_step "Running E2E tests..."
    
    cd "$PROJECT_ROOT/tests/e2e"
    
    # Install test dependencies if needed
    if [ ! -d "node_modules" ]; then
        npm install >/dev/null 2>&1
    fi
    
    # Set test configuration
    export PLAYWRIGHT_BASE_URL=http://localhost:3001
    export API_BASE_URL=http://localhost:8001
    export E2E_HEADLESS=true
    export E2E_TIMEOUT=15000
    
    # Run tests based on arguments
    case "${1:-smoke}" in
        "smoke")
            npm run test:e2e:smoke
            ;;
        "full")
            npm run test:e2e
            ;;
        "debug")
            npm run test:e2e:debug
            ;;
        "ui")
            npm run test:e2e:ui
            ;;
        *)
            npm run test:e2e:smoke
            ;;
    esac
}

# Main execution
main() {
    log_info "🚀 Starting Fast E2E Test Runner..."
    
    check_prerequisites
    start_external_services
    start_backend
    start_frontend
    
    log_success "🎉 All services ready! Running tests..."
    run_tests "${1:-smoke}"
    
    log_success "✨ Fast E2E tests completed!"
}

# Show usage if requested
if [ "${1}" = "--help" ] || [ "${1}" = "-h" ]; then
    echo "Fast E2E Test Runner"
    echo ""
    echo "Usage: $0 [test-type]"
    echo ""
    echo "Test types:"
    echo "  smoke   - Quick smoke tests (default)"
    echo "  full    - Complete test suite"
    echo "  debug   - Debug mode with browser UI"
    echo "  ui      - Interactive test runner"
    echo ""
    echo "Examples:"
    echo "  $0              # Run smoke tests"
    echo "  $0 full         # Run all tests"
    echo "  $0 debug        # Debug failing tests"
    exit 0
fi

# Execute main function
main "$@"
