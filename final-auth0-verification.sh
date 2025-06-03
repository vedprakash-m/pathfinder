#!/bin/bash

# Final Auth0 Fix Verification and Deployment
# This script ensures the Auth0 configuration is correctly deployed

echo "🔍 Final Auth0 Fix Verification"
echo "================================"

# Step 1: Check current container app status
echo "1. Checking container app status..."
ACTIVE_REVISION=$(az containerapp revision list \
    --name pathfinder-frontend \
    --resource-group pathfinder-rg-dev \
    --query '[?properties.active].{name:name,image:properties.template.containers[0].image}' \
    --output tsv 2>/dev/null || echo "failed")

if [ "$ACTIVE_REVISION" != "failed" ]; then
    echo "✅ Active revision found: $ACTIVE_REVISION"
else
    echo "❌ Could not retrieve active revision"
fi

# Step 2: Test frontend accessibility
echo ""
echo "2. Testing frontend accessibility..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Frontend is accessible (HTTP $HTTP_STATUS)"
else
    echo "❌ Frontend is not accessible (HTTP $HTTP_STATUS)"
fi

# Step 3: Check for Auth0 configuration in the live app
echo ""
echo "3. Checking Auth0 configuration in live application..."

# Get the main JS file
JS_FILE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//' | sed 's/"//' || echo "")

if [ -n "$JS_FILE" ]; then
    echo "✅ Found JavaScript file: $JS_FILE"
    
    # Test for the correct Auth0 domain
    AUTH0_FOUND=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -o "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | head -1 || echo "")
    
    if [ -n "$AUTH0_FOUND" ]; then
        echo "✅ Correct Auth0 domain found: $AUTH0_FOUND"
        echo "🎉 AUTH0 FIX SUCCESSFUL!"
    else
        echo "❌ Correct Auth0 domain not found in JavaScript bundle"
        echo "🚨 AUTH0 FIX STILL NEEDED"
        
        # Try to find what Auth0 configuration is actually present
        echo ""
        echo "Checking what Auth0 configuration is present..."
        curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -i "auth0" | head -3 || echo "No Auth0 references found"
    fi
else
    echo "❌ Could not find JavaScript file in frontend"
fi

# Step 4: Manual deployment if needed
if [ -z "$AUTH0_FOUND" ]; then
    echo ""
    echo "4. Triggering manual deployment with correct Auth0 configuration..."
    
    # Get current timestamp for unique tag
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    IMAGE_TAG="auth0-verified-$TIMESTAMP"
    
    echo "Building image: pathfinder-frontend:$IMAGE_TAG"
    
    cd frontend
    az acr build \
        --registry pathfinderregistry \
        --image pathfinder-frontend:$IMAGE_TAG \
        --build-arg VITE_AUTH0_DOMAIN="dev-jwnud3v8ghqnyygr.us.auth0.com" \
        --build-arg VITE_AUTH0_CLIENT_ID="KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn" \
        --build-arg VITE_AUTH0_AUDIENCE="https://pathfinder-api.com" \
        --build-arg VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
        --build-arg ENVIRONMENT="production" \
        . && \
    cd .. && \
    az containerapp update \
        --name pathfinder-frontend \
        --resource-group pathfinder-rg-dev \
        --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG
    
    echo "✅ Manual deployment completed with tag: $IMAGE_TAG"
    echo "⏳ Please wait 60 seconds for deployment to complete, then test again"
fi

echo ""
echo "================================"
echo "Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Expected Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com"
echo ""
echo "To test login:"
echo "1. Visit the frontend URL"
echo "2. Click the login button"
echo "3. Verify it redirects to: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
echo "4. Should NOT redirect to: https://authorize/?client_id=..."
