#!/bin/bash

# Force Auth0 Fix Deployment - Complete rebuild and deployment
# This script rebuilds the frontend with correct Auth0 config and deploys to production

set -e

echo "🚀 Starting Force Auth0 Fix Deployment..."
echo "=================================================="

# Get current timestamp for unique image tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="auth0-fix-$TIMESTAMP"

echo "📋 Deployment Configuration:"
echo "- Resource Group: pathfinder-rg-dev"
echo "- Registry: pathfinderregistry"
echo "- Image Tag: $IMAGE_TAG"
echo "- Target: Production Environment"

# Step 1: Get Auth0 configuration from Key Vault
echo ""
echo "🔐 Retrieving Auth0 configuration from Key Vault..."
AUTH0_DOMAIN=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-domain --query 'value' --output tsv)
AUTH0_CLIENT_ID=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-client-id --query 'value' --output tsv)
AUTH0_AUDIENCE=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-audience --query 'value' --output tsv)

echo "✅ Auth0 Domain: $AUTH0_DOMAIN"
echo "✅ Auth0 Client ID: ${AUTH0_CLIENT_ID:0:8}..."
echo "✅ Auth0 Audience: $AUTH0_AUDIENCE"

# Step 2: Build and push new image with correct configuration
echo ""
echo "🏗️  Building frontend image with Auth0 configuration..."
cd frontend

# Build image with proper Auth0 configuration
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg VITE_AUTH0_DOMAIN="$AUTH0_DOMAIN" \
  --build-arg VITE_AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID" \
  --build-arg VITE_AUTH0_AUDIENCE="$AUTH0_AUDIENCE" \
  --build-arg VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
  --build-arg ENVIRONMENT="production" \
  .

echo "✅ Image built and pushed to registry"

# Step 3: Update container app with new image
echo ""
echo "🔄 Updating container app with new image..."
cd ..

az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG

echo "✅ Container app updated with new image"

# Step 4: Wait for deployment to complete
echo ""
echo "⏳ Waiting for deployment to complete..."
sleep 30

# Step 5: Verify the deployment
echo ""
echo "🔍 Verifying deployment..."

# Check if new revision is active
ACTIVE_REVISION=$(az containerapp revision list \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --query '[?properties.active].name' \
  --output tsv)

echo "✅ Active revision: $ACTIVE_REVISION"

# Test the Auth0 configuration in the live app
echo ""
echo "🧪 Testing Auth0 configuration in live application..."
sleep 10

# Check if the app is responding
if curl -s -f "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" > /dev/null; then
    echo "✅ Frontend is responding"
    
    # Try to find Auth0 domain in the response
    FOUND_DOMAIN=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" | grep -o "$AUTH0_DOMAIN" | head -1 || echo "")
    if [ -n "$FOUND_DOMAIN" ]; then
        echo "✅ Correct Auth0 domain found in frontend: $FOUND_DOMAIN"
    else
        echo "⚠️  Auth0 domain not detected in frontend response"
    fi
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "🎉 Deployment Complete!"
echo "=================================================="
echo "Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Auth0 Domain: $AUTH0_DOMAIN"
echo "Image Tag: $IMAGE_TAG"
echo ""
echo "Please test the login functionality to verify the Auth0 fix is working."
echo "The login button should now redirect to: https://$AUTH0_DOMAIN/authorize/..."
