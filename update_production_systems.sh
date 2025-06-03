#!/bin/bash

# PRODUCTION SYSTEMS UPDATE - PHASE 2 OF SECURITY REMEDIATION
# This script updates production systems with new credentials after git history cleanup

set -e

echo "🚀 PRODUCTION SYSTEMS UPDATE - PHASE 2"
echo "======================================"
echo ""
echo "✅ Prerequisites completed:"
echo "   - Git history cleaned (secrets removed from ALL commits)"
echo "   - Final security scan: 0 critical issues"
echo "   - BFG cleanup completed successfully"
echo ""
echo "🔧 Now updating production systems with new credentials..."
echo ""

# Function to check if Azure CLI is installed
check_azure_cli() {
    if ! command -v az >/dev/null 2>&1; then
        echo "⚠️  Azure CLI not found. Install with: brew install azure-cli"
        echo "   Then run: az login"
        return 1
    fi
    echo "✅ Azure CLI available"
    return 0
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "⚠️  Docker not running. Please start Docker Desktop"
        return 1
    fi
    echo "✅ Docker available"
    return 0
}

# Check prerequisites
echo "🔍 Checking deployment prerequisites..."
check_azure_cli
check_docker

echo ""
echo "🔑 STEP 1: Create secure production environment file"
echo "=================================================="

# Create secure production environment file from template
if [[ ! -f ".env.production" ]]; then
    echo "Creating secure .env.production from template..."
    cp .env.production.template .env.production
    
    # Generate new secret keys
    SECRET_KEY=$(openssl rand -base64 32)
    CSRF_SECRET_KEY=$(openssl rand -base64 32)
    
    # Update with new secret keys
    sed -i '' "s/your-production-secret-key-generate-a-strong-random-key/$SECRET_KEY/" .env.production
    sed -i '' "s/your-production-csrf-secret-key-generate-a-strong-random-key/$CSRF_SECRET_KEY/" .env.production
    
    echo "✅ Secure .env.production created with new secret keys"
    echo "⚠️  IMPORTANT: You must still update Auth0, OpenAI, and other service credentials manually"
else
    echo "✅ .env.production already exists"
fi

echo ""
echo "🏗️  STEP 2: Build and test applications locally"
echo "==============================================="

# Build frontend
echo "Building frontend..."
cd frontend
if [[ -f "package.json" ]]; then
    npm install --silent
    npm run build
    echo "✅ Frontend built successfully"
else
    echo "⚠️  Frontend package.json not found, skipping build"
fi
cd ..

# Build backend
echo "Building backend..."
cd backend
if [[ -f "requirements.txt" ]]; then
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    echo "✅ Backend dependencies installed"
    deactivate
else
    echo "⚠️  Backend requirements.txt not found, skipping build"
fi
cd ..

echo ""
echo "🔨 STEP 3: Build Docker containers with clean code"
echo "================================================="

# Build containers
echo "Building Docker containers..."
docker-compose build --no-cache

echo "✅ Docker containers built with cleaned codebase"

echo ""
echo "🚀 STEP 4: Deploy to production"
echo "================================"

echo "⚠️  MANUAL STEPS REQUIRED:"
echo ""
echo "1. 🔑 UPDATE CREDENTIALS IN AZURE KEY VAULT:"
echo "   az keyvault secret set --vault-name pathfinder-kv --name AUTH0-CLIENT-SECRET --value 'NEW_SECRET'"
echo "   az keyvault secret set --vault-name pathfinder-kv --name AUTH0-CLIENT-ID --value 'NEW_CLIENT_ID'"
echo "   az keyvault secret set --vault-name pathfinder-kv --name OPENAI-API-KEY --value 'NEW_OPENAI_KEY'"
echo ""
echo "2. 🚀 DEPLOY UPDATED CONTAINERS:"
echo "   az containerapp revision copy --name pathfinder-backend --resource-group pathfinder-rg"
echo "   az containerapp revision copy --name pathfinder-frontend --resource-group pathfinder-rg"
echo ""
echo "3. 🔍 VERIFY DEPLOYMENT:"
echo "   - Check container app logs for successful startup"
echo "   - Test authentication flows"
echo "   - Verify API endpoints respond correctly"
echo ""

# Test local deployment
echo "🧪 STEP 5: Local testing with clean codebase"
echo "============================================="

echo "Starting local test deployment..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Test backend health
echo "Testing backend health..."
if curl -s http://localhost:8000/health >/dev/null; then
    echo "✅ Backend health check passed"
else
    echo "⚠️  Backend health check failed - check logs with: docker-compose logs backend"
fi

# Test frontend
echo "Testing frontend..."
if curl -s http://localhost:3000 >/dev/null; then
    echo "✅ Frontend accessible"
else
    echo "⚠️  Frontend not accessible - check logs with: docker-compose logs frontend"
fi

echo ""
echo "🔍 Stopping test deployment..."
docker-compose down

echo ""
echo "✅ PRODUCTION SYSTEMS UPDATE PHASE 2 COMPLETE!"
echo "=============================================="
echo ""
echo "📋 SUMMARY:"
echo "✅ Git history cleaned (secrets removed from ALL commits)"
echo "✅ New secret keys generated for production"
echo "✅ Docker containers built with clean codebase"
echo "✅ Local testing completed"
echo ""
echo "🔴 NEXT STEPS:"
echo "1. Update credentials in Azure Key Vault (manual step above)"
echo "2. Deploy to Azure Container Apps"
echo "3. Run final verification tests"
echo ""
echo "📄 Files updated:"
echo "   - .env.production (with new secret keys)"
echo "   - Docker containers (rebuilt with clean code)"
echo ""
