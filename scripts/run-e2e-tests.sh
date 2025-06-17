#!/bin/bash

# Pathfinder E2E Test Environment Setup and Execution Script
# This script provides a complete workflow for running E2E tests locally

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
E2E_DIR="$PROJECT_ROOT/tests/e2e"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.e2e.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Function to check if required tools are installed
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if ! command -v node &> /dev/null; then
        missing_tools+=("node")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again."
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Function to setup E2E environment
setup_environment() {
    log_step "Setting up E2E test environment..."
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/playwright-report"
    mkdir -p "$PROJECT_ROOT/test-results"
    mkdir -p "$PROJECT_ROOT/test-results/screenshots"
    
    # Install E2E test dependencies
    if [ -f "$E2E_DIR/package.json" ]; then
        log_step "Installing E2E test dependencies..."
        cd "$E2E_DIR"
        npm install
        cd "$PROJECT_ROOT"
    fi
    
    log_success "E2E environment setup complete"
}

# Function to start services
start_services() {
    log_step "Starting E2E test services..."
    
    # Stop any existing containers
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    
    # Start core services (without test runner)
    log_step "Starting backend, frontend, and databases..."
    docker-compose -f "$COMPOSE_FILE" up -d backend-e2e frontend-e2e mongodb-e2e redis-e2e
    
    # Wait for services to be healthy
    log_step "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts..."
        
        if cd "$E2E_DIR" && node scripts/health-check.js; then
            log_success "All services are healthy!"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy within timeout"
            show_service_logs
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    cd "$PROJECT_ROOT"
}

# Function to setup test data
setup_test_data() {
    log_step "Setting up test data..."
    
    cd "$E2E_DIR"
    
    # Initialize MongoDB
    log_step "Initializing MongoDB..."
    node scripts/mongodb-init.js
    
    # Setup test data
    log_step "Creating test data..."
    node scripts/setup-test-data.js
    
    cd "$PROJECT_ROOT"
    
    log_success "Test data setup complete"
}

# Function to run E2E tests
run_tests() {
    local test_type="${1:-all}"
    
    log_step "Running E2E tests (type: $test_type)..."
    
    cd "$E2E_DIR"
    
    case "$test_type" in
        "smoke")
            log_info "Running smoke tests..."
            npm run test:e2e:smoke
            ;;
        "critical")
            log_info "Running critical path tests..."
            npm run test:e2e:critical
            ;;
        "auth")
            log_info "Running authentication tests..."
            npm run test:e2e:auth
            ;;
        "trips")
            log_info "Running trip management tests..."
            npm run test:e2e:trips
            ;;
        "families")
            log_info "Running family management tests..."
            npm run test:e2e:families
            ;;
        "debug")
            log_info "Running tests in debug mode..."
            npm run test:e2e:debug
            ;;
        "headed")
            log_info "Running tests in headed mode..."
            npm run test:e2e:headed
            ;;
        "all"|*)
            log_info "Running all E2E tests..."
            npm run test:e2e
            ;;
    esac
    
    local exit_code=$?
    cd "$PROJECT_ROOT"
    
    return $exit_code
}

# Function to cleanup
cleanup() {
    log_step "Cleaning up test environment..."
    
    # Cleanup test data
    if [ -d "$E2E_DIR" ]; then
        cd "$E2E_DIR"
        node scripts/cleanup-test-data.js || true
        cd "$PROJECT_ROOT"
    fi
    
    # Stop all containers
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans --volumes || true
    
    log_success "Cleanup complete"
}

# Function to show service logs
show_service_logs() {
    log_step "Showing service logs..."
    
    echo -e "${YELLOW}=== Backend Logs ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50 backend-e2e || true
    
    echo -e "${YELLOW}=== Frontend Logs ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50 frontend-e2e || true
    
    echo -e "${YELLOW}=== MongoDB Logs ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 mongodb-e2e || true
    
    echo -e "${YELLOW}=== Redis Logs ===${NC}"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 redis-e2e || true
}

# Function to show test report
show_report() {
    if [ -f "$PROJECT_ROOT/playwright-report/index.html" ]; then
        log_success "Opening test report..."
        if command -v open &> /dev/null; then
            open "$PROJECT_ROOT/playwright-report/index.html"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$PROJECT_ROOT/playwright-report/index.html"
        else
            log_info "Test report available at: file://$PROJECT_ROOT/playwright-report/index.html"
        fi
    else
        log_warning "No test report found"
    fi
}

# Function to display help
show_help() {
    echo "Pathfinder E2E Test Runner"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup     - Setup E2E test environment"
    echo "  start     - Start E2E test services"
    echo "  test      - Run E2E tests"
    echo "  stop      - Stop E2E test services"
    echo "  cleanup   - Cleanup test environment"
    echo "  logs      - Show service logs"
    echo "  report    - Open test report"
    echo "  full      - Complete E2E workflow (setup + start + test + cleanup)"
    echo ""
    echo "Test Types (for 'test' command):"
    echo "  all       - Run all tests (default)"
    echo "  smoke     - Run smoke tests only"
    echo "  critical  - Run critical path tests"
    echo "  auth      - Run authentication tests"
    echo "  trips     - Run trip management tests"
    echo "  families  - Run family management tests"
    echo "  debug     - Run tests in debug mode"
    echo "  headed    - Run tests in headed mode"
    echo ""
    echo "Examples:"
    echo "  $0 full                    # Complete E2E workflow"
    echo "  $0 test smoke             # Run smoke tests only"
    echo "  $0 test debug             # Run tests in debug mode"
    echo "  $0 start && $0 test auth  # Start services and run auth tests"
}

# Main execution logic
main() {
    local command="${1:-help}"
    local test_type="${2:-all}"
    
    case "$command" in
        "setup")
            check_prerequisites
            setup_environment
            ;;
        "start")
            start_services
            setup_test_data
            ;;
        "test")
            if ! run_tests "$test_type"; then
                log_error "E2E tests failed"
                show_service_logs
                exit 1
            fi
            log_success "E2E tests completed successfully"
            ;;
        "stop")
            docker-compose -f "$COMPOSE_FILE" down
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            show_service_logs
            ;;
        "report")
            show_report
            ;;
        "full")
            # Complete E2E workflow
            log_info "Starting complete E2E test workflow..."
            
            check_prerequisites
            setup_environment
            start_services
            setup_test_data
            
            # Run tests and capture exit code
            local test_exit_code=0
            if ! run_tests "$test_type"; then
                test_exit_code=1
                log_error "E2E tests failed"
                show_service_logs
            else
                log_success "E2E tests completed successfully"
            fi
            
            # Show report regardless of test result
            show_report
            
            # Cleanup
            cleanup
            
            exit $test_exit_code
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Trap to ensure cleanup on script exit
trap cleanup EXIT

# Execute main function with all arguments
main "$@"
