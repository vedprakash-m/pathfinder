#!/bin/bash

# Auth0 Login Verification Script
# Tests current authentication functionality

echo "🔍 Auth0 Login Verification"
echo "=========================="
echo ""

# Application URLs
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

echo "📍 Testing application endpoints..."

# Test frontend accessibility
echo "1. Frontend accessibility:"
if curl -s --head "$FRONTEND_URL" | grep -q "200\|301\|302"; then
    echo "   ✅ Frontend is accessible at $FRONTEND_URL"
else
    echo "   ❌ Frontend is not accessible"
fi

# Test backend health
echo "2. Backend health:"
if curl -s "$BACKEND_URL/health" | grep -q "ok\|healthy\|success"; then
    echo "   ✅ Backend is healthy at $BACKEND_URL/health"
else
    echo "   ⚠️  Backend health check inconclusive"
fi

echo ""
echo "🔧 Current Auth0 Configuration Status:"
echo "   Domain: dev-jwnud3v8ghqnyygr.us.auth0.com ✅"
echo "   Client ID: PLACEHOLDER_NEEDS_NEW_AUTH0_CLIENT_ID ❌"
echo "   Audience: https://pathfinder-api.com ✅"
echo ""

echo "🚨 Known Issue:"
echo "   The frontend container was built with a placeholder Auth0 Client ID"
echo "   instead of the actual rotated credentials from Azure Key Vault."
echo ""

echo "🛠️  Resolution Required:"
echo "   1. Access Azure Key Vault to get actual auth0-client-id value"
echo "   2. Update frontend/.env.production with correct Client ID"
echo "   3. Rebuild and deploy frontend container"
echo "   4. Test authentication flow"
echo ""

echo "📖 For manual steps, see: MANUAL_AUTH0_FIX_COMPLETION.md"
echo "🤖 For automated fix, run: ./complete-auth0-fix-final.sh (when Azure CLI works)"
echo ""

echo "🌐 Test authentication manually at:"
echo "   $FRONTEND_URL"
echo "   (Expected: 'Unknown host' error during login attempt)"
