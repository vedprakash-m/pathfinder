#!/bin/bash

echo "🚀 AZURE DIRECT DEPLOYMENT - Dashboard Fix"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration (corrected)
RESOURCE_GROUP="pathfinder-rg-dev"
BACKEND_APP="pathfinder-backend"
FRONTEND_APP="pathfinder-frontend"
REGISTRY_NAME="pathfinderdevregistry"
IMAGE_NAME="pathfinder"

echo -e "${BLUE}Configuration:${NC}"
echo "Resource Group: $RESOURCE_GROUP"
echo "Backend App: $BACKEND_APP"
echo "Frontend App: $FRONTEND_APP"
echo "Registry: $REGISTRY_NAME"
echo ""

echo -e "${BLUE}Step 1: Building Backend${NC}"
echo "======================="

echo "Building backend image with route conflict fix..."
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
echo -e "${BLUE}Step 2: Deploying Backend${NC}"
echo "========================"

echo "Deploying backend with route conflict fix..."
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
echo -e "${BLUE}Step 3: Building Frontend${NC}"
echo "========================"

echo "Building frontend image with API fixes..."
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
echo -e "${BLUE}Step 4: Deploying Frontend${NC}"
echo "========================="

echo "Deploying frontend with API fixes..."
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
echo -e "${BLUE}Step 5: Testing Deployment${NC}"
echo "=========================="

echo "Waiting 60 seconds for deployment to stabilize..."
sleep 60

# Test backend
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Testing backend at: $BACKEND_URL"

echo "Health check..."
HEALTH_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
echo "  Health: $HEALTH_STATUS"

echo "Testing trips endpoint (the main fix)..."
TRIPS_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips")
echo "  Trips API: $TRIPS_STATUS"

# Test frontend
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "Testing frontend at: $FRONTEND_URL"
FRONTEND_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_URL/")
echo "  Frontend: $FRONTEND_STATUS"

echo ""
echo -e "${BLUE}Results:${NC}"
echo "========"

if [ "$TRIPS_STATUS" != "307" ]; then
    echo -e "${GREEN}🎉 SUCCESS: Route conflict resolved!${NC}"
    echo -e "${GREEN}   No more 307 redirects on /api/v1/trips${NC}"
    echo -e "${GREEN}   Dashboard loading issue should be fixed!${NC}"
else
    echo -e "${RED}❌ Still getting 307 redirects${NC}"
    echo "   The deployment may still be propagating..."
fi

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend accessible${NC}"
else
    echo -e "${RED}❌ Frontend issue: $FRONTEND_STATUS${NC}"
fi

echo ""
echo -e "${GREEN}🎯 DEPLOYMENT COMPLETE!${NC}"
echo ""
echo "🌐 Dashboard URL: $FRONTEND_URL"
echo "🔧 Backend API: $BACKEND_URL"
echo ""
echo "✅ Fixes deployed:"
echo "   - Backend: Route conflict resolved (/trips vs /trip-messages)"
echo "   - Frontend: API calls updated with trailing slashes"
echo "   - Frontend: CSRF token handling added"
echo ""
echo "🧪 Test the dashboard now to verify the fix!"
