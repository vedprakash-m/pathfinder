#!/bin/bash

# Simple Auth0 Fix - Direct deployment approach
set -e

echo "🚀 Simple Auth0 Fix Deployment"
echo "=============================="

# Get timestamp for unique tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Get Auth0 config from Key Vault
echo "Getting Auth0 configuration..."
AUTH0_DOMAIN=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-domain --query 'value' --output tsv)
AUTH0_CLIENT_ID=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-client-id --query 'value' --output tsv)
AUTH0_AUDIENCE=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-audience --query 'value' --output tsv)

echo "Auth0 Domain: $AUTH0_DOMAIN"
echo "Auth0 Client ID: ${AUTH0_CLIENT_ID:0:8}..."

# Build and deploy
echo "Building frontend..."
cd frontend

az acr build \
  --registry pathfinderregistry \
  --image pathfinder-frontend:fix-$TIMESTAMP \
  --build-arg VITE_AUTH0_DOMAIN="$AUTH0_DOMAIN" \
  --build-arg VITE_AUTH0_CLIENT_ID="$AUTH0_CLIENT_ID" \
  --build-arg VITE_AUTH0_AUDIENCE="$AUTH0_AUDIENCE" \
  --build-arg VITE_API_URL="https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
  .

echo "Updating container app..."
cd ..

az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --image pathfinderregistry.azurecr.io/pathfinder-frontend:fix-$TIMESTAMP

echo "✅ Deployment complete! Tag: fix-$TIMESTAMP"
echo "Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
