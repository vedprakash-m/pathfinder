#!/bin/bash

# Script to deploy the fixed frontend with the correct Auth0 domain
# Run this script on a machine with Docker installed and access to Azure

# Step 1: Build the frontend image
echo "Building frontend image with correct Auth0 domain..."
docker build -t pathfinder-frontend:fixed -f frontend/Dockerfile ./frontend

# Step 2: Tag and push to Azure Container Registry
echo "Tagging and pushing image to Azure Container Registry..."
ACR_NAME="pathfinderacr"
IMAGE_TAG="pathfinder-frontend:fixed"
ACR_IMAGE="$ACR_NAME.azurecr.io/pathfinder-frontend:latest"

az acr login --name $ACR_NAME
docker tag $IMAGE_TAG $ACR_IMAGE
docker push $ACR_IMAGE

# Step 3: Update the frontend container app to use the new image
echo "Updating container app to use the new image..."
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg \
  --image $ACR_IMAGE

echo "Deployment completed successfully!"
