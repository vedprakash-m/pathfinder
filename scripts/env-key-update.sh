#!/bin/bash
# Alternative: Environment Variable Method
# Set your keys as environment variables and run this script

echo "🔐 Environment Variable Key Update"
echo "================================="
echo ""

# Check if environment variables are set
if [[ -z "$NEW_AUTH0_CLIENT_SECRET" || -z "$NEW_GOOGLE_MAPS_API_KEY" ]]; then
    echo "❌ Please set environment variables first:"
    echo ""
    echo "export NEW_AUTH0_CLIENT_SECRET='your-new-secret'"
    echo "export NEW_GOOGLE_MAPS_API_KEY='your-new-key'"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Environment variables detected"
echo "🔄 Updating Azure Key Vault..."

# Update secrets
az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name auth0-client-secret \
  --value "$NEW_AUTH0_CLIENT_SECRET" \
  --output none

az keyvault secret set \
  --vault-name pathfinder-kv-dev \
  --name google-maps-api-key \
  --value "$NEW_GOOGLE_MAPS_API_KEY" \
  --output none

echo "✅ Keys updated successfully"

# Clean up environment variables
unset NEW_AUTH0_CLIENT_SECRET
unset NEW_GOOGLE_MAPS_API_KEY

echo "🔒 Environment variables cleared for security"
