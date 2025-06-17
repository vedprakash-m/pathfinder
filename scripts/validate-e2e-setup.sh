#!/bin/bash

# E2E Setup Validation Script
# This script performs a quick validation of the E2E testing setup

set -e

echo "🔍 Validating E2E Testing Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ "$2" = "success" ]; then
        echo -e "${GREEN}✅ $1${NC}"
    elif [ "$2" = "warning" ]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

# Check if we're in the project root
if [ ! -f "docker-compose.e2e.yml" ]; then
    print_status "Not in project root directory. Please run from the pathfinder project root." "error"
    exit 1
fi

print_status "Found docker-compose.e2e.yml" "success"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    print_status "Docker is not installed or not in PATH" "error"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_status "Docker daemon is not running" "error"
    exit 1
fi

print_status "Docker is available and running" "success"

# Check Docker Compose availability
if ! command -v docker-compose &> /dev/null; then
    print_status "docker-compose is not installed or not in PATH" "error"
    exit 1
fi

print_status "Docker Compose is available" "success"

# Check Node.js availability
if ! command -v node &> /dev/null; then
    print_status "Node.js is not installed or not in PATH" "warning"
    echo "   Node.js is needed for local debugging of E2E tests"
else
    NODE_VERSION=$(node --version)
    print_status "Node.js is available ($NODE_VERSION)" "success"
fi

# Check if required ports are available
PORTS=(3000 8000 27017 6379 8081 9080)
UNAVAILABLE_PORTS=()

for port in "${PORTS[@]}"; do
    if lsof -i:$port &> /dev/null; then
        UNAVAILABLE_PORTS+=($port)
    fi
done

if [ ${#UNAVAILABLE_PORTS[@]} -gt 0 ]; then
    print_status "Some required ports are in use: ${UNAVAILABLE_PORTS[*]}" "warning"
    echo "   You may need to stop services using these ports before running E2E tests"
    echo "   Use 'lsof -i:PORT' to identify what's using each port"
else
    print_status "All required ports (${PORTS[*]}) are available" "success"
fi

# Check E2E directory structure
E2E_FILES=(
    "tests/e2e/Dockerfile"
    "tests/e2e/package.json"
    "tests/e2e/playwright.config.ts"
    "tests/e2e/global-setup.ts"
    "tests/e2e/global-teardown.ts"
    "scripts/run-e2e-tests.sh"
)

MISSING_FILES=()
for file in "${E2E_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=($file)
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    print_status "Missing E2E files: ${MISSING_FILES[*]}" "error"
    exit 1
else
    print_status "All required E2E files are present" "success"
fi

# Check script permissions
if [ ! -x "scripts/run-e2e-tests.sh" ]; then
    print_status "E2E script is not executable, fixing..." "warning"
    chmod +x scripts/run-e2e-tests.sh
    print_status "Made scripts/run-e2e-tests.sh executable" "success"
else
    print_status "E2E script has correct permissions" "success"
fi

# Validate docker-compose.e2e.yml syntax
if docker-compose -f docker-compose.e2e.yml config &> /dev/null; then
    print_status "docker-compose.e2e.yml syntax is valid" "success"
else
    print_status "docker-compose.e2e.yml has syntax errors" "error"
    exit 1
fi

# Check E2E test files
TEST_DIRS=(
    "tests/e2e/tests/auth"
    "tests/e2e/tests/trips"
    "tests/e2e/tests/families"
    "tests/e2e/tests/api"
    "tests/e2e/tests/workflows"
)

for dir in "${TEST_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        print_status "Missing test directory: $dir" "error"
        exit 1
    elif [ -z "$(ls -A $dir)" ]; then
        print_status "Empty test directory: $dir" "warning"
    else
        print_status "Test directory exists and has content: $dir" "success"
    fi
done

# Check utility scripts
SCRIPT_FILES=(
    "tests/e2e/scripts/health-check.js"
    "tests/e2e/scripts/setup-test-data.js"
    "tests/e2e/scripts/cleanup-test-data.js"
    "tests/e2e/scripts/mongodb-init.js"
)

for script in "${SCRIPT_FILES[@]}"; do
    if [ ! -f "$script" ]; then
        print_status "Missing utility script: $script" "error"
        exit 1
    else
        print_status "Utility script exists: $script" "success"
    fi
done

# Final summary
echo ""
echo "🎉 E2E Setup Validation Complete!"
echo ""
echo "Next Steps:"
echo "1. Run the full E2E test suite:"
echo "   ./scripts/run-e2e-tests.sh"
echo ""
echo "2. For debugging and manual control:"
echo "   docker-compose -f docker-compose.e2e.yml up -d"
echo "   cd tests/e2e && node scripts/health-check.js"
echo "   cd tests/e2e && npm test"
echo ""
echo "3. Read the comprehensive guide:"
echo "   open E2E_TESTING.md"
echo ""

if [ ${#UNAVAILABLE_PORTS[@]} -gt 0 ]; then
    echo "⚠️  Remember to stop services using ports: ${UNAVAILABLE_PORTS[*]}"
    echo ""
fi

print_status "E2E testing setup is ready!" "success"
