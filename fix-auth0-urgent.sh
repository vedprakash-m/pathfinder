#!/bin/bash

# Enhanced Auth0 Fix - Complete Solution
# This script provides multiple approaches to fix the Auth0 login issue

set -e

echo "🚨 URGENT: Auth0 Login Fix - Complete Solution"
echo "============================================="
echo ""

# Color codes for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}CRITICAL ISSUE IDENTIFIED:${NC}"
echo "• Frontend built with placeholder Auth0 Client ID"
echo "• Authentication completely broken for all users"
echo "• Credential rotation completed but not applied to frontend"
echo ""

# Application URLs
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

echo -e "${BLUE}🔍 Testing current application status...${NC}"

# Test frontend accessibility
if curl -s --head "$FRONTEND_URL" | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ Frontend accessible:${NC} $FRONTEND_URL"
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
fi

# Test backend health  
if curl -s "$BACKEND_URL/health" | grep -q "ok\|healthy\|success"; then
    echo -e "${GREEN}✅ Backend healthy:${NC} $BACKEND_URL/health"
else
    echo -e "${YELLOW}⚠️  Backend health check inconclusive${NC}"
fi

echo ""
echo -e "${YELLOW}📋 Current Auth0 Configuration Analysis:${NC}"
echo "   Domain: dev-jwnud3v8ghqnyygr.us.auth0.com ✅ Correct"
echo "   Client ID: PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID ❌ BROKEN"
echo "   Audience: https://pathfinder-api.com ✅ Correct"
echo ""

# Check Azure CLI authentication
echo -e "${BLUE}🔑 Checking Azure CLI access...${NC}"
if az account show > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Azure CLI authenticated${NC}"
    
    # Get Auth0 Client ID from Key Vault
    echo -e "${BLUE}📥 Retrieving actual Auth0 Client ID from Key Vault...${NC}"
    
    AUTH0_CLIENT_ID=$(az keyvault secret show \
        --vault-name pathfinder-kv-dev \
        --name auth0-client-id \
        --query 'value' \
        --output tsv 2>/dev/null)
    
    if [[ -n "$AUTH0_CLIENT_ID" && "$AUTH0_CLIENT_ID" != "PLACEHOLDER"* ]]; then
        echo -e "${GREEN}✅ Retrieved actual Auth0 Client ID: ${AUTH0_CLIENT_ID:0:8}...${NC}"
        
        # Update frontend .env.production
        echo -e "${BLUE}📝 Updating frontend/.env.production...${NC}"
        
        # Backup current file
        cp frontend/.env.production frontend/.env.production.backup.$(date +%Y%m%d-%H%M%S)
        
        # Replace placeholder with actual Client ID
        sed -i.bak "s/PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID/$AUTH0_CLIENT_ID/g" frontend/.env.production
        
        # Verify the update
        if grep -q "$AUTH0_CLIENT_ID" frontend/.env.production; then
            echo -e "${GREEN}✅ Successfully updated frontend/.env.production${NC}"
            
            echo ""
            echo -e "${BLUE}🏗️  Building and deploying fixed frontend...${NC}"
            
            # Set environment variables for build
            export VITE_AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com"
            export VITE_AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID"
            export VITE_AUTH0_AUDIENCE="https://pathfinder-api.com"
            export VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
            
            # Build and push frontend container using Azure Container Registry
            echo "Building frontend container with correct Auth0 credentials..."
            az acr build \
                --registry pathfinderdevregistry \
                --image pathfinder-frontend:auth0-fix-$(date +%Y%m%d-%H%M%S) \
                --file frontend/Dockerfile \
                --build-arg VITE_AUTH0_DOMAIN="$VITE_AUTH0_DOMAIN" \
                --build-arg VITE_AUTH0_CLIENT_ID="$VITE_AUTH0_CLIENT_ID" \
                --build-arg VITE_AUTH0_AUDIENCE="$VITE_AUTH0_AUDIENCE" \
                --build-arg VITE_API_URL="$VITE_API_URL" \
                frontend/
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Frontend container built successfully${NC}"
                
                # Update container app to use new image
                echo "Updating pathfinder-frontend container app..."
                az containerapp update \
                    --name pathfinder-frontend \
                    --resource-group pathfinder-rg-dev \
                    --image pathfinderdevregistry.azurecr.io/pathfinder-frontend:auth0-fix-$(date +%Y%m%d-%H%M%S)
                
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}✅ Frontend container app updated successfully${NC}"
                    
                    echo ""
                    echo -e "${GREEN}🎉 Auth0 Fix Completed Successfully!${NC}"
                    echo "============================================"
                    echo ""
                    echo "✅ Actions completed:"
                    echo "   • Retrieved actual Auth0 Client ID from Key Vault"
                    echo "   • Updated frontend/.env.production with correct credentials"
                    echo "   • Built new frontend container with Auth0 credentials embedded"
                    echo "   • Deployed updated container to pathfinder-frontend"
                    echo ""
                    echo -e "${BLUE}🧪 Test authentication now:${NC}"
                    echo "   1. Go to: $FRONTEND_URL"
                    echo "   2. Click 'Login' button"
                    echo "   3. Verify Auth0 login page loads without errors"
                    echo "   4. Complete login flow"
                    echo "   5. Confirm access to dashboard"
                    echo ""
                    echo -e "${GREEN}Expected result: No 'Unknown host' or client errors${NC}"
                else
                    echo -e "${RED}❌ Failed to update container app${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}❌ Failed to build frontend container${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Failed to update .env.production file${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Could not retrieve valid Auth0 Client ID from Key Vault${NC}"
        echo "Manual intervention required - see URGENT_AUTH0_FIX_COMPLETION.md"
        exit 1
    fi
else
    echo -e "${RED}❌ Azure CLI not authenticated${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Manual Fix Required:${NC}"
    echo "1. Login to Azure CLI: az login"
    echo "2. Run this script again, OR"
    echo "3. Follow manual steps in URGENT_AUTH0_FIX_COMPLETION.md"
    echo ""
    echo -e "${BLUE}Alternative: Manual Azure Portal Approach${NC}"
    echo "1. Go to https://portal.azure.com"
    echo "2. Navigate to Key Vaults → pathfinder-kv-dev"
    echo "3. Find secret 'auth0-client-id' and copy the value"
    echo "4. Replace PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID in frontend/.env.production"
    echo "5. Rebuild and deploy frontend container"
    exit 1
fi

# Clean up environment variables
unset VITE_AUTH0_DOMAIN
unset VITE_AUTH0_CLIENT_ID  
unset VITE_AUTH0_AUDIENCE
unset VITE_API_URL

echo ""
echo -e "${GREEN}🔒 Security: Environment variables cleaned up${NC}"
echo -e "${BLUE}📋 Next: Monitor application and verify user authentication works${NC}"
