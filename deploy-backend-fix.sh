#!/bin/bash

echo "🔧 Deploying Backend Route Fix"
echo "=============================="

RESOURCE_GROUP="pathfinder-rg-dev"
BACKEND_APP="pathfinder-backend"
REGISTRY="pathfinderdevregistry.azurecr.io"
IMAGE="pathfinder-backend:latest"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Building and pushing backend container...${NC}"
az acr build --registry pathfinderdevregistry --image pathfinder-backend:latest ./backend

echo -e "${BLUE}Step 2: Updating container app...${NC}"
az containerapp update \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE

echo -e "${BLUE}Step 3: Testing the fix...${NC}"
echo "Waiting 30 seconds for deployment..."
sleep 30

# Test the API endpoint
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

echo "Testing trips endpoint..."
curl -I "$BACKEND_URL/api/v1/trips"

echo ""
echo "Testing trips endpoint with trailing slash..."
curl -I "$BACKEND_URL/api/v1/trips/"

echo ""
echo -e "${GREEN}Backend deployment complete!${NC}"
echo "Please test the dashboard in the browser."
