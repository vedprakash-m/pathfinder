#!/bin/bash

# Complete Auth0 Fix - Azure CLI Version
# Run this script when Azure CLI access is restored

set -e

echo "🔧 Completing Auth0 Login Fix"
echo "==============================="
echo ""

# Check Azure CLI login
if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure CLI first:"
    echo "   az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"
echo ""

# Get Auth0 Client ID from Key Vault
echo "📥 Retrieving Auth0 Client ID from Azure Key Vault..."
AUTH0_CLIENT_ID=$(az keyvault secret show \
    --vault-name pathfinder-kv-dev \
    --name auth0-client-id \
    --query 'value' \
    --output tsv)

if [[ -z "$AUTH0_CLIENT_ID" ]]; then
    echo "❌ Failed to retrieve Auth0 Client ID from Key Vault"
    echo "   Vault: pathfinder-kv-dev"
    echo "   Secret: auth0-client-id"
    exit 1
fi

echo "✅ Retrieved Auth0 Client ID: ${AUTH0_CLIENT_ID:0:8}..."
echo ""

# Update frontend .env.production file
echo "📝 Updating frontend/.env.production with actual Auth0 Client ID..."

# Backup current file
cp frontend/.env.production frontend/.env.production.backup

# Replace placeholder with actual Client ID
sed -i.bak "s/PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID/$AUTH0_CLIENT_ID/g" frontend/.env.production

echo "✅ Updated frontend/.env.production"
echo "   Backup saved: frontend/.env.production.backup"
echo ""

# Verify the update
echo "🔍 Verifying update..."
if grep -q "$AUTH0_CLIENT_ID" frontend/.env.production; then
    echo "✅ Auth0 Client ID successfully updated in frontend/.env.production"
else
    echo "❌ Failed to update Auth0 Client ID"
    exit 1
fi

echo ""

# Build and deploy frontend
echo "🏗️  Building and deploying frontend with correct Auth0 credentials..."

# Set environment variables for build
export VITE_AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com"
export VITE_AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID"
export VITE_AUTH0_AUDIENCE="https://pathfinder-api.com"
export VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

# Build and push frontend container
az acr build \
    --registry pathfinderdevregistry \
    --image pathfinder-frontend:auth0-fix-$(date +%Y%m%d-%H%M%S) \
    --file frontend/Dockerfile \
    --build-arg VITE_AUTH0_DOMAIN="$VITE_AUTH0_DOMAIN" \
    --build-arg VITE_AUTH0_CLIENT_ID="$VITE_AUTH0_CLIENT_ID" \
    --build-arg VITE_AUTH0_AUDIENCE="$VITE_AUTH0_AUDIENCE" \
    --build-arg VITE_API_URL="$VITE_API_URL" \
    frontend/

echo "✅ Frontend container built with correct Auth0 credentials"
echo ""

# Update container app
echo "🚀 Updating frontend container app..."
az containerapp update \
    --name pathfinder-frontend \
    --resource-group pathfinder-rg-dev \
    --image pathfinderdevregistry.azurecr.io/pathfinder-frontend:auth0-fix-$(date +%Y%m%d-%H%M%S)

echo "✅ Frontend container app updated"
echo ""

# Wait for deployment
echo "⏳ Waiting for deployment to complete..."
sleep 30

# Verify deployment
echo "🔍 Verifying deployment..."
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"

if curl -s --head "$FRONTEND_URL" | grep -q "200 OK"; then
    echo "✅ Frontend is responding successfully"
    echo "   URL: $FRONTEND_URL"
else
    echo "⚠️  Frontend may still be starting up"
    echo "   URL: $FRONTEND_URL"
    echo "   Please wait a few minutes and check manually"
fi

echo ""
echo "🎉 Auth0 Fix Completed!"
echo "========================="
echo ""
echo "✅ Actions completed:"
echo "   • Retrieved actual Auth0 Client ID from Key Vault"
echo "   • Updated frontend/.env.production with correct credentials"
echo "   • Built new frontend container with Auth0 credentials embedded"
echo "   • Deployed updated container to pathfinder-frontend"
echo ""
echo "🧪 Next steps:"
echo "   1. Test login functionality at: $FRONTEND_URL"
echo "   2. Verify no 'Unknown host' errors in browser console"
echo "   3. Confirm users can complete Auth0 authentication flow"
echo ""
echo "📋 If issues persist:"
echo "   • Check browser console for Auth0 errors"
echo "   • Verify Auth0 application configuration in Auth0 Dashboard"
echo "   • Review container app logs in Azure Portal"

# Clean up environment variables
unset VITE_AUTH0_DOMAIN
unset VITE_AUTH0_CLIENT_ID
unset VITE_AUTH0_AUDIENCE
unset VITE_API_URL
