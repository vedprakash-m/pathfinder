#!/bin/bash

# Nuclear Option: Complete Auth0 Fix with Full Rebuild
# This script completely rebuilds and redeploys the frontend from scratch

set -e

echo "💥 NUCLEAR AUTH0 FIX - COMPLETE REBUILD"
echo "======================================="

# Get timestamp for unique tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="nuclear-auth0-$TIMESTAMP"

echo "📋 Complete rebuild configuration:"
echo "- Image Tag: $IMAGE_TAG"
echo "- Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com (HARDCODED)"
echo "- Auth0 Client ID: KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn (HARDCODED)"
echo "- Auth0 Audience: https://pathfinder-api.com (HARDCODED)"

echo ""
echo "🔧 Step 1: Verify hardcoded Auth0 configuration exists..."
if [ -f "frontend/src/auth0-config.ts" ]; then
    echo "✅ Found auth0-config.ts"
    cat frontend/src/auth0-config.ts
else
    echo "❌ auth0-config.ts not found, creating it..."
    cat > frontend/src/auth0-config.ts << 'EOF'
// Auth0 configuration with hardcoded values - NO ENVIRONMENT VARIABLES
const auth0Config = {
  domain: 'dev-jwnud3v8ghqnyygr.us.auth0.com',
  clientId: 'KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn',
  authorizationParams: {
    redirect_uri: window.location.origin,
    audience: 'https://pathfinder-api.com',
  },
}

export default auth0Config;
EOF
    echo "✅ Created auth0-config.ts with hardcoded values"
fi

echo ""
echo "🏗️ Step 2: Building frontend with ACR..."
cd frontend

# Build with minimal arguments to avoid environment variable issues
echo "Starting ACR build with hardcoded configuration..."
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  .

if [ $? -eq 0 ]; then
    echo "✅ ACR build completed successfully"
else
    echo "❌ ACR build failed"
    exit 1
fi

echo ""
echo "🔄 Step 3: Force update container app with new image..."
cd ..

# Force update the container app
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG \
  --min-replicas 1 \
  --max-replicas 3

if [ $? -eq 0 ]; then
    echo "✅ Container app update completed"
else
    echo "❌ Container app update failed"
    exit 1
fi

echo ""
echo "⏳ Step 4: Waiting for deployment to stabilize..."
sleep 90

echo ""
echo "🧪 Step 5: Testing the nuclear deployment..."

# Test frontend accessibility
echo "Testing frontend accessibility..."
for i in {1..5}; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" 2>/dev/null || echo "000")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Frontend accessible (HTTP $HTTP_STATUS)"
        break
    else
        echo "❌ Frontend not accessible (HTTP $HTTP_STATUS), attempt $i/5"
        if [ $i -lt 5 ]; then
            sleep 20
        fi
    fi
done

# Test Auth0 configuration
echo ""
echo "Testing Auth0 configuration in deployed app..."
JS_FILE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" 2>/dev/null | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//' | sed 's/"//') 

if [ -n "$JS_FILE" ]; then
    echo "✅ Found JavaScript file: $JS_FILE"
    
    # Check for hardcoded Auth0 domain
    AUTH0_FOUND=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" 2>/dev/null | grep -o "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | head -1)
    
    if [ -n "$AUTH0_FOUND" ]; then
        echo "🎉 NUCLEAR SUCCESS! Auth0 domain found: $AUTH0_FOUND"
        echo ""
        echo "✅ AUTH0 NUCLEAR FIX SUCCESSFUL!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🌐 Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
        echo "🔐 Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com"
        echo "📦 Image: pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG"
        echo ""
        echo "🎯 LOGIN TEST:"
        echo "1. Open the frontend URL"
        echo "2. Click 'Sign Up' or 'Log In'"
        echo "3. You should be redirected to:"
        echo "   ✅ https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
        echo "4. You should NOT see:"
        echo "   ❌ https://authorize/?client_id=..."
        echo ""
        echo "If you still see the error, there may be a browser cache issue."
        echo "Try opening in an incognito/private window."
        
    else
        echo "❌ Auth0 domain STILL not found in deployed app"
        echo "This indicates a deeper configuration issue."
        echo ""
        echo "Debugging info:"
        echo "Looking for any Auth0 references in the bundle..."
        curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" 2>/dev/null | grep -i "auth0" | head -5 || echo "No Auth0 references found at all"
    fi
else
    echo "❌ Could not find JavaScript file in frontend response"
    echo "This suggests the deployment may not be working correctly"
fi

echo ""
echo "💥 Nuclear deployment completed!"
echo "Image tag: $IMAGE_TAG"
