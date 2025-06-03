#!/bin/bash
# Secure Auth0 Fix Deployment - No secrets in build args

echo "🚀 Deploying Auth0 Fix for Pathfinder Frontend (Secure Method)"
echo "=============================================================="

# Set variables
REGISTRY="pathfinderdevregistry"
RESOURCE_GROUP="pathfinder-rg-dev"
FRONTEND_APP="pathfinder-frontend"
IMAGE_TAG="auth0-secure-$(date +%Y%m%d-%H%M%S)"

echo "📦 Building frontend image with placeholder values..."
echo "ℹ️  Secrets will be injected at runtime from Key Vault"

# Build the image using Azure Container Registry with placeholder values
# The entrypoint script will replace these with actual values from Key Vault at runtime
az acr build --registry $REGISTRY \
  --image pathfinder-frontend:$IMAGE_TAG \
  --build-arg VITE_AUTH0_DOMAIN=PLACEHOLDER_AUTH0_DOMAIN \
  --build-arg VITE_AUTH0_CLIENT_ID=PLACEHOLDER_AUTH0_CLIENT_ID \
  --build-arg VITE_AUTH0_AUDIENCE=PLACEHOLDER_AUTH0_AUDIENCE \
  --build-arg VITE_API_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io \
  --build-arg ENVIRONMENT=production \
  ./frontend

if [ $? -eq 0 ]; then
    echo "✅ Image built successfully with placeholders"
else
    echo "❌ Image build failed"
    exit 1
fi

echo "🔄 Updating container app with new secure image..."

# Update the container app with the new image
# The environment variables are already configured to pull from Key Vault
az containerapp update \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --image $REGISTRY.azurecr.io/pathfinder-frontend:$IMAGE_TAG \
  --revision-suffix secure$(date +%s)

if [ $? -eq 0 ]; then
    echo "✅ Container app updated successfully"
    echo ""
    echo "🔍 Deployment Details:"
    echo "- Image: $REGISTRY.azurecr.io/pathfinder-frontend:$IMAGE_TAG"
    echo "- Frontend URL: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
    echo "- Secrets: Pulled from Key Vault at runtime (secure)"
    echo ""
    echo "⏳ Please wait 2-3 minutes for the new revision to be ready"
    echo "The entrypoint script will replace placeholders with Key Vault values"
else
    echo "❌ Container app update failed"
    exit 1
fi

echo ""
echo "🔐 Security Benefits:"
echo "- No secrets exposed in build logs"
echo "- No secrets in Docker image layers"
echo "- Runtime secret injection from Key Vault"
echo ""
echo "🧪 To verify the fix:"
echo "1. Check logs: az containerapp logs show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP --tail 20"
echo "2. Look for: '🔧 Configuring runtime environment variables...'"
echo "3. Test login: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io"
