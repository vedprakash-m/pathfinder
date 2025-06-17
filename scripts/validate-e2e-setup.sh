#!/bin/bash

# Comprehensive E2E Setup and CI/CD Validation Script
# This script validates E2E setup AND catches issues that would fail in CI/CD

set -e

echo "🔍 Comprehensive E2E and CI/CD Validation..."

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

# Check Docker availability (allow bypass for CI/CD validation)
DOCKER_REQUIRED=${DOCKER_REQUIRED:-true}
if [ "$DOCKER_REQUIRED" = "true" ]; then
    if ! command -v docker &> /dev/null; then
        print_status "Docker is not installed or not in PATH" "error"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_status "Docker daemon is not running" "error"
        exit 1
    fi

    print_status "Docker is available and running" "success"
else
    if ! command -v docker &> /dev/null; then
        print_status "Docker not available (bypassed for CI/CD validation)" "warning"
    else
        print_status "Docker is available" "success"
    fi
fi

# Check Docker Compose availability (allow bypass)
if [ "$DOCKER_REQUIRED" = "true" ]; then
    if ! command -v docker-compose &> /dev/null; then
        print_status "docker-compose is not installed or not in PATH" "error"
        exit 1
    fi
    print_status "Docker Compose is available" "success"
else
    if ! command -v docker-compose &> /dev/null; then
        print_status "Docker Compose not available (bypassed for CI/CD validation)" "warning"
    else
        print_status "Docker Compose is available" "success"
    fi
fi

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

# Validate docker-compose.e2e.yml syntax (respect DOCKER_REQUIRED flag)
if [ "$DOCKER_REQUIRED" = "true" ] && command -v docker-compose &> /dev/null && docker info >/dev/null 2>&1; then
    if docker-compose -f docker-compose.e2e.yml config &> /dev/null; then
        print_status "docker-compose.e2e.yml syntax is valid" "success"
    else
        print_status "docker-compose.e2e.yml has syntax errors" "error"
        exit 1
    fi
elif command -v python3 &> /dev/null; then
    # Fallback: basic YAML syntax check
    if python3 -c "import yaml; yaml.safe_load(open('docker-compose.e2e.yml'))" >/dev/null 2>&1; then
        print_status "docker-compose.e2e.yml YAML syntax is valid (basic check)" "success"
    else
        print_status "docker-compose.e2e.yml has YAML syntax errors" "error"
        exit 1
    fi
else
    print_status "Cannot validate docker-compose.e2e.yml syntax (limited validation mode)" "warning"
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

# ========================================
# CI/CD VALIDATION (NEW COMPREHENSIVE CHECKS)
# ========================================

echo ""
echo "🔍 CI/CD Integration Validation..."

# 1. Backend Dependency Validation
echo ""
echo "🐍 Backend Dependencies Validation:"

# Check Python version compatibility
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION" "success"
    
    # Check if it's Python 3.12+ which causes dependency-injector issues
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
        print_status "Python 3.12+ detected - potential dependency-injector compilation issues" "warning"
        echo "   ⚠️  CI/CD may fail with dependency-injector package compilation"
    fi
else
    print_status "Python3 not available" "warning"
fi

# Validate backend requirements.txt
if [ -f "backend/requirements.txt" ]; then
    print_status "Found backend/requirements.txt" "success"
    
    # Check for problematic dependencies
    if grep -q "dependency-injector" backend/requirements.txt; then
        print_status "dependency-injector found in requirements.txt - may fail on Python 3.12+" "warning"
    fi
    
    # Test pip install simulation (dry run)
    echo "   Testing pip install simulation..."
    if python3 -m pip install --dry-run -r backend/requirements.txt >/dev/null 2>&1; then
        print_status "Backend dependencies appear installable" "success"
    else
        print_status "Backend dependencies may have installation issues" "warning"
        echo "   ⚠️  Some packages may fail during CI/CD pip install"
    fi
else
    print_status "Missing backend/requirements.txt" "error"
fi

# 2. Poetry/pyproject.toml validation
echo ""
echo "📦 Poetry Configuration Validation:"

if [ -f "pyproject.toml" ]; then
    print_status "Found pyproject.toml" "success"
    
    # Check for required Poetry fields
    if grep -q "tool.poetry.name\|^name\s*=" pyproject.toml; then
        print_status "Project name configured" "success"
    else
        print_status "Missing project name in pyproject.toml - will fail Snyk scan" "error"
        echo "   ❌ Add [tool.poetry.name] or [project] name = \"...\" to pyproject.toml"
    fi
    
    if grep -q "tool.poetry.version\|^version\s*=" pyproject.toml; then
        print_status "Project version configured" "success"
    else
        print_status "Missing project version in pyproject.toml - will fail Snyk scan" "error"
        echo "   ❌ Add [tool.poetry.version] or [project] version = \"...\" to pyproject.toml"
    fi
else
    print_status "Missing pyproject.toml" "warning"
fi

# 3. Infrastructure Prerequisites Check
echo ""
echo "�️  Infrastructure Prerequisites:"

# Check for Azure CLI (if available)
if command -v az &> /dev/null; then
    print_status "Azure CLI available" "success"
    
    # Check login status (non-blocking)
    if az account show >/dev/null 2>&1; then
        print_status "Azure CLI logged in" "success"
        
        # Check data layer prerequisites
        echo "   Checking Azure data layer resources..."
        DATA_RG="pathfinder-db-rg"
        
        if az group exists --name "$DATA_RG" >/dev/null 2>&1; then
            print_status "Data resource group '$DATA_RG' exists" "success"
            
            # Check for SQL server
            SQL_SERVER_COUNT=$(az sql server list --resource-group "$DATA_RG" --query "length([])" -o tsv 2>/dev/null || echo "0")
            if [ "$SQL_SERVER_COUNT" -gt 0 ]; then
                print_status "SQL server found in data layer" "success"
            else
                print_status "SQL server missing in data layer - deployment will fail" "error"
                echo "   ❌ Run './scripts/deploy-data-layer.sh' first"
            fi
            
            # Check for Cosmos DB
            COSMOS_COUNT=$(az cosmosdb list --resource-group "$DATA_RG" --query "length([])" -o tsv 2>/dev/null || echo "0")
            if [ "$COSMOS_COUNT" -gt 0 ]; then
                print_status "Cosmos DB found in data layer" "success"
            else
                print_status "Cosmos DB missing in data layer - deployment will fail" "error"
                echo "   ❌ Run './scripts/deploy-data-layer.sh' first"
            fi
            
            # Check for Storage account
            STORAGE_COUNT=$(az storage account list --resource-group "$DATA_RG" --query "length([])" -o tsv 2>/dev/null || echo "0")
            if [ "$STORAGE_COUNT" -gt 0 ]; then
                print_status "Storage account found in data layer" "success"
            else
                print_status "Storage account missing in data layer - deployment will fail" "error"
                echo "   ❌ Run './scripts/deploy-data-layer.sh' first"
            fi
        else
            print_status "Data resource group '$DATA_RG' does not exist - deployment will fail" "error"
            echo "   ❌ Run './scripts/deploy-data-layer.sh' first"
        fi
    else
        print_status "Azure CLI not logged in" "warning"
        echo "   ⚠️  Infrastructure deployment will fail without Azure login"
    fi
else
    print_status "Azure CLI not available" "warning"
    echo "   ⚠️  Required for infrastructure deployment"
fi

# Check for required environment variables (common CI/CD secrets)
ENV_VARS=("AZURE_CREDENTIALS" "SQL_ADMIN_USERNAME" "SQL_ADMIN_PASSWORD")
for var in "${ENV_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        print_status "$var is set" "success"
    else
        print_status "$var not set" "warning"
        echo "   ⚠️  Required for CI/CD deployment"
    fi
done

# 4. Security Scan Prerequisites
echo ""
echo "🔐 Security Scan Prerequisites:"

# Check for Snyk token
if [ -n "$SNYK_TOKEN" ]; then
    print_status "SNYK_TOKEN is set" "success"
else
    print_status "SNYK_TOKEN not set" "warning"
    echo "   ⚠️  Required for dependency vulnerability scanning"
fi

# Check if packages are installed for Snyk scan
if [ -f "backend/requirements.txt" ]; then
    echo "   Checking if backend packages are installed..."
    MISSING_PACKAGES=()
    while IFS= read -r line; do
        if [[ $line =~ ^[a-zA-Z] ]]; then
            PACKAGE=$(echo "$line" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
            if ! python3 -c "import $PACKAGE" 2>/dev/null; then
                MISSING_PACKAGES+=("$PACKAGE")
            fi
        fi
    done < backend/requirements.txt
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        print_status "Some backend packages not installed: ${MISSING_PACKAGES[*]:0:5}..." "warning"
        echo "   ⚠️  Snyk scan may fail - run 'pip install -r backend/requirements.txt'"
    else
        print_status "Backend packages appear to be installed" "success"
    fi
fi

# 5. Container Security Prerequisites
echo ""
echo "🐳 Container Security Prerequisites:"

# Check for Trivy (if available)
if command -v trivy &> /dev/null; then
    print_status "Trivy security scanner available" "success"
else
    print_status "Trivy not available" "warning"
    echo "   ⚠️  Container security scanning won't work locally"
fi

# Check GitHub token for CodeQL
if [ -n "$GITHUB_TOKEN" ]; then
    print_status "GITHUB_TOKEN is set" "success"
else
    print_status "GITHUB_TOKEN not set" "warning"
    echo "   ⚠️  Required for CodeQL security scan uploads"
fi

# 6. CI/CD Configuration Validation
echo ""
echo "⚙️  CI/CD Configuration:"

# Check GitHub Actions workflows
if [ -d ".github/workflows" ]; then
    print_status "GitHub Actions workflows directory exists" "success"
    
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
    print_status "Found $WORKFLOW_COUNT workflow files" "success"
    
    # Check for common required workflows
    if [ -f ".github/workflows/ci-cd-pipeline.yml" ]; then
        print_status "Main CI/CD pipeline workflow exists" "success"
    else
        print_status "Main CI/CD pipeline workflow missing" "warning"
    fi
else
    print_status "No GitHub Actions workflows found" "warning"
fi

# (Docker Compose validation already done earlier in the script)

# Final comprehensive summary
echo ""
echo "🎉 Comprehensive Validation Complete!"
echo ""
echo "📊 Summary:"
echo "   ✅ E2E Setup: Ready"
echo "   ⚠️  CI/CD Issues: Check warnings above"
echo ""
echo "🚨 CRITICAL FIXES NEEDED FOR CI/CD:"
echo "   1. Fix pyproject.toml Poetry configuration (project name/version)"
echo "   2. Consider Python 3.12 compatibility issues with dependency-injector"
echo "   3. Ensure Azure credentials are properly configured"
echo "   4. Install backend dependencies before running security scans"
echo ""
echo "Next Steps:"
echo "1. Fix critical CI/CD issues (see warnings above)"
echo "2. Run the full E2E test suite:"
echo "   ./scripts/run-e2e-tests.sh"
echo ""
echo "3. For CI/CD validation only (skip Docker):"
echo "   DOCKER_REQUIRED=false ./scripts/validate-e2e-setup.sh"
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
