#!/bin/bash

# IMMEDIATE AUTH0 FIX
# This script builds a new frontend image with the correct Auth0 configuration
# and deploys it to fix the login redirect issue

set -e

echo "🚨 EMERGENCY AUTH0 FIX"
echo "====================="
echo "Issue: Login redirecting to https://authorize/ instead of Auth0 domain"
echo "Solution: Rebuild frontend with correct Auth0 domain embedded"
echo ""

REGISTRY="pathfinderdevregistry"
RESOURCE_GROUP="pathfinder-rg-dev"
APP_NAME="pathfinder-frontend"
TAG="emergency-fix-$(date +%Y%m%d-%H%M%S)"

echo "🔧 Building new image: pathfinder-frontend:$TAG"
echo "📋 Build arguments:"
echo "   - VITE_AUTH0_DOMAIN: dev-jwnud3v8ghqnyygr.us.auth0.com"
echo "   - VITE_AUTH0_CLIENT_ID: KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn"
echo "   - VITE_AUTH0_AUDIENCE: https://pathfinder-api.com"
echo ""

# Step 1: Build the image
echo "⏳ Step 1/2: Building image..."
az acr build \
  --registry $REGISTRY \
  --image pathfinder-frontend:$TAG \
  --build-arg VITE_AUTH0_DOMAIN=dev-jwnud3v8ghqnyygr.us.auth0.com \
  --build-arg VITE_AUTH0_CLIENT_ID=KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn \
  --build-arg VITE_AUTH0_AUDIENCE=https://pathfinder-api.com \
  --build-arg VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io \
  --build-arg ENVIRONMENT=production \
  ./frontend

echo "✅ Build completed successfully!"
echo ""

# Step 2: Update container app
echo "⏳ Step 2/2: Updating container app..."
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY.azurecr.io/pathfinder-frontend:$TAG \
  --revision-suffix emergency$(date +%s)

echo "✅ Container app updated!"
echo ""
echo "🎉 DEPLOYMENT COMPLETE"
echo "======================"
echo "Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo ""
echo "⏳ Please wait 2-3 minutes for the new revision to be ready"
echo "🧪 Then test the login - it should now redirect to the correct Auth0 domain"
echo ""
echo "Expected behavior:"
echo "✅ Login button should redirect to: https://dev-jwnud3v8ghqnyygr.us.auth0.com"
echo "❌ Should NOT redirect to: https://authorize/"
