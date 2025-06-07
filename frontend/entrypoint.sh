#!/bin/sh
# Runtime environment variable replacement for Vite-built apps
# This script replaces placeholders in the built JS files with actual environment variables

# Set default values if not provided
VITE_AUTH0_DOMAIN="${VITE_AUTH0_DOMAIN:-dev-jwnud3v8ghqnyygr.us.auth0.com}"
VITE_AUTH0_CLIENT_ID="${VITE_AUTH0_CLIENT_ID:-KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn}"
VITE_AUTH0_AUDIENCE="${VITE_AUTH0_AUDIENCE:-https://pathfinder-api.com}"
VITE_API_URL="${VITE_API_URL:-https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io}"

echo "🔧 Configuring runtime environment variables..."
echo "Auth0 Domain: $VITE_AUTH0_DOMAIN"
echo "Auth0 Client ID: ${VITE_AUTH0_CLIENT_ID:0:8}..."
echo "Auth0 Audience: $VITE_AUTH0_AUDIENCE"
echo "API URL: $VITE_API_URL"

# Find and replace in all JS files in the build directory
find /usr/share/nginx/html -name "*.js" -type f -exec sed -i \
  -e "s|dev-pathfinder\.us\.auth0\.com|$VITE_AUTH0_DOMAIN|g" \
  -e "s|PLACEHOLDER_AUTH0_DOMAIN|$VITE_AUTH0_DOMAIN|g" \
  -e "s|import\.meta\.env\.VITE_AUTH0_DOMAIN|\"$VITE_AUTH0_DOMAIN\"|g" \
  -e "s|PLACEHOLDER_AUTH0_CLIENT_ID|$VITE_AUTH0_CLIENT_ID|g" \
  -e "s|import\.meta\.env\.VITE_AUTH0_CLIENT_ID|\"$VITE_AUTH0_CLIENT_ID\"|g" \
  -e "s|PLACEHOLDER_AUTH0_AUDIENCE|$VITE_AUTH0_AUDIENCE|g" \
  -e "s|import\.meta\.env\.VITE_AUTH0_AUDIENCE|\"$VITE_AUTH0_AUDIENCE\"|g" \
  -e "s|import\.meta\.env\.VITE_API_URL|\"$VITE_API_URL\"|g" \
  {} \;

echo "✅ Environment variables configured"

# Start nginx
exec nginx -g "daemon off;"
