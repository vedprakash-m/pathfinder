#!/bin/bash
# Auth0 Configuration Verification and Testing Script
# Tests Auth0 configuration and provides deployment verification

set -e

echo "🔐 AUTH0 CONFIGURATION VERIFICATION"
echo "==================================="
echo ""

# Configuration
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
EXPECTED_AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com"
EXPECTED_CLIENT_ID="KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}1. Source Code Verification${NC}"
echo "=========================="

# Check Auth0 configuration file
if [[ -f "frontend/src/auth0-config.ts" ]]; then
    echo "✅ Auth0 configuration file found"
    
    # Extract values from config
    DOMAIN=$(grep -o "domain: '[^']*'" frontend/src/auth0-config.ts | cut -d"'" -f2)
    CLIENT_ID=$(grep -o "clientId: '[^']*'" frontend/src/auth0-config.ts | cut -d"'" -f2)
    AUDIENCE=$(grep -o "audience: '[^']*'" frontend/src/auth0-config.ts | cut -d"'" -f2)
    
    echo "📋 Configuration Details:"
    echo "  Domain: $DOMAIN"
    echo "  Client ID: ${CLIENT_ID:0:8}..."
    echo "  Audience: $AUDIENCE"
    
    # Verify values
    if [[ "$DOMAIN" == "$EXPECTED_AUTH0_DOMAIN" ]]; then
        echo "  ✅ Auth0 domain is correct"
    else
        echo "  ❌ Auth0 domain mismatch!"
        echo "     Expected: $EXPECTED_AUTH0_DOMAIN"
        echo "     Found: $DOMAIN"
    fi
    
    if [[ "$CLIENT_ID" == "$EXPECTED_CLIENT_ID" ]]; then
        echo "  ✅ Client ID is correct"
    else
        echo "  ❌ Client ID mismatch!"
        echo "     Expected: ${EXPECTED_CLIENT_ID:0:8}..."
        echo "     Found: ${CLIENT_ID:0:8}..."
    fi
    
else
    echo "❌ Auth0 configuration file not found at frontend/src/auth0-config.ts"
fi

echo ""
echo -e "${BLUE}2. Application Connectivity Tests${NC}"
echo "==============================="

# Test frontend
echo "🌐 Testing frontend connectivity..."
FRONTEND_STATUS=$(curl -s -w "%{http_code}" -o /tmp/frontend_response.html --max-time 10 "$FRONTEND_URL" 2>/dev/null || echo "000")

if [[ "$FRONTEND_STATUS" == "200" ]]; then
    echo "✅ Frontend is accessible (HTTP $FRONTEND_STATUS)"
    
    # Check for Auth0 in response
    if grep -q "$EXPECTED_AUTH0_DOMAIN" /tmp/frontend_response.html 2>/dev/null; then
        echo "  ✅ Auth0 domain found in frontend response"
    else
        echo "  ⚠️  Auth0 domain not visible in HTML (likely in bundled JS)"
    fi
    
    # Check for React/Vite indicators
    if grep -q "vite\|react" /tmp/frontend_response.html 2>/dev/null; then
        echo "  📦 Frontend framework detected"
    fi
    
else
    echo "❌ Frontend not accessible (HTTP $FRONTEND_STATUS)"
fi

# Test backend
echo ""
echo "🔧 Testing backend connectivity..."
BACKEND_STATUS=$(curl -s -w "%{http_code}" -o /dev/null --max-time 10 "$BACKEND_URL/health" 2>/dev/null || echo "000")

if [[ "$BACKEND_STATUS" == "200" ]]; then
    echo "✅ Backend health endpoint accessible (HTTP $BACKEND_STATUS)"
else
    echo "⚠️  Backend health endpoint status: HTTP $BACKEND_STATUS"
fi

# Test API endpoints
echo ""
echo "📊 Testing API endpoints..."
TRIPS_STATUS=$(curl -s -w "%{http_code}" -o /dev/null --max-time 10 "$BACKEND_URL/api/v1/trips/" 2>/dev/null || echo "000")
echo "  Trips endpoint: HTTP $TRIPS_STATUS"

if [[ "$TRIPS_STATUS" == "401" ]]; then
    echo "  ✅ API correctly requires authentication"
elif [[ "$TRIPS_STATUS" == "307" ]]; then
    echo "  ⚠️  Still getting redirects - route conflicts detected"
elif [[ "$TRIPS_STATUS" == "200" ]]; then
    echo "  ⚠️  API accessible without auth - check configuration"
else
    echo "  ℹ️  Unexpected response: HTTP $TRIPS_STATUS"
fi

echo ""
echo -e "${BLUE}3. Deployment Status Assessment${NC}"
echo "============================="

# Overall status assessment
AUTH0_OK="false"
FRONTEND_OK="false"
BACKEND_OK="false"

if [[ "$DOMAIN" == "$EXPECTED_AUTH0_DOMAIN" && "$CLIENT_ID" == "$EXPECTED_CLIENT_ID" ]]; then
    AUTH0_OK="true"
fi

if [[ "$FRONTEND_STATUS" == "200" ]]; then
    FRONTEND_OK="true"
fi

if [[ "$BACKEND_STATUS" == "200" || "$TRIPS_STATUS" == "401" ]]; then
    BACKEND_OK="true"
fi

echo "📊 Component Status:"
echo "  Auth0 Config: $([ "$AUTH0_OK" == "true" ] && echo "✅ Ready" || echo "❌ Needs attention")"
echo "  Frontend: $([ "$FRONTEND_OK" == "true" ] && echo "✅ Running" || echo "❌ Issues detected")"
echo "  Backend: $([ "$BACKEND_OK" == "true" ] && echo "✅ Running" || echo "❌ Issues detected")"

echo ""
echo -e "${BLUE}4. LLM Orchestration Readiness${NC}"
echo "============================"

# Check LLM orchestration files
LLM_DIR="/Users/vedprakashmishra/pathfinder/llm_orchestration"
if [[ -d "$LLM_DIR" ]]; then
    echo "✅ LLM orchestration directory exists"
    
    # Check critical files
    if [[ -f "$LLM_DIR/app_production.py" ]]; then
        echo "  ✅ Production app ready"
    else
        echo "  ❌ Production app missing"
    fi
    
    if [[ -f "$LLM_DIR/deploy-ultra-simple.sh" ]]; then
        echo "  ✅ Quick deployment script ready"
    else
        echo "  ❌ Deployment script missing"
    fi
    
    if [[ -f "$LLM_DIR/Dockerfile.production" ]]; then
        echo "  ✅ Production Dockerfile ready"
    else
        echo "  ❌ Dockerfile missing"
    fi
    
else
    echo "❌ LLM orchestration directory not found"
fi

echo ""
echo -e "${BLUE}5. Manual Testing Commands${NC}"
echo "========================"

echo "🧪 Use these commands to test the current deployment:"
echo ""
echo "# Test frontend directly"
echo "curl -I '$FRONTEND_URL'"
echo ""
echo "# Test backend health"
echo "curl '$BACKEND_URL/health'"
echo ""
echo "# Test API authentication (should get 401)"
echo "curl -I '$BACKEND_URL/api/v1/trips/'"
echo ""
echo "# Check frontend Auth0 config in browser"
echo "# Open: $FRONTEND_URL"
echo "# Check browser console for Auth0 configuration logs"

echo ""
echo -e "${BLUE}6. Deployment Recommendations${NC}"
echo "============================"

if [[ "$AUTH0_OK" == "true" && "$FRONTEND_OK" == "true" && "$BACKEND_OK" == "true" ]]; then
    echo -e "${GREEN}🎉 READY FOR LLM ORCHESTRATION DEPLOYMENT${NC}"
    echo ""
    echo "✅ All components are properly configured"
    echo "✅ Auth0 authentication is set up correctly"
    echo "✅ Frontend and backend are running"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Deploy LLM Orchestration Service using:"
    echo "   cd $LLM_DIR && ./deploy-ultra-simple.sh"
    echo ""
    echo "2. Test the complete stack integration"
    echo "3. Configure production API keys"
    
else
    echo -e "${YELLOW}⚠️  ISSUES DETECTED - NEEDS ATTENTION${NC}"
    echo ""
    
    if [[ "$AUTH0_OK" != "true" ]]; then
        echo "❌ Auth0 configuration issues:"
        echo "   - Verify domain and client ID in auth0-config.ts"
        echo "   - Redeploy frontend if changes are needed"
    fi
    
    if [[ "$FRONTEND_OK" != "true" ]]; then
        echo "❌ Frontend connectivity issues:"
        echo "   - Check Azure Container Apps status"
        echo "   - Verify deployment and scaling"
    fi
    
    if [[ "$BACKEND_OK" != "true" ]]; then
        echo "❌ Backend connectivity issues:"
        echo "   - Check backend deployment status"
        echo "   - Verify API endpoints and routes"
    fi
fi

echo ""
echo -e "${BLUE}7. Quick Fix Commands${NC}"
echo "==================="

echo "If issues are detected, try these quick fixes:"
echo ""
echo "# Force frontend restart"
echo "az containerapp update --name pathfinder-frontend --resource-group pathfinder-rg-dev --min-replicas 0"
echo "sleep 10"
echo "az containerapp update --name pathfinder-frontend --resource-group pathfinder-rg-dev --min-replicas 1"
echo ""
echo "# Check deployment status"
echo "az containerapp show --name pathfinder-frontend --resource-group pathfinder-rg-dev --query 'properties.latestRevisionName'"
echo ""
echo "# View logs"
echo "az containerapp logs show --name pathfinder-frontend --resource-group pathfinder-rg-dev --follow"

# Cleanup temp files
rm -f /tmp/frontend_response.html

echo ""
echo -e "${GREEN}🔍 VERIFICATION COMPLETE${NC}"
echo ""
echo "📋 Summary: Auth0 $([ "$AUTH0_OK" == "true" ] && echo "✅" || echo "❌"), Frontend $([ "$FRONTEND_OK" == "true" ] && echo "✅" || echo "❌"), Backend $([ "$BACKEND_OK" == "true" ] && echo "✅" || echo "❌")"
echo "🚀 Ready for LLM service deployment: $([ "$AUTH0_OK" == "true" ] && [ "$FRONTEND_OK" == "true" ] && [ "$BACKEND_OK" == "true" ] && echo "YES" || echo "AFTER FIXES")"
