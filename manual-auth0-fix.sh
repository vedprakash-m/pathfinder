#!/bin/bash

# Manual Auth0 Fix Script - Execute after getting Client ID from Key Vault
# Usage: ./manual-auth0-fix.sh "YOUR_ACTUAL_32_CHAR_CLIENT_ID"

if [ $# -eq 0 ]; then
    echo "❌ ERROR: Auth0 Client ID required"
    echo "Usage: $0 \"YOUR_ACTUAL_32_CHAR_CLIENT_ID\""
    echo ""
    echo "Steps to get Client ID:"
    echo "1. Go to Azure Portal → Key Vaults → pathfinder-kv-dev"
    echo "2. Secrets → auth0-client-id → Show Secret Value"
    echo "3. Copy the 32-character value"
    echo "4. Run: $0 \"PASTE_CLIENT_ID_HERE\""
    exit 1
fi

CLIENT_ID="$1"

# Validate Client ID format
if [[ ! "$CLIENT_ID" =~ ^[A-Za-z0-9]{32}$ ]]; then
    echo "❌ ERROR: Invalid Client ID format"
    echo "Expected: 32 alphanumeric characters"
    echo "Received: $CLIENT_ID (length: ${#CLIENT_ID})"
    exit 1
fi

echo "🔧 Applying Auth0 Fix with Client ID: ${CLIENT_ID:0:8}..."
echo ""

# Backup original files
echo "📋 Creating backups..."
cp frontend/.env.production frontend/.env.production.backup
cp frontend/src/auth0-config.ts frontend/src/auth0-config.ts.backup

# Update .env.production
echo "🔧 Updating frontend/.env.production..."
sed -i.bak "s/VITE_AUTH0_CLIENT_ID=PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID/VITE_AUTH0_CLIENT_ID=$CLIENT_ID/" frontend/.env.production

# Update auth0-config.ts fallback
echo "🔧 Updating frontend/src/auth0-config.ts..."
sed -i.bak "s/PLACEHOLDER_CLIENT_ID_NEEDS_ROTATION/$CLIENT_ID/" frontend/src/auth0-config.ts

# Verify changes
echo ""
echo "✅ Configuration Updated!"
echo "================================"
echo "📋 Updated files:"
echo "- frontend/.env.production"
echo "- frontend/src/auth0-config.ts"
echo ""
echo "🔍 Current configuration:"
echo "-------------------------"
grep "VITE_AUTH0_CLIENT_ID" frontend/.env.production
grep "clientId:" frontend/src/auth0-config.ts
echo ""

# Check if Docker is available for building
if command -v docker &> /dev/null; then
    echo "🐳 Docker available - ready to build container"
    echo ""
    echo "Next steps:"
    echo "1. Build: docker build -t pathfinder-frontend-fixed frontend/"
    echo "2. Tag: docker tag pathfinder-frontend-fixed pathfinderacr.azurecr.io/pathfinder-frontend:latest"
    echo "3. Push: docker push pathfinderacr.azurecr.io/pathfinder-frontend:latest"
    echo "4. Or run: ./complete-auth0-fix-final.sh"
else
    echo "❌ Docker not available"
    echo "Manual container update required via Azure Portal"
fi

echo ""
echo "🎯 Test URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "Expected: Login button should work without errors"
