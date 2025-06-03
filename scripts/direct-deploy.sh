#!/bin/bash

echo "🚀 DIRECT DEPLOYMENT - Dashboard Fix"
echo "===================================="
echo ""
echo "Bypassing CI/CD to deploy fixes immediately..."
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
REGISTRY="ghcr.io"
IMAGE_NAME="vedprakash-m/pathfinder"

echo -e "${BLUE}Step 1: Building and Deploying Backend${NC}"
echo "======================================"

# Build backend Docker image
echo "Building backend Docker image..."
cd backend
docker build -t $REGISTRY/$IMAGE_NAME-backend:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend image built successfully${NC}"
else
    echo -e "${RED}❌ Backend image build failed${NC}"
    exit 1
fi

# Push backend image
echo "Pushing backend image to registry..."
docker push $REGISTRY/$IMAGE_NAME-backend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend image pushed successfully${NC}"
else
    echo -e "${RED}❌ Backend image push failed${NC}"
    exit 1
fi

# Deploy backend to Azure Container Apps
echo "Deploying backend to Azure Container Apps..."
az containerapp update \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME-backend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend deployed successfully${NC}"
else
    echo -e "${RED}❌ Backend deployment failed${NC}"
    exit 1
fi

cd ..

echo ""
echo -e "${BLUE}Step 2: Building and Deploying Frontend${NC}"
echo "======================================="

# Build frontend Docker image
echo "Building frontend Docker image..."
cd frontend
docker build -t $REGISTRY/$IMAGE_NAME-frontend:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend image built successfully${NC}"
else
    echo -e "${RED}❌ Frontend image build failed${NC}"
    exit 1
fi

# Push frontend image
echo "Pushing frontend image to registry..."
docker push $REGISTRY/$IMAGE_NAME-frontend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend image pushed successfully${NC}"
else
    echo -e "${RED}❌ Frontend image push failed${NC}"
    exit 1
fi

# Deploy frontend to Azure Container Apps
echo "Deploying frontend to Azure Container Apps..."
az containerapp update \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY/$IMAGE_NAME-frontend:latest

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend deployed successfully${NC}"
else
    echo -e "${RED}❌ Frontend deployment failed${NC}"
    exit 1
fi

cd ..

echo ""
echo -e "${BLUE}Step 3: Verification${NC}"
echo "==================="

# Wait for deployment to stabilize
echo "Waiting 30 seconds for deployment to stabilize..."
sleep 30

# Test backend routes
echo "Testing backend routes..."
BACKEND_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"

HEALTH_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/health")
echo "Health check: $HEALTH_STATUS"

TRIPS_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$BACKEND_URL/api/v1/trips")
echo "Trips API: $TRIPS_STATUS"

if [ "$TRIPS_STATUS" != "307" ]; then
    echo -e "${GREEN}🎉 SUCCESS: Route conflict resolved! No more 307 redirects${NC}"
else
    echo -e "${RED}❌ Still getting 307 redirects${NC}"
fi

# Test frontend
echo "Testing frontend..."
FRONTEND_URL="https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
FRONTEND_STATUS=$(curl -s -w "%{http_code}" -o /dev/null "$FRONTEND_URL/")
echo "Frontend: $FRONTEND_STATUS"

echo ""
echo -e "${GREEN}🎯 DIRECT DEPLOYMENT COMPLETE!${NC}"
echo ""
echo "Dashboard should now be working at:"
echo "$FRONTEND_URL"
echo ""
echo "Next steps:"
echo "1. Test the dashboard manually"
echo "2. Fix CI/CD pipeline for future deployments"
