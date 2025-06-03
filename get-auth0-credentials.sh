#!/bin/bash
# Script to retrieve the current Auth0 Client ID from Azure Key Vault

echo "🔍 Retrieving Auth0 credentials from Azure Key Vault..."

# Check if Azure CLI is logged in
if ! az account show > /dev/null 2>&1; then
    echo "❌ Please login to Azure CLI first: az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"

# Get Auth0 Client ID from Key Vault
echo "Getting Auth0 Client ID..."
AUTH0_CLIENT_ID=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-client-id --query 'value' --output tsv)

if [ -z "$AUTH0_CLIENT_ID" ]; then
    echo "❌ Could not retrieve Auth0 Client ID from Key Vault"
    echo "Please check:"
    echo "1. Key Vault name: pathfinder-kv-dev"
    echo "2. Secret name: auth0-client-id" 
    echo "3. Your access permissions"
    exit 1
fi

echo "✅ Auth0 Client ID retrieved: ${AUTH0_CLIENT_ID:0:8}..."

# Get other Auth0 config for verification
echo "Getting other Auth0 configuration..."
AUTH0_DOMAIN=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-domain --query 'value' --output tsv)
AUTH0_AUDIENCE=$(az keyvault secret show --vault-name pathfinder-kv-dev --name auth0-audience --query 'value' --output tsv)

echo ""
echo "🔧 Current Auth0 Configuration:"
echo "Domain: $AUTH0_DOMAIN"
echo "Client ID: ${AUTH0_CLIENT_ID:0:8}..."
echo "Audience: $AUTH0_AUDIENCE"

echo ""
echo "📝 Update your frontend/.env.production file with:"
echo "VITE_AUTH0_CLIENT_ID=$AUTH0_CLIENT_ID"
