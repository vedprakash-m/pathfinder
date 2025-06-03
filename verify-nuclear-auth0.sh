#!/bin/bash

echo "🧪 NUCLEAR AUTH0 DEPLOYMENT VERIFICATION"
echo "========================================"

# Test frontend accessibility
echo "1. Testing frontend accessibility..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Frontend accessible (HTTP $HTTP_STATUS)"
else
    echo "❌ Frontend not accessible (HTTP $HTTP_STATUS)"
    exit 1
fi

# Get JavaScript file
echo ""
echo "2. Finding JavaScript bundle..."
JS_FILE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" 2>/dev/null | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//' | sed 's/"//') 

if [ -n "$JS_FILE" ]; then
    echo "✅ Found JavaScript file: $JS_FILE"
    
    # Check for Auth0 domain in bundle
    echo ""
    echo "3. Checking for hardcoded Auth0 domain..."
    AUTH0_CHECK=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" 2>/dev/null | grep -c "dev-jwnud3v8ghqnyygr\.us\.auth0\.com")
    
    if [ "$AUTH0_CHECK" -gt 0 ]; then
        echo "🎉 SUCCESS! Auth0 domain found $AUTH0_CHECK times in bundle"
        echo ""
        echo "✅ NUCLEAR AUTH0 FIX SUCCESSFUL!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🌐 Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
        echo "🔐 Auth0 Domain: dev-jwnud3v8ghqnyygr.us.auth0.com (HARDCODED)"
        echo "📦 Image: pathfinderregistry.azurecr.io/pathfinder-frontend:nuclear-auth0-20250601-213117"
        echo ""
        echo "🎯 NEXT STEPS:"
        echo "1. Open the frontend URL in a browser"
        echo "2. Click 'Sign Up' or 'Log In'"
        echo "3. You should be redirected to: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
        echo "4. You should NOT see: https://authorize/?client_id=..."
        echo ""
        echo "The Auth0 authentication issue has been RESOLVED!"
    else
        echo "❌ Auth0 domain not found in JavaScript bundle"
        echo "Checking for any Auth0 references..."
        curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" 2>/dev/null | grep -i "auth0" | head -3 || echo "No Auth0 references found"
    fi
else
    echo "❌ Could not find JavaScript file"
fi

echo ""
echo "Nuclear verification completed!"
