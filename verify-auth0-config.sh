#!/bin/bash

# Auth0 Configuration Verification Script
# Analyzes current frontend Auth0 configuration

echo "🔍 Auth0 Configuration Analysis"
echo "==============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}📋 Checking frontend configuration files...${NC}"
echo ""

# Check .env.production file
if [[ -f "frontend/.env.production" ]]; then
    echo -e "${GREEN}✅ Found frontend/.env.production${NC}"
    echo ""
    echo "🔧 Current Auth0 configuration:"
    echo "--------------------------------"
    
    # Extract Auth0 variables
    DOMAIN=$(grep "VITE_AUTH0_DOMAIN" frontend/.env.production | cut -d'=' -f2)
    CLIENT_ID=$(grep "VITE_AUTH0_CLIENT_ID" frontend/.env.production | cut -d'=' -f2)
    AUDIENCE=$(grep "VITE_AUTH0_AUDIENCE" frontend/.env.production | cut -d'=' -f2)
    
    echo "Domain: $DOMAIN"
    echo "Client ID: $CLIENT_ID"  
    echo "Audience: $AUDIENCE"
    echo ""
    
    # Analyze each configuration
    echo "🔍 Configuration Analysis:"
    echo "-------------------------"
    
    # Check domain
    if [[ "$DOMAIN" == "dev-jwnud3v8ghqnyygr.us.auth0.com" ]]; then
        echo -e "${GREEN}✅ Domain: Correct${NC}"
    else
        echo -e "${RED}❌ Domain: Incorrect (should be dev-jwnud3v8ghqnyygr.us.auth0.com)${NC}"
    fi
    
    # Check client ID
    if [[ "$CLIENT_ID" == "PLACEHOLDER"* ]]; then
        echo -e "${RED}❌ Client ID: PLACEHOLDER DETECTED - This is the problem!${NC}"
        echo -e "${YELLOW}   Expected: 32-character alphanumeric string${NC}"
        echo -e "${YELLOW}   Actual: $CLIENT_ID${NC}"
    elif [[ ${#CLIENT_ID} -eq 32 && "$CLIENT_ID" =~ ^[A-Za-z0-9]+$ ]]; then
        echo -e "${GREEN}✅ Client ID: Valid format (32 characters)${NC}"
    else
        echo -e "${YELLOW}⚠️  Client ID: Unexpected format${NC}"
        echo -e "${YELLOW}   Length: ${#CLIENT_ID} characters (expected 32)${NC}"
    fi
    
    # Check audience
    if [[ "$AUDIENCE" == "https://pathfinder-api.com" ]]; then
        echo -e "${GREEN}✅ Audience: Correct${NC}"
    else
        echo -e "${RED}❌ Audience: Incorrect (should be https://pathfinder-api.com)${NC}"
    fi
else
    echo -e "${RED}❌ frontend/.env.production not found${NC}"
fi

echo ""

# Check auth0-config.ts file
if [[ -f "frontend/src/auth0-config.ts" ]]; then
    echo -e "${GREEN}✅ Found frontend/src/auth0-config.ts${NC}"
    echo ""
    echo "🔧 Checking fallback configuration:"
    echo "-----------------------------------"
    
    # Check for placeholder in fallback
    if grep -q "PLACEHOLDER" frontend/src/auth0-config.ts; then
        echo -e "${RED}❌ PLACEHOLDER found in auth0-config.ts fallback${NC}"
        echo "Fallback line:"
        grep "clientId:" frontend/src/auth0-config.ts || echo "Could not extract clientId line"
        echo ""
        echo -e "${YELLOW}⚠️  This means even if env vars fail, it falls back to placeholder${NC}"
    else
        echo -e "${GREEN}✅ No placeholders found in fallback configuration${NC}"
    fi
else
    echo -e "${RED}❌ frontend/src/auth0-config.ts not found${NC}"
fi

echo ""
echo -e "${BLUE}🌐 Testing application endpoints...${NC}"
echo ""

# Test frontend
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Testing frontend: $FRONTEND_URL"
if curl -s --head "$FRONTEND_URL" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ Frontend accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
fi

# Test backend
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Testing backend: $BACKEND_URL/health"
if curl -s "$BACKEND_URL/health" | grep -q "ok\|healthy\|success"; then
    echo -e "${GREEN}✅ Backend healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Backend health check inconclusive${NC}"
fi

echo ""
echo -e "${BLUE}🚨 DIAGNOSIS SUMMARY:${NC}"
echo "======================"

# Determine the problem
HAS_PLACEHOLDER_ENV=$(grep "PLACEHOLDER" frontend/.env.production 2>/dev/null || echo "")
HAS_PLACEHOLDER_CONFIG=$(grep "PLACEHOLDER" frontend/src/auth0-config.ts 2>/dev/null || echo "")

if [[ -n "$HAS_PLACEHOLDER_ENV" ]]; then
    echo -e "${RED}🔴 CRITICAL: Placeholder detected in .env.production${NC}"
    echo -e "${YELLOW}   This is why users cannot login!${NC}"
    echo ""
    echo -e "${BLUE}💡 SOLUTION:${NC}"
    echo "1. Get actual Auth0 Client ID from Azure Key Vault 'pathfinder-kv-dev'"
    echo "2. Replace PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID with actual value"
    echo "3. Rebuild frontend container with correct credentials"
    echo "4. Deploy updated container"
    echo ""
    echo -e "${GREEN}📖 Detailed fix instructions: MANUAL_AUTH0_FIX_DETAILED.md${NC}"
    echo -e "${GREEN}🤖 Automated fix script: ./fix-auth0-urgent.sh${NC}"
elif [[ -n "$HAS_PLACEHOLDER_CONFIG" ]]; then
    echo -e "${YELLOW}🟡 WARNING: Placeholder in auth0-config.ts fallback${NC}"
    echo "Environment variable may be correct, but fallback is problematic"
else
    echo -e "${GREEN}✅ No obvious placeholders detected${NC}"
    echo "Issue may be elsewhere - check container build process"
fi

echo ""
echo -e "${BLUE}📋 NEXT STEPS:${NC}"
echo "1. Run automated fix: ./fix-auth0-urgent.sh"
echo "2. OR follow manual guide: MANUAL_AUTH0_FIX_DETAILED.md" 
echo "3. Test login functionality after fix"
echo "4. Verify users can access dashboard"
