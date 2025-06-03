#!/bin/bash

# Quick Auth0 Test Script
# Tests if the correct Auth0 domain is deployed

echo "🧪 Quick Auth0 Domain Test"
echo "=========================="

echo "Testing frontend at: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

# Get JavaScript file
JS_FILE=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" | grep -o 'src="[^"]*\.js"' | head -1 | sed 's/src="//' | sed 's/"//') 

if [ -n "$JS_FILE" ]; then
  echo "✅ Found JS file: $JS_FILE"
  
  # Test for correct Auth0 domain
  AUTH0_FOUND=$(curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -o "dev-jwnud3v8ghqnyygr\.us\.auth0\.com" | head -1)
  
  if [ -n "$AUTH0_FOUND" ]; then
    echo "🎉 SUCCESS! Auth0 domain found: $AUTH0_FOUND"
    echo ""
    echo "✅ LOGIN SHOULD NOW WORK!"
    echo "Try clicking Login/Sign Up on the website"
  else
    echo "❌ Correct Auth0 domain NOT found"
    echo ""
    echo "Looking for any Auth0 references..."
    curl -s "https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io$JS_FILE" | grep -i "auth0" | head -3 || echo "No Auth0 references found"
  fi
else
  echo "❌ Could not find JavaScript file"
fi
