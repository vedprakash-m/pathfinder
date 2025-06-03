#!/bin/bash
# Deploy Auth0 Fix for Frontend

echo "🚀 Deploying Auth0 Fix for Pathfinder Frontend"
echo "=============================================="

# Set variables
REGISTRY="pathfinderdevregistry"
RESOURCE_GROUP="pathfinder-rg-dev"
FRONTEND_APP="pathfinder-frontend"
IMAGE_TAG="auth0-fix-$(date +%Y%m%d-%H%M%S)"

echo "📦 Building frontend image with secure Key Vault configuration..."

# Get secrets from Key Vault for build arguments
VITE_AUTH0_DOMAIN=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-domain --query "value" --output tsv)
VITE_AUTH0_CLIENT_ID=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-client-id --query "value" --output tsv)
VITE_AUTH0_AUDIENCE=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-audience --query "value" --output tsv)

echo "Using Auth0 Domain: $VITE_AUTH0_DOMAIN"
echo "Using Auth0 Client ID: ${VITE_AUTH0_CLIENT_ID:0:8}..."

# Build the image using Azure Container Registry with Key Vault secrets
az acr build --registry $REGISTRY \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg VITE_AUTH0_DOMAIN="$VITE_AUTH0_DOMAIN" \
  --build-arg VITE_AUTH0_CLIENT_ID="$VITE_AUTH0_CLIENT_ID" \
  --build-arg VITE_AUTH0_AUDIENCE="$VITE_AUTH0_AUDIENCE" \
  --build-arg VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io \
  --build-arg ENVIRONMENT=production \
  ./frontend

if [ $? -eq 0 ]; then
    echo "✅ Image built successfully"
else
    echo "❌ Image build failed"
    exit 1
fi

echo "🔄 Updating container app with new image..."

# Update the container app with the new image
az containerapp update \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY.azurecr.io/pathfinder-frontend:$IMAGE_TAG \
  --revision-suffix auth0fix$(date +%s)

if [ $? -eq 0 ]; then
    echo "✅ Container app updated successfully"
    echo ""
    echo "🔍 Deployment Details:"
    echo "- Image: $REGISTRY.azurecr.io/pathfinder-frontend:$IMAGE_TAG"
    echo "- Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
    echo ""
    echo "⏳ Please wait 2-3 minutes for the new revision to be ready"
    echo "Then test the login functionality"
else
    echo "❌ Container app update failed"
    exit 1
fi

echo ""
echo "🧪 To verify the fix:"
echo "1. Open: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
echo "2. Click 'Login' and verify it redirects to Auth0 properly"
echo "3. Check that the URL shows 'dev-jwnud3v8ghqnyygr.us.auth0.com' instead of 'authorize'"
echo ""
echo "🔍 To check logs:"
echo "az containerapp logs show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP --tail 20"
