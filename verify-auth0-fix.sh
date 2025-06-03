#!/bin/bash

echo "🔍 COMPREHENSIVE AUTH0 VERIFICATION & CACHE BUSTING"
echo "==================================================="

FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

echo "1. Testing different cache-busting methods..."

echo ""
echo "📱 Testing with cache-busting parameter..."
CACHE_BUSTER="?v=$(date +%s)"
curl -s "$FRONTEND_URL$CACHE_BUSTER" | grep -o 'src="[^"]*\.js[^"]*"' | head -3

echo ""
echo "🔄 Testing with no-cache headers..."
curl -s -H "Cache-Control: no-cache" -H "Pragma: no-cache" "$FRONTEND_URL" | grep -o 'src="[^"]*\.js[^"]*"' | head -3

echo ""
echo "📊 Checking current container app revision..."
REVISION_INFO=$(az containerapp revision list --name pathfinder-frontend --resource-group pathfinder-rg-dev --query '[0].{name:name,active:properties.active,created:properties.createdTime}' -o table 2>/dev/null || echo "Could not fetch revision info")
echo "$REVISION_INFO"

echo ""
echo "🧪 Testing Auth0 configuration extraction..."

# Get frontend content
FRONTEND_CONTENT=$(curl -s "$FRONTEND_URL$CACHE_BUSTER")

# Extract all JavaScript files
JS_FILES=$(echo "$FRONTEND_CONTENT" | grep -o 'src="[^"]*\.js[^"]*"' | sed 's/src="//g' | sed 's/"//g')

echo "Found JavaScript files:"
for js_file in $JS_FILES; do
    echo "  - $js_file"
done

echo ""
echo "🔍 Detailed Auth0 analysis for each JS file..."

for js_file in $JS_FILES; do
    echo ""
    echo "Analyzing: $js_file"
    
    if [[ $js_file == http* ]]; then
        FULL_URL="$js_file"
    else
        FULL_URL="$FRONTEND_URL$js_file"
    fi
    
    echo "  URL: $FULL_URL"
    
    # Download with cache busting
    JS_CONTENT=$(curl -s -H "Cache-Control: no-cache" "$FULL_URL$CACHE_BUSTER")
    
    # Check file size to ensure we got content
    FILE_SIZE=${#JS_CONTENT}
    echo "  Size: $FILE_SIZE bytes"
    
    if [ $FILE_SIZE -lt 100 ]; then
        echo "  ❌ File too small or empty"
        continue
    fi
    
    # Look for correct Auth0 domain
    CORRECT_DOMAIN=$(echo "$JS_CONTENT" | grep -o "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | wc -l)
    echo "  ✅ Correct domain count: $CORRECT_DOMAIN"
    
    # Look for any other auth0 domains
    OTHER_DOMAINS=$(echo "$JS_CONTENT" | grep -o "[a-zA-Z0-9-]*\.auth0\.com" | grep -v "dev-jwnud3v8ghqnyygr.us.auth0.com" | sort | uniq)
    if [ -n "$OTHER_DOMAINS" ]; then
        echo "  ❌ Other Auth0 domains found:"
        echo "$OTHER_DOMAINS" | sed 's/^/    /'
    else
        echo "  ✅ No incorrect domains found"
    fi
    
    # Look for environment variable patterns
    ENV_VARS=$(echo "$JS_CONTENT" | grep -o "VITE_AUTH0_[A-Z_]*" | sort | uniq)
    if [ -n "$ENV_VARS" ]; then
        echo "  ⚠️  Environment variable patterns found:"
        echo "$ENV_VARS" | sed 's/^/    /'
    else
        echo "  ✅ No environment variable patterns found"
    fi
    
    # Look for debug logging
    DEBUG_LOG=$(echo "$JS_CONTENT" | grep -o "Auth0 Config Loaded" | head -1)
    if [ -n "$DEBUG_LOG" ]; then
        echo "  ✅ Debug logging found: $DEBUG_LOG"
    else
        echo "  ❌ Debug logging not found"
    fi
    
    # Look for empty/broken config patterns
    BROKEN_CONFIGS=$(echo "$JS_CONTENT" | grep -o "authorize/?[^\"]*" | head -3)
    if [ -n "$BROKEN_CONFIGS" ]; then
        echo "  ❌ Broken Auth0 configs found:"
        echo "$BROKEN_CONFIGS" | sed 's/^/    /'
    else
        echo "  ✅ No broken configs found"
    fi
done

echo ""
echo "🎯 MANUAL TESTING CHECKLIST:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Open: $FRONTEND_URL in INCOGNITO mode"
echo "2. Press CTRL+SHIFT+R (or CMD+SHIFT+R) for hard refresh"
echo "3. Open Developer Tools (F12)"
echo "4. Go to Console tab"
echo "5. Look for: '🔧 Auth0 Config Loaded:' message"
echo "6. Click 'Sign Up' or 'Log In'"
echo "7. Check Network tab for Auth0 redirect"
echo "8. Expected: https://dev-jwnud3v8ghqnyygr.us.auth0.com/authorize/..."
echo "9. NOT: https://authorize/?client_id=..."
echo ""
echo "If you still see the error, try:"
echo "- Clear all browser cache and cookies"
echo "- Try a different browser"
echo "- Check if there's a service worker caching old content"

echo ""
echo "🔍 Verification script completed."
