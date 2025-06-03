#!/bin/bash

echo "🚀 Simple Auth0 Fix Deployment"
echo "==============================="

# Configuration
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="auth0-fix-$TIMESTAMP"

echo "Image tag: $IMAGE_TAG"
echo "Starting deployment..."

# Step 1: Build frontend using Azure Container Registry
echo "Building frontend with hardcoded Auth0 config..."
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  --no-cache \
  --file frontend/Dockerfile \
  frontend/

# Step 2: Update container app with new image
echo "Updating container app..."
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG

echo "✅ Deployment completed with image: $IMAGE_TAG"
echo "🌐 Test at: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
