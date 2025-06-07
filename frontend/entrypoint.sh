#!/bin/sh
# Simplified entrypoint for production deployment
# Auth0 configuration is now set at build time via environment variables

echo "🚀 Starting Pathfinder Frontend..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "API URL: ${VITE_API_URL:-https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io}"

# Start nginx
exec nginx -g "daemon off;"
