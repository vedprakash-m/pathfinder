#!/bin/bash

# EMERGENCY AUTH0 FIX - FINAL ATTEMPT
# This script eliminates ALL possible sources of Auth0 configuration issues

set -e

echo "🚨 EMERGENCY AUTH0 FIX - FINAL ATTEMPT"
echo "====================================="

# Get unique timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="emergency-auth0-$TIMESTAMP"

echo "📋 Emergency deployment configuration:"
echo "- Image Tag: $IMAGE_TAG"
echo "- Strategy: Hardcoded configuration with debug logging"
echo "- Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com (HARDCODED)"

echo ""
echo "🔧 Step 1: Verifying all Auth0 configurations are hardcoded..."

echo "✅ Checking auth0-config.ts..."
if grep -q "dev-jwnud3v8ghqnyygr.us.auth0.com" frontend/src/auth0-config.ts; then
    echo "  ✓ auth0-config.ts contains correct domain"
else
    echo "  ❌ auth0-config.ts missing correct domain"
    exit 1
fi

echo "✅ Checking auth.ts imports..."
if grep -q "import auth0Config from '../auth0-config'" frontend/src/services/auth.ts; then
    echo "  ✓ auth.ts imports hardcoded config"
else
    echo "  ❌ auth.ts not using hardcoded config"
    exit 1
fi

echo "✅ Checking main.tsx imports..."
if grep -q "import auth0Config from './auth0-config.ts'" frontend/src/main.tsx; then
    echo "  ✓ main.tsx imports hardcoded config"
else
    echo "  ❌ main.tsx not using hardcoded config"
    exit 1
fi

echo ""
echo "🏗️ Step 2: Building frontend with COMPLETE hardcoded configuration..."
cd frontend

# Build with ACR and aggressive cache busting
echo "Starting emergency ACR build..."
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --no-cache \
  .

if [ $? -eq 0 ]; then
    echo "✅ Emergency ACR build completed successfully"
else
    echo "❌ Emergency ACR build failed"
    exit 1
fi

echo ""
echo "🔄 Step 3: Force updating container app..."
cd ..

# Force restart and update with new image
echo "Force updating container app with new image..."
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG \
  --min-replicas 0 \
  --max-replicas 3

# Force restart by scaling down and up
echo "Force restarting container app..."
az containerapp revision deactivate \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev

sleep 10

az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --min-replicas 1 \
  --max-replicas 3

if [ $? -eq 0 ]; then
    echo "✅ Emergency container app update completed"
else
    echo "❌ Emergency container app update failed"
    exit 1
fi

echo ""
echo "⏳ Step 4: Waiting for emergency deployment to stabilize..."
sleep 120

echo ""
echo "🧪 Step 5: Testing emergency deployment..."

# Test frontend accessibility
echo "Testing frontend accessibility..."
for i in {1..10}; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" 2>/dev/null || echo "000")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ Frontend accessible (HTTP $HTTP_STATUS)"
        break
    else
        echo "❌ Frontend not accessible (HTTP $HTTP_STATUS), attempt $i/10"
        if [ $i -lt 10 ]; then
            sleep 15
        fi
    fi
done

if [ "$HTTP_STATUS" != "200" ]; then
    echo "❌ Frontend still not accessible after emergency deployment"
    exit 1
fi

# Test for hardcoded Auth0 domain in bundle
echo ""
echo "Testing for hardcoded Auth0 domain..."
sleep 30

# Get the main JS bundle
FRONTEND_PAGE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" 2>/dev/null)
JS_FILE=$(echo "$FRONTEND_PAGE" | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//g' | sed 's/"//g')

if [ -n "$JS_FILE" ]; then
    echo "Found JS bundle: $JS_FILE"
    
    # Check for our hardcoded domain
    BUNDLE_CONTENT=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" 2>/dev/null)
    DOMAIN_COUNT=$(echo "$BUNDLE_CONTENT" | grep -c "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" || echo "0")
    
    if [ "$DOMAIN_COUNT" -gt "0" ]; then
        echo "🎉 SUCCESS! Found hardcoded Auth0 domain $DOMAIN_COUNT times in bundle"
        
        # Check for debug logging
        DEBUG_LOG=$(echo "$BUNDLE_CONTENT" | grep -o "Auth0 Config Loaded" || echo "")
        if [ -n "$DEBUG_LOG" ]; then
            echo "✅ Debug logging found in bundle"
        fi
        
        echo ""
        echo "✅ EMERGENCY AUTH0 FIX SUCCESSFUL!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🌐 Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
        echo "🔐 Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com (HARDCODED)"
        echo "📦 Image: pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG"
        echo ""
        echo "🎯 FINAL TEST:"
        echo "1. Open the frontend URL in a NEW incognito window"
        echo "2. Open browser developer tools (F12)"
        echo "3. Check Console for 'Auth0 Config Loaded' message"
        echo "4. Click 'Sign Up' or 'Log In'"
        echo "5. Verify redirect goes to: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
        echo ""
        echo "If you STILL see issues, there may be a caching problem."
        echo "Try CTRL+F5 or clear browser cache completely."
        
    else
        echo "❌ Auth0 domain STILL not found in emergency deployment"
        echo "This indicates a fundamental build or configuration issue."
        
        # Debug output
        echo ""
        echo "Debug: Checking for any auth0 references..."
        AUTH0_REFS=$(echo "$BUNDLE_CONTENT" | grep -i "auth0" | head -5 || echo "No auth0 references found")
        echo "$AUTH0_REFS"
        
        echo ""
        echo "Debug: Checking for environment variable patterns..."
        ENV_PATTERNS=$(echo "$BUNDLE_CONTENT" | grep -o "VITE_AUTH0[^\"']*" | head -5 || echo "No VITE_AUTH0 patterns found")
        echo "$ENV_PATTERNS"
    fi
else
    echo "❌ Could not find JavaScript bundle file"
fi

echo ""
echo "🚨 Emergency deployment completed!"
echo "Image tag: $IMAGE_TAG"
echo "Status: $([ "$DOMAIN_COUNT" -gt "0" ] && echo "SUCCESS" || echo "FAILED")"
