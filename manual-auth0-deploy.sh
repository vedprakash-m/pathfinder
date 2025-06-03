#!/bin/bash

# Manual Auth0 Deployment - Step by Step
echo "=== MANUAL AUTH0 DEPLOYMENT ==="

# Set unique tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="manual-auth0-$TIMESTAMP"

echo "Image tag: $IMAGE_TAG"
echo "Starting deployment..."

# Step 1: Navigate to frontend
cd /Users/vedprakashmishra/pathfinder/frontend

# Step 2: Build image
echo "Building image with ACR..."
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  .

# Step 3: Update container app
echo "Updating container app..."
cd ..
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG

echo "Deployment completed with tag: $IMAGE_TAG"
