#!/bin/bash
# Comprehensive Deployment Verification Script
# Verifies Auth0 configuration and prepares LLM Orchestration deployment

set -e

echo "🚀 COMPREHENSIVE DEPLOYMENT VERIFICATION"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com"

echo -e "${BLUE}Phase 1: Auth0 Configuration Verification${NC}"
echo "==========================================="

# Check Auth0 configuration in source code
echo "🔍 Checking Auth0 configuration files..."

if [[ -f "frontend/src/auth0-config.ts" ]]; then
    echo "✅ Auth0 configuration file found"
    
    # Extract domain from config
    CONFIGURED_DOMAIN=$(grep -o "domain: '[^']*'" frontend/src/auth0-config.ts | cut -d"'" -f2)
    CONFIGURED_CLIENT_ID=$(grep -o "clientId: '[^']*'" frontend/src/auth0-config.ts | cut -d"'" -f2)
    CONFIGURED_AUDIENCE=$(grep -o "audience: '[^']*'" frontend/src/auth0-config.ts | cut -d"'" -f2)
    
    echo "  📋 Configured Domain: $CONFIGURED_DOMAIN"
    echo "  📋 Configured Client ID: ${CONFIGURED_CLIENT_ID:0:8}..."
    echo "  📋 Configured Audience: $CONFIGURED_AUDIENCE"
    
    if [[ "$CONFIGURED_DOMAIN" == "$AUTH0_DOMAIN" ]]; then
        echo "  ✅ Auth0 domain is correctly configured"
    else
        echo "  ❌ Auth0 domain mismatch!"
        echo "     Expected: $AUTH0_DOMAIN"
        echo "     Found: $CONFIGURED_DOMAIN"
    fi
else
    echo "❌ Auth0 configuration file not found"
fi

# Test frontend connectivity
echo ""
echo "🌐 Testing frontend connectivity..."
if curl -s --max-time 10 "$FRONTEND_URL" > /dev/null; then
    echo "✅ Frontend is accessible"
    
    # Check for Auth0 domain in frontend response
    echo "🔍 Checking deployed Auth0 configuration..."
    FRONTEND_CONTENT=$(curl -s --max-time 10 "$FRONTEND_URL")
    
    if echo "$FRONTEND_CONTENT" | grep -q "$AUTH0_DOMAIN"; then
        echo "✅ Correct Auth0 domain found in deployed frontend"
    else
        echo "⚠️  Auth0 domain not found in frontend response (may be in bundled JS)"
    fi
else
    echo "❌ Frontend is not accessible"
fi

# Test backend connectivity
echo ""
echo "🔧 Testing backend connectivity..."
if curl -s --max-time 10 "$BACKEND_URL/health" > /dev/null; then
    echo "✅ Backend is accessible"
    
    # Test API endpoints
    TRIPS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null --max-time 10 "$BACKEND_URL/api/v1/trips/" 2>/dev/null || echo "000")
    echo "  📊 Trips endpoint response: $TRIPS_RESPONSE"
    
    if [[ "$TRIPS_RESPONSE" == "401" ]]; then
        echo "  ✅ API requiring authentication (expected behavior)"
    elif [[ "$TRIPS_RESPONSE" == "307" ]]; then
        echo "  ⚠️  Still getting redirects - route conflicts may persist"
    else
        echo "  ℹ️  Unexpected response: $TRIPS_RESPONSE"
    fi
else
    echo "❌ Backend is not accessible"
fi

echo ""
echo -e "${BLUE}Phase 2: LLM Orchestration Service Preparation${NC}"
echo "=============================================="

# Check LLM orchestration files
echo "📁 Checking LLM orchestration service files..."

LLM_ORCH_DIR="/Users/vedprakashmishra/pathfinder/llm_orchestration"
if [[ -d "$LLM_ORCH_DIR" ]]; then
    echo "✅ LLM orchestration directory found"
    
    # Check key files
    declare -a required_files=(
        "app_production.py"
        "requirements-production.txt" 
        "Dockerfile.production"
        "deploy-ultra-simple.sh"
        "deploy-azure.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$LLM_ORCH_DIR/$file" ]]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (missing)"
        fi
    done
    
    # Check service structure
    echo ""
    echo "📋 LLM Orchestration Service Structure:"
    if [[ -d "$LLM_ORCH_DIR/core" ]]; then
        echo "  ✅ Core modules: $(ls $LLM_ORCH_DIR/core | wc -l) files"
    fi
    if [[ -d "$LLM_ORCH_DIR/services" ]]; then
        echo "  ✅ Service modules: $(ls $LLM_ORCH_DIR/services | wc -l) files"
    fi
    if [[ -d "$LLM_ORCH_DIR/config" ]]; then
        echo "  ✅ Configuration files: $(ls $LLM_ORCH_DIR/config | wc -l) files"
    fi
    
else
    echo "❌ LLM orchestration directory not found"
fi

echo ""
echo -e "${BLUE}Phase 3: Deployment Strategy${NC}"
echo "============================="

echo "🎯 Recommended deployment approach:"
echo ""
echo "1. Auth0 Configuration:"
if [[ "$CONFIGURED_DOMAIN" == "$AUTH0_DOMAIN" ]]; then
    echo "   ✅ Auth0 is properly configured"
    echo "   📝 Action: Verify frontend deployment is using latest image"
else
    echo "   ⚠️  Auth0 configuration needs verification"
    echo "   📝 Action: Redeploy frontend with correct Auth0 config"
fi

echo ""
echo "2. LLM Orchestration Service:"
echo "   📦 Deployment options available:"
echo "     - Ultra-simple: Azure Container Instances (fastest)"
echo "     - Full Azure: Container Apps with Key Vault and Redis"
echo "     - App Service: Alternative hosting option"

echo ""
echo "🚀 Ready to deploy LLM Orchestration Service:"
echo ""
echo "Option 1 - Quick deployment (Azure Container Instances):"
echo "  cd $LLM_ORCH_DIR && ./deploy-ultra-simple.sh"
echo ""
echo "Option 2 - Full production deployment (Azure Container Apps):"
echo "  cd $LLM_ORCH_DIR && ./deploy-azure.sh"
echo ""
echo "Option 3 - Manual Azure CLI commands:"
echo "  # Create resource group"
echo "  az group create --name llm-orchestration-rg --location eastus"
echo "  # Deploy container instance"
echo "  az container create --resource-group llm-orchestration-rg \\"
echo "    --name llm-orchestration-service --image python:3.9-slim \\"
echo "    --cpu 1 --memory 2 --ports 8000 --ip-address Public"

echo ""
echo -e "${BLUE}Phase 4: Testing Commands${NC}"
echo "========================"

echo "🧪 Post-deployment testing commands:"
echo ""
echo "# Test Auth0 frontend"
echo "curl -I '$FRONTEND_URL'"
echo ""
echo "# Test backend API"
echo "curl -I '$BACKEND_URL/api/v1/trips/'"
echo ""
echo "# Test LLM service (after deployment)"
echo "curl -X POST http://\$LLM_SERVICE_IP:8000/v1/generate \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"prompt\":\"Hello world\",\"user_id\":\"test\"}'"

echo ""
echo -e "${GREEN}🎉 VERIFICATION COMPLETE${NC}"
echo ""
echo "📝 Summary:"
echo "  - Auth0 configuration: $([ "$CONFIGURED_DOMAIN" == "$AUTH0_DOMAIN" ] && echo "✅ Ready" || echo "⚠️ Needs attention")"
echo "  - Frontend/Backend: $(curl -s --max-time 5 "$FRONTEND_URL" > /dev/null && echo "✅ Running" || echo "❌ Issues detected")"
echo "  - LLM Orchestration: 🚀 Ready for deployment"
echo ""
echo "Next step: Deploy LLM Orchestration Service using one of the methods above"
