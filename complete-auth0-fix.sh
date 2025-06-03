#!/bin/bash
# Complete Auth0 Login Fix Deployment Script
# This script will:
# 1. Get the actual Auth0 Client ID from Azure Key Vault
# 2. Update the frontend .env.production file
# 3. Build and deploy the fixed frontend

set -e

echo "🚀 Complete Auth0 Login Fix Deployment"
echo "======================================"

# Check if Azure CLI is logged in
if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure CLI first: az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"

# Get Auth0 configuration from Key Vault
echo "🔍 Retrieving Auth0 configuration from Azure Key Vault..."
AUTH0_DOMAIN=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-domain --query 'value' --output tsv)
AUTH0_CLIENT_ID=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-client-id --query 'value' --output tsv)
AUTH0_AUDIENCE=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-audience --query 'value' --output tsv)

if [ -z "$AUTH0_CLIENT_ID" ] || [ -z "$AUTH0_DOMAIN" ]; then
    echo "❌ Could not retrieve Auth0 configuration from Key Vault"
    echo "Please check your Azure Key Vault access permissions"
    exit 1
fi

echo "✅ Auth0 configuration retrieved"
echo "   Domain: $AUTH0_DOMAIN"
echo "   Client ID: ${AUTH0_CLIENT_ID:0:8}..."
echo "   Audience: $AUTH0_AUDIENCE"

# Update frontend .env.production file
echo ""
echo "📝 Updating frontend/.env.production with actual Auth0 credentials..."

cat > frontend/.env.production << EOF
# Production Environment Variables for Pathfinder Frontend
# Updated with actual Auth0 credentials from Azure Key Vault

# Auth0 Configuration - Actual rotated credentials
VITE_AUTH0_DOMAIN=$AUTH0_DOMAIN
VITE_AUTH0_CLIENT_ID=$AUTH0_CLIENT_ID
VITE_AUTH0_AUDIENCE=$AUTH0_AUDIENCE

# API Configuration
VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io
EOF

echo "✅ Updated frontend/.env.production with actual credentials"

# Get timestamp for deployment tracking
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo ""
echo "🔨 Building and deploying fixed frontend..."

# Build frontend with Azure Container Registry
cd frontend

az acr build \
  --registry pathfinderdevregistry \
  --image pathfinder-frontend:auth0-fix-$TIMESTAMP \
  --build-arg VITE_AUTH0_DOMAIN="$AUTH0_DOMAIN" \
  --build-arg VITE_AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID" \
  --build-arg VITE_AUTH0_AUDIENCE="$AUTH0_AUDIENCE" \
  --build-arg VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
  .

echo "✅ Frontend image built successfully"

# Update container app to use new image
echo ""
echo "🚀 Updating container app with fixed image..."

az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderdevregistry.azurecr.io/pathfinder-frontend:auth0-fix-$TIMESTAMP

echo ""
echo "🎉 Auth0 login fix deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for deployment to complete"
echo "2. Test login at: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "3. Verify users can sign up and log in successfully"
echo ""
echo "🔒 Security: Using actual rotated Auth0 credentials from Key Vault"
