#!/bin/bash

# Hardcoded Auth0 Fix - No Environment Variables Needed
# This approach embeds Auth0 config directly in the source code

set -e

echo "🔧 HARDCODED AUTH0 FIX DEPLOYMENT"
echo "================================="

# Get timestamp for unique tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="hardcoded-auth0-$TIMESTAMP"

echo "📋 Using hardcoded Auth0 configuration:"
echo "- Domain: dev-jwnud3v8ghqnyygr.us.auth0.com"
echo "- Client ID: KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn"
echo "- Audience: https://pathfinder-api.com"
echo "- Image Tag: $IMAGE_TAG"

echo ""
echo "🏗️ Building frontend with hardcoded Auth0 config..."
cd frontend

# Build without environment variables - using hardcoded values
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
  --build-arg ENVIRONMENT="production" \
  .

echo "✅ Build completed"

echo ""
echo "🔄 Updating container app..."
cd ..

az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG

echo "✅ Container app updated"

echo ""
echo "⏳ Waiting for deployment..."
sleep 60

echo ""
echo "🧪 Testing hardcoded Auth0 deployment..."

# Test multiple times to ensure deployment is complete
for i in {1..3}; do
  echo "Test attempt $i..."
  
  JS_FILE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//' | sed 's/"//') 
  
  if [ -n "$JS_FILE" ]; then
    echo "✅ JavaScript file: $JS_FILE"
    
    # Check for our hardcoded Auth0 domain
    AUTH0_FOUND=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -o "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | head -1)
    
    if [ -n "$AUTH0_FOUND" ]; then
      echo "🎉 SUCCESS! Hardcoded Auth0 domain found: $AUTH0_FOUND"
      echo ""
      echo "✅ HARDCODED AUTH0 FIX SUCCESSFUL!"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "Frontend: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
      echo "Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com"
      echo "Image: pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG"
      echo ""
      echo "🧪 TEST INSTRUCTIONS:"
      echo "1. Visit the frontend URL"
      echo "2. Click Sign Up or Log In"
      echo "3. Verify redirect goes to: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
      echo "4. Should NOT go to: https://authorize/?client_id=..."
      break
    else
      echo "❌ Auth0 domain not found (attempt $i/3)"
      if [ $i -lt 3 ]; then
        echo "Waiting 30 seconds before retry..."
        sleep 30
      fi
    fi
  else
    echo "❌ JavaScript file not found (attempt $i/3)"
    if [ $i -lt 3 ]; then
      sleep 30
    fi
  fi
done

echo ""
echo "🏁 Hardcoded deployment completed!"
