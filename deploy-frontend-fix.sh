#!/bin/bash

# Frontend Deployment Script - Dashboard Loading Fix
# This script deploys the frontend with URL consistency fixes and CSRF token handling

set -e

echo "🚀 Deploying Frontend with Dashboard Loading Fixes..."

# Build and push the frontend container
echo "📦 Building frontend container..."
az acr build --registry pathfinderdevregistry --image pathfinder-frontend:latest ./frontend

# Update the frontend container app
echo "🔄 Updating frontend container app..."
az containerapp update \
    --name pathfinder-frontend \
    --resource-group pathfinder-rg-dev \
    --image pathfinderdevregistry.azurecr.io/pathfinder-frontend:latest

# Force a new revision by scaling down and up
echo "🔄 Forcing new revision deployment..."
az containerapp update \
    --name pathfinder-frontend \
    --resource-group pathfinder-rg-dev \
    --min-replicas 0

sleep 10

az containerapp update \
    --name pathfinder-frontend \
    --resource-group pathfinder-rg-dev \
    --min-replicas 1

# Check the deployment
echo "✅ Checking deployment status..."
NEW_REVISION=$(az containerapp show \
    --name pathfinder-frontend \
    --resource-group pathfinder-rg-dev \
    --query "properties.latestRevisionName" -o tsv)

echo "🎉 Frontend deployed successfully!"
echo "📋 New revision: $NEW_REVISION"
echo "🌐 Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"

echo ""
echo "🔍 Testing frontend connectivity..."
curl -I https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/

echo ""
echo "✅ Frontend deployment complete!"
echo "📝 Changes included:"
echo "   - URL consistency fixes (trailing slashes)"
echo "   - CSRF token handling improvements"
echo "   - Matching backend route fixes"
