#!/bin/bash

# Auth0 Status Check Script
echo "🔍 Auth0 Configuration Status Check"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📋 Checking current configuration..."
echo ""

# Check .env.production
if [[ -f "frontend/.env.production" ]]; then
    CLIENT_ID=$(grep "VITE_AUTH0_CLIENT_ID" frontend/.env.production | cut -d'=' -f2)
    DOMAIN=$(grep "VITE_AUTH0_DOMAIN" frontend/.env.production | cut -d'=' -f2)
    
    echo "Current frontend/.env.production:"
    echo "  Domain: $DOMAIN"
    echo "  Client ID: $CLIENT_ID"
    echo ""
    
    if [[ "$CLIENT_ID" == "PLACEHOLDER"* ]]; then
        echo -e "${RED}❌ PROBLEM: Client ID is still a placeholder${NC}"
        echo -e "${YELLOW}   Action needed: Replace with actual Auth0 Client ID${NC}"
    else
        echo -e "${GREEN}✅ Client ID looks valid${NC}"
    fi
else
    echo -e "${RED}❌ frontend/.env.production not found${NC}"
fi

echo ""

# Check auth0-config.ts
if [[ -f "frontend/src/auth0-config.ts" ]]; then
    FALLBACK=$(grep "PLACEHOLDER_CLIENT_ID_NEEDS_ROTATION" frontend/src/auth0-config.ts)
    
    if [[ -n "$FALLBACK" ]]; then
        echo -e "${RED}❌ PROBLEM: auth0-config.ts still has placeholder fallback${NC}"
        echo -e "${YELLOW}   Action needed: Replace fallback value${NC}"
    else
        echo -e "${GREEN}✅ auth0-config.ts fallback looks updated${NC}"
    fi
else
    echo -e "${RED}❌ frontend/src/auth0-config.ts not found${NC}"
fi

echo ""
echo "🎯 Application URLs:"
echo "  Frontend: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "  Backend:  https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo ""

# Check if manual fix script is ready
if [[ -x "manual-auth0-fix.sh" ]]; then
    echo -e "${GREEN}✅ Manual fix script ready${NC}"
    echo "   Usage: ./manual-auth0-fix.sh \"YOUR_CLIENT_ID_FROM_KEYVAULT\""
else
    echo -e "${YELLOW}⚠️  Manual fix script not executable${NC}"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Get Auth0 Client ID from Azure Key Vault (pathfinder-kv-dev → auth0-client-id)"
echo "2. Run: ./manual-auth0-fix.sh \"YOUR_ACTUAL_CLIENT_ID\""
echo "3. Build and deploy updated frontend container"
echo "4. Test authentication at the frontend URL"
