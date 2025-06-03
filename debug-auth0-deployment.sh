#!/bin/bash

echo "🔍 DEBUGGING AUTH0 CONFIGURATION IN DEPLOYED APP"
echo "================================================="

# Step 1: Check if frontend is accessible
echo "1. Testing frontend accessibility..."
HTTP_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io")
echo "Frontend HTTP status: $HTTP_STATUS"

if [ "$HTTP_STATUS" != "200" ]; then
    echo "❌ Frontend not accessible, exiting"
    exit 1
fi

echo ""
echo "2. Fetching frontend HTML to find JavaScript files..."
FRONTEND_HTML=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io")

# Extract script src
JS_FILES=$(echo "$FRONTEND_HTML" | grep -o 'src="[^"]*\.js"' | sed 's/src="//g' | sed 's/"//g')

echo "Found JavaScript files:"
echo "$JS_FILES"

echo ""
echo "3. Checking Auth0 configuration in each JavaScript file..."

for js_file in $JS_FILES; do
    echo ""
    echo "Checking file: $js_file"
    echo "Full URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$js_file"
    
    # Download and check for Auth0 domain
    BUNDLE_CONTENT=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$js_file")
    
    # Look for our correct Auth0 domain
    CORRECT_DOMAIN_COUNT=$(echo "$BUNDLE_CONTENT" | grep -c "dev-jwnud3v8ghqnyygr\.us\.auth0\.com")
    
    # Look for any incorrect domains or empty domain issues
    INCORRECT_DOMAINS=$(echo "$BUNDLE_CONTENT" | grep -o "dev-[^\"]*\.auth0\.com" | grep -v "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | head -5)
    
    # Look for empty/undefined Auth0 config patterns
    EMPTY_CONFIGS=$(echo "$BUNDLE_CONTENT" | grep -o "authorize/?[^\"]*" | head -3)
    
    echo "  ✅ Correct domain occurrences: $CORRECT_DOMAIN_COUNT"
    
    if [ -n "$INCORRECT_DOMAINS" ]; then
        echo "  ❌ Found incorrect domains:"
        echo "$INCORRECT_DOMAINS"
    else
        echo "  ✅ No incorrect domains found"
    fi
    
    if [ -n "$EMPTY_CONFIGS" ]; then
        echo "  ❌ Found empty/malformed Auth0 configs:"
        echo "$EMPTY_CONFIGS"
    else
        echo "  ✅ No empty configs found"
    fi
    
    # Look for any auth0 config objects
    AUTH0_CONFIG_PATTERN=$(echo "$BUNDLE_CONTENT" | grep -o "domain[\"']*:[\"']*[^\"']*[\"']*" | head -3)
    if [ -n "$AUTH0_CONFIG_PATTERN" ]; then
        echo "  📋 Auth0 config patterns found:"
        echo "$AUTH0_CONFIG_PATTERN"
    fi
done

echo ""
echo "4. Summary and recommendations..."

# Final check: try to simulate the Auth0 redirect
echo ""
echo "5. Testing Auth0 redirect URL construction..."
TEST_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Opening browser developer tools on: $TEST_URL"
echo ""
echo "🎯 MANUAL TESTING STEPS:"
echo "1. Open: $TEST_URL"
echo "2. Open browser developer tools (F12)"
echo "3. Go to Console tab"
echo "4. Click 'Sign Up' or 'Log In'"
echo "5. Look for Auth0 redirect URL in network tab"
echo "6. Expected: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
echo "7. NOT: https://authorize/?client_id=..."

echo ""
echo "🔍 Debug script completed. Check results above."
