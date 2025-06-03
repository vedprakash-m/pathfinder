#!/bin/bash

# CRITICAL AUTH0 FIX - Code-level fixes
# This addresses the root cause: missing fallback values in the frontend code

set -e

echo "🚨 CRITICAL AUTH0 FIX - Code Level"
echo "=================================="
echo "Issue: Frontend code using '!' assertions without fallbacks"
echo "Fix: Added proper fallback values in TypeScript code"
echo ""

REGISTRY="pathfinderdevregistry"
RESOURCE_GROUP="pathfinder-rg-dev"
APP_NAME="pathfinder-frontend"
TAG="critical-fix-$(date +%Y%m%d-%H%M%S)"

echo "🔧 Changes made:"
echo "✅ Updated main.tsx with fallback values"
echo "✅ Updated auth.ts with fallback values"
echo "✅ Added debug logging for development"
echo ""

echo "📦 Building new image: pathfinder-frontend:$TAG"

# Build with explicit values AND the code now has fallbacks
az acr build \
  --registry $REGISTRY \
  --image pathfinder-frontend:$TAG \
  --build-arg VITE_AUTH0_DOMAIN=dev-jwnud3v8ghqnyygr.us.auth0.com \
  --build-arg VITE_AUTH0_CLIENT_ID=KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn \
  --build-arg VITE_AUTH0_AUDIENCE=https://pathfinder-api.com \
  --build-arg VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io \
  --build-arg ENVIRONMENT=production \
  ./frontend

echo "✅ Build completed!"
echo ""

echo "🚀 Deploying to Container App..."
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY.azurecr.io/pathfinder-frontend:$TAG \
  --revision-suffix critical$(date +%s)

echo ""
echo "🎉 CRITICAL FIX DEPLOYED!"
echo "========================"
echo "Changes:"
echo "1. ✅ Code now has proper fallback values"
echo "2. ✅ Build arguments explicitly set"
echo "3. ✅ Runtime environment variables from Key Vault"
echo ""
echo "Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo ""
echo "🧪 Test immediately:"
echo "1. Open the URL above"
echo "2. Click Login"
echo "3. Should redirect to: https://dev-jwnud3v8ghqnyygr.us.auth0.com"
echo ""
echo "If this doesn't work, the issue is deeper in the Auth0 React SDK configuration."
