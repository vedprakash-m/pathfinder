#!/bin/bash

# Comprehensive Docker-based testing script for Pathfinder
# This script runs the full application stack in Docker and performs comprehensive testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐙 Pathfinder Comprehensive Docker Testing${NC}"
echo "========================================================"

# Ensure we're in the project root
if [ ! -f "docker-compose.test.yml" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not available${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    exit 1
fi

# Check Docker Compose availability
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not available${NC}"
    echo "   💡 Install Docker Compose or use Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker environment ready${NC}"

# Clean up any existing containers
echo "🧹 Cleaning up existing test containers..."
docker-compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || true
docker compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || true

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up test environment...${NC}"
    docker-compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || true
    docker compose -f docker-compose.test.yml down -v >/dev/null 2>&1 || true
}

trap cleanup EXIT

# Build and run comprehensive tests
echo "🏗️  Building and starting test environment..."
echo "   This may take a few minutes on first run..."

# Run tests with detailed output
echo -e "\n${BLUE}🧪 Running Comprehensive Test Suite${NC}"
echo "========================================"

if docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit; then
    echo -e "\n${GREEN}✅ COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY${NC}"
    echo ""
    echo "🎉 Your application passed all tests in a production-like environment!"
    echo ""
    echo "📋 Tests completed:"
    echo "   ✅ Unit tests"
    echo "   ✅ Integration tests"
    echo "   ✅ E2E tests"
    echo "   ✅ API endpoint tests"
    echo "   ✅ Database connectivity"
    echo "   ✅ Authentication flows"
    echo "   ✅ CORS configuration"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Review test output above"
    echo "   2. Commit your changes: git add . && git commit -m 'Your message'"
    echo "   3. Push to trigger CI/CD: git push origin main"
    echo ""
    echo "The CI/CD pipeline will run similar tests and deploy if successful."
    exit 0
elif docker compose -f docker-compose.test.yml up --build --abort-on-container-exit; then
    echo -e "\n${GREEN}✅ COMPREHENSIVE TESTING COMPLETED SUCCESSFULLY${NC}"
    exit 0
else
    echo -e "\n${RED}❌ TESTING FAILED${NC}"
    echo ""
    echo "💡 Common issues:"
    echo "   - Check Docker logs above for specific failures"
    echo "   - Ensure all required environment variables are set"
    echo "   - Verify database migrations are working"
    echo "   - Check for import errors or missing dependencies"
    echo ""
    echo "🔧 Debug commands:"
    echo "   docker-compose -f docker-compose.test.yml logs test-runner"
    echo "   docker-compose -f docker-compose.test.yml logs test-api"
    echo "   docker-compose -f docker-compose.test.yml logs test-db"
    echo ""
    exit 1
fi
