#!/bin/bash

# Emergency Auth0 Fix - Direct and Immediate Deployment
# This script forces an immediate rebuild and deployment with verification

set -e

echo "🚨 EMERGENCY AUTH0 FIX - IMMEDIATE DEPLOYMENT"
echo "=============================================="

# Get timestamp for unique tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="emergency-auth0-$TIMESTAMP"

echo "📋 Configuration:"
echo "- Image Tag: $IMAGE_TAG"
echo "- Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com"
echo "- Auth0 Client ID: KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn"
echo "- Auth0 Audience: https://pathfinder-api.com"

echo ""
echo "🏗️ Building frontend with HARDCODED Auth0 configuration..."
cd frontend

# Create a temporary build file with hardcoded values
cat > temp-build.js << 'EOF'
// Temporary build verification
console.log('Auth0 Domain:', 'dev-jwnud3v8ghqnyygr.us.auth0.com');
console.log('Auth0 Client ID:', 'KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn');
console.log('Auth0 Audience:', 'https://pathfinder-api.com');
EOF

# Build with ACR
echo "Starting ACR build..."
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg VITE_AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com" \
  --build-arg VITE_AUTH0_CLIENT_ID="KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn" \
  --build-arg VITE_AUTH0_AUDIENCE="https://pathfinder-api.com" \
  --build-arg VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
  --build-arg ENVIRONMENT="production" \
  .

echo "✅ Build completed"

# Clean up temp file
rm -f temp-build.js

echo ""
echo "🔄 Updating container app..."
cd ..

az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG

echo "✅ Container app updated"

echo ""
echo "⏳ Waiting for deployment to complete..."
sleep 45

echo ""
echo "🧪 Testing deployment..."

# Test if frontend is responding
for i in {1..5}; do
  echo "Attempt $i: Testing frontend accessibility..."
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" || echo "000")
  
  if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Frontend is accessible (HTTP $HTTP_STATUS)"
    break
  else
    echo "❌ Frontend not accessible (HTTP $HTTP_STATUS), retrying in 15 seconds..."
    sleep 15
  fi
done

# Get the JavaScript file and check Auth0 configuration
echo ""
echo "🔍 Checking Auth0 configuration in deployed application..."

JS_FILE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//' | sed 's/"//') 

if [ -n "$JS_FILE" ]; then
  echo "✅ Found JavaScript file: $JS_FILE"
  
  # Check for correct Auth0 domain
  echo "Searching for Auth0 domain in JavaScript bundle..."
  AUTH0_FOUND=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -o "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | head -1)
  
  if [ -n "$AUTH0_FOUND" ]; then
    echo "🎉 SUCCESS! Correct Auth0 domain found: $AUTH0_FOUND"
    echo ""
    echo "✅ AUTH0 FIX DEPLOYMENT SUCCESSFUL!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
    echo "Login should now redirect to: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
    echo "Image Tag: $IMAGE_TAG"
  else
    echo "❌ Auth0 domain not found in JavaScript bundle"
    echo "Deployment may still be in progress or there's a configuration issue"
    
    # Show what Auth0 references are actually present
    echo ""
    echo "Auth0 references found in bundle:"
    curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -i "auth0" | head -3 || echo "No Auth0 references found"
  fi
else
  echo "❌ Could not find JavaScript file in frontend response"
fi

echo ""
echo "🏁 Emergency deployment completed!"
echo "Image: pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG"
