#!/bin/bash

# PRODUCTION SECURITY UPDATE SCRIPT
# Run this AFTER rotating Auth0 credentials

echo "🔄 Updating Azure Key Vault with new Auth0 credentials..."

# Update Key Vault (replace with your actual values)
echo "az keyvault secret set --vault-name pathfinder-kv --name AUTH0-CLIENT-SECRET --value 'NEW_CLIENT_SECRET_HERE'"
echo "az keyvault secret set --vault-name pathfinder-kv --name AUTH0-CLIENT-ID --value 'NEW_CLIENT_ID_HERE'"

echo "🚀 Restarting Container Apps to pick up new secrets..."
echo "az containerapp revision copy --name pathfinder-backend --resource-group pathfinder-rg"
echo "az containerapp revision copy --name pathfinder-frontend --resource-group pathfinder-rg"

echo "✅ Production security update commands ready"
echo "Remember to replace placeholder values with actual new credentials"
