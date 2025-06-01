#!/bin/bash
# Secure Key Rotation Script
# Run this locally after rotating your API keys

set -e

echo "🔐 Secure API Key Update Script"
echo "==============================="
echo ""
echo "This script will securely update rotated API keys in Azure Key Vault."
echo "You'll be prompted to enter each key individually (input will be hidden)."
echo ""

# Function to read password securely
read_secret() {
    local prompt="$1"
    local secret
    echo -n "$prompt: "
    read -s secret
    echo ""
    echo "$secret"
}

echo "Please enter your rotated API keys:"
echo ""

# Read Auth0 Client Secret
echo "1. Auth0 Client Secret (after rotation in Auth0 dashboard)"
AUTH0_CLIENT_SECRET=$(read_secret "New Auth0 Client Secret")

# Read Google Maps API Key  
echo ""
echo "2. Google Maps API Key (after regeneration in Google Cloud Console)"
GOOGLE_MAPS_API_KEY=$(read_secret "New Google Maps API Key")

echo ""
echo "🔄 Updating Azure Key Vault..."

# Update Auth0 Client Secret
az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name auth0-client-secret \
  --value "$AUTH0_CLIENT_SECRET" \
  --output none

echo "✅ Updated Auth0 Client Secret"

# Update Google Maps API Key
az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name google-maps-api-key \
  --value "$GOOGLE_MAPS_API_KEY" \
  --output none

echo "✅ Updated Google Maps API Key"

echo ""
echo "🔄 Restarting container apps to pick up new keys..."

# Get current revisions
BACKEND_REVISION=$(az containerapp revision list --name pathfinder-backend --resource-group pathfinder-rg-dev --query "[0].name" --output tsv)
FRONTEND_REVISION=$(az containerapp revision list --name pathfinder-frontend --resource-group pathfinder-rg-dev --query "[0].name" --output tsv)

# Restart backend
az containerapp revision restart \
  --name pathfinder-backend \
  --resource-group pathfinder-rg-dev \
  --revision "$BACKEND_REVISION" \
  --output none

echo "✅ Restarted backend container"

# Restart frontend  
az containerapp revision restart \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --revision "$FRONTEND_REVISION" \
  --output none

echo "✅ Restarted frontend container"

echo ""
echo "🎉 Key rotation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Test the application: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "2. Verify Auth0 login functionality"
echo "3. Check Google Maps integration"
echo ""
echo "🔒 Security: The old exposed keys are now invalid and safe."

# Clean up variables
unset AUTH0_CLIENT_SECRET
unset GOOGLE_MAPS_API_KEY
