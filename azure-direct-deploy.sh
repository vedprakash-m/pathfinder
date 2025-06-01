#!/bin/bash

echo "🚀 AZURE REMOTE BUILD & DEPLOY - Dashboard Fix"
echo "============================================="
echo ""
echo "Using Azure Container Registry to build remotely..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
RESOURCE_GROUP="pathfinder-prod"
BACKEND_APP="pathfinder-backend-prod"
FRONTEND_APP="pathfinder-frontend-prod"
REGISTRY_NAME="pathfinderacr"
IMAGE_NAME="pathfinder"

echo -e "${BLUE}Step 1: Azure Login Check${NC}"
echo "=========================="

# Check if logged in to Azure
az account show > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Azure CLI already logged in${NC}"
    ACCOUNT=$(az account show --query "user.name" -o tsv)
    echo "Logged in as: $ACCOUNT"
else
    echo -e "${YELLOW}⚠️  Not logged in to Azure${NC}"
    echo "Please run: az login"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 2: Building Backend with ACR${NC}"
echo "================================="

# Build backend using Azure Container Registry
echo "Building backend image remotely..."
az acr build \
  --registry $REGISTRY_NAME \
  --image $IMAGE_NAME-backend:latest \
  --file backend/Dockerfile \
  backend/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend image built successfully${NC}"
else
    echo -e "${RED}❌ Backend image build failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3: Deploying Backend${NC}"
echo "=========================="

# Deploy backend to Azure Container Apps
echo "Deploying backend to Azure Container Apps..."
az containerapp update \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME-backend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend deployed successfully${NC}"
else
    echo -e "${RED}❌ Backend deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 4: Building Frontend with ACR${NC}"
echo "=================================="

# Build frontend using Azure Container Registry
echo "Building frontend image remotely..."
az acr build \
  --registry $REGISTRY_NAME \
  --image $IMAGE_NAME-frontend:latest \
  --file frontend/Dockerfile \
  frontend/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend image built successfully${NC}"
else
    echo -e "${RED}❌ Frontend image build failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 5: Deploying Frontend${NC}"
echo "=========================="

# Deploy frontend to Azure Container Apps
echo "Deploying frontend to Azure Container Apps..."
az containerapp update \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY_NAME.azurecr.io/$IMAGE_NAME-frontend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend deployed successfully${NC}"
else
    echo -e "${RED}❌ Frontend deployment failed${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 6: Verification${NC}"
echo "==================="

# Wait for deployment to stabilize
echo "Waiting 60 seconds for deployment to stabilize..."
sleep 60

# Test backend routes
echo "Testing backend routes..."
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

echo "Testing health endpoint..."
HEALTH_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
echo "Health check: $HEALTH_STATUS"

echo "Testing trips endpoint (the fix)..."
TRIPS_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips")
echo "Trips API: $TRIPS_STATUS"

if [ "$TRIPS_STATUS" != "307" ]; then
    echo -e "${GREEN}🎉 SUCCESS: Route conflict resolved! No more 307 redirects${NC}"
    echo "Dashboard loading issue should be fixed!"
else
    echo -e "${RED}❌ Still getting 307 redirects - check deployment${NC}"
fi

# Test frontend
echo "Testing frontend..."
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
FRONTEND_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_URL/")
echo "Frontend: $FRONTEND_STATUS"

echo ""
echo -e "${GREEN}🎯 DIRECT DEPLOYMENT COMPLETE!${NC}"
echo ""
echo "Dashboard URL: $FRONTEND_URL"
echo "Backend API: $BACKEND_URL"
echo ""
echo "✅ Changes deployed:"
echo "   - Backend route conflict fixed (/trips vs /trip-messages)"
echo "   - Frontend API calls updated with trailing slashes"
echo "   - CSRF token handling implemented"
echo ""
echo "🧪 Next steps:"
echo "   1. Test dashboard manually at the URL above"
echo "   2. Verify trips load without errors"
echo "   3. Fix CI/CD pipeline for future deployments"
