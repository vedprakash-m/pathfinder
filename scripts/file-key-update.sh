#!/bin/bash
# File-based key update (most secure method)

KEY_FILE="/tmp/rotated-keys.txt"

if [[ ! -f "$KEY_FILE" ]]; then
    echo "❌ Key file not found: $KEY_FILE"
    echo "Please create the file first with your rotated keys."
    exit 1
fi

echo "🔐 Reading keys from secure file..."

# Source the key file
source "$KEY_FILE"

# Verify keys are loaded
if [[ -z "$AUTH0_CLIENT_SECRET" || -z "$GOOGLE_MAPS_API_KEY" ]]; then
    echo "❌ Keys not found in file. Please check the format."
    exit 1
fi

echo "✅ Keys loaded from file"
echo "🔄 Updating Azure Key Vault..."

# Update secrets
az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name auth0-client-secret \
  --value "$AUTH0_CLIENT_SECRET" \
  --output none

az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name google-maps-api-key \
  --value "$GOOGLE_MAPS_API_KEY" \
  --output none

echo "✅ Keys updated successfully"

# Immediately delete the key file for security
rm "$KEY_FILE"
echo "🗑️  Temporary key file deleted for security"

# Clear variables
unset AUTH0_CLIENT_SECRET
unset GOOGLE_MAPS_API_KEY

echo ""
echo "🔄 Restarting containers..."

# Restart containers (same as other scripts)
BACKEND_REVISION=$(az containerapp revision list --name pathfinder-backend --resource-group pathfinder-rg-dev --query "[0].name" --output tsv)
FRONTEND_REVISION=$(az containerapp revision list --name pathfinder-frontend --resource-group pathfinder-rg-dev --query "[0].name" --output tsv)

az containerapp revision restart \
  --name pathfinder-backend \
  --resource-group pathfinder-rg-dev \
  --revision "$BACKEND_REVISION" \
  --output none

az containerapp revision restart \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --revision "$FRONTEND_REVISION" \
  --output none

echo "✅ Container restart completed"
echo "🎉 Secure key rotation finished!"
