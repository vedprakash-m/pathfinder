#!/bin/bash
# Immediate Auth0 Fix - Build with correct values

echo "🚨 IMMEDIATE AUTH0 FIX - Building with correct domain"
echo "====================================================="

IMAGE_TAG="auth0-fix-immediate-$(date +%s)"
REGISTRY="pathfinderdevregistry"

echo "📦 Building with correct Auth0 domain in JavaScript bundle..."

# Build with the ACTUAL Auth0 domain embedded in the JavaScript
az acr build --registry $REGISTRY \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg VITE_AUTH0_DOMAIN=dev-jwnud3v8ghqnyygr.us.auth0.com \
  --build-arg VITE_AUTH0_CLIENT_ID=KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn \
  --build-arg VITE_AUTH0_AUDIENCE=https://pathfinder-api.com \
  --build-arg VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io \
  --build-arg ENVIRONMENT=production \
  ./frontend

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully"
    
    echo "🔄 Updating container app..."
    az containerapp update \
      --name pathfinder-frontend \
      --resource-group pathfinder-rg-dev \
      --image $REGISTRY.azurecr.io/pathfinder-frontend:$IMAGE_TAG \
      --revision-suffix fix$(date +%s)
    
    if [ $? -eq 0 ]; then
        echo "✅ Container app updated!"
        echo ""
        echo "🧪 Test the fix:"
        echo "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
        echo ""
        echo "⏳ Wait 2-3 minutes for deployment, then test login"
    else
        echo "❌ Container update failed"
    fi
else
    echo "❌ Build failed"
fi
