#!/bin/bash

# Deploy Frontend Fixes Script
# This script helps deploy the frontend fixes for the dashboard loading issue

set -e

echo "🚀 Pathfinder Frontend Deployment Script"
echo "========================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "package.json" ]]; then
    echo "❌ Error: Not in the Pathfinder root directory"
    echo "Please run this script from the project root where package.json exists"
    exit 1
fi

echo "✅ Verified we're in the correct directory"
echo ""

# Show the fixes that have been applied
echo "📋 Applied Fixes Summary:"
echo "------------------------"
echo "1. ✅ Backend route conflict fix (deployed)"
echo "2. ✅ Frontend trailing slash URLs"
echo "3. ✅ CSRF token handling"
echo ""

# Display the specific files that were modified
echo "📄 Modified Files:"
echo "- frontend/src/services/tripService.ts"
echo "- frontend/src/services/api.ts"
echo ""

# Check if the files have the expected changes
echo "🔍 Verifying Fixes..."

# Check tripService.ts for trailing slash
if grep -q "'/trips/'" frontend/src/services/tripService.ts; then
    echo "✅ tripService.ts - trailing slash fix verified"
else
    echo "❌ tripService.ts - trailing slash fix not found"
    exit 1
fi

# Check api.ts for CSRF handling
if grep -q "X-CSRF-Token" frontend/src/services/api.ts; then
    echo "✅ api.ts - CSRF token handling verified"
else
    echo "❌ api.ts - CSRF token handling not found"
    exit 1
fi

echo ""
echo "🎯 Next Steps for Deployment:"
echo "-----------------------------"
echo ""
echo "Since Docker is not available locally, you have these options:"
echo ""
echo "Option 1: Deploy via Azure Container Registry"
echo "  1. Commit these changes to git"
echo "  2. Push to your repository"
echo "  3. Trigger the CI/CD pipeline to rebuild the frontend"
echo ""
echo "Option 2: Manual Azure Container Apps Update"
echo "  1. Use Azure CLI to update the container app with new environment variables"
echo "  2. Force restart the frontend container"
echo ""
echo "Option 3: Local Testing (if you have a local dev environment)"
echo "  1. Run 'npm run dev' or 'pnpm dev' in the frontend directory"
echo "  2. Test the fixes locally against the production backend"
echo ""

# Show the current API configuration
echo "🔧 Current API Configuration:"
echo "-----------------------------"
if [[ -f "frontend/.env.production" ]]; then
    echo "Environment file found:"
    cat frontend/.env.production
else
    echo "No production environment file found."
    echo "Expected configuration:"
    echo "VITE_AUTH0_DOMAIN=dev-jwnud3v8ghqnyygr.us.auth0.com"
    echo "VITE_AUTH0_CLIENT_ID=YOUR_AUTH0_CLIENT_ID"
    echo "VITE_AUTH0_AUDIENCE=https://pathfinder-api.com"
    echo "VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/api/v1"
    echo "ENVIRONMENT=production"
fi

echo ""
echo "🏁 Deployment Script Complete!"
echo ""
echo "💡 Quick Test Command:"
echo "Once deployed, you can test the fix with:"
echo "curl -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "  'https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/api/v1/trips/'"
echo ""
echo "The response should be 200 OK with trip data (not 307 redirect)"
