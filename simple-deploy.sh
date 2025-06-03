#!/bin/bash

# Simple Auth0 deployment script
echo "🚀 Simple Auth0 Deployment"

# Get timestamp for unique tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="auth0-simple-$TIMESTAMP"

echo "Building with tag: $IMAGE_TAG"

cd frontend

# Build the image
az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:$IMAGE_TAG \
  --no-cache \
  .

# Update the container app
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:$IMAGE_TAG

echo "✅ Deployment completed with image: $IMAGE_TAG"
