#!/bin/bash
# Interactive Key Rotation Script
# Securely update API keys in Azure Key Vault with user prompts

set -e  # Exit on any error

echo "🔐 Interactive Key Rotation for Pathfinder"
echo "=========================================="
echo ""
echo "This script will help you securely rotate API keys that may have been exposed."
echo ""

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to read password without echoing
read_secret() {
    local prompt="$1"
    local secret
    echo -n "$prompt"
    read -s secret
    echo ""
    echo "$secret"
}

# Function to confirm action
confirm() {
    local prompt="$1"
    local response
    echo -n "${YELLOW}$prompt (y/N): ${NC}"
    read response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

echo "${BLUE}Which keys would you like to rotate?${NC}"
echo ""
echo "1. Auth0 Client Secret"
echo "2. Google Maps API Key" 
echo "3. OpenAI API Key"
echo "4. All keys"
echo ""
echo -n "Enter your choice (1-4): "
read choice

case $choice in
    1)
        rotate_auth0=true
        ;;
    2)
        rotate_google=true
        ;;
    3)
        rotate_openai=true
        ;;
    4)
        rotate_auth0=true
        rotate_google=true
        rotate_openai=true
        ;;
    *)
        echo "${RED}❌ Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo ""
echo "${YELLOW}⚠️  IMPORTANT SECURITY NOTES:${NC}"
echo "• Generate new keys from the respective service providers"
echo "• Never reuse old/exposed keys"
echo "• Keys will be stored securely in Azure Key Vault"
echo "• Container apps will be restarted to pick up new keys"
echo ""

if ! confirm "Do you want to continue?"; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "${BLUE}🔄 Starting key rotation process...${NC}"

# Check Azure CLI login
if ! az account show > /dev/null 2>&1; then
    echo "${RED}❌ Please login to Azure CLI first: az login${NC}"
    exit 1
fi

echo "✅ Azure CLI authenticated"

# Update Auth0 Client Secret
if [[ "$rotate_auth0" == "true" ]]; then
    echo ""
    echo "${BLUE}🔑 Auth0 Client Secret Rotation${NC}"
    echo "1. Go to https://manage.auth0.com/dashboard"
    echo "2. Navigate to Applications > Pathfinder > Settings"
    echo "3. Generate a new Client Secret"
    echo "4. Copy the new secret"
    echo ""
    
    NEW_AUTH0_SECRET=$(read_secret "Enter new Auth0 Client Secret: ")
    
    if [[ -z "$NEW_AUTH0_SECRET" ]]; then
        echo "${RED}❌ Auth0 secret cannot be empty${NC}"
        exit 1
    fi
    
    echo "🔄 Updating Auth0 secret in Key Vault..."
    az keyvault secret set \
      --vault-name pathfinder-kv-dev \
      --name auth0-client-secret \
      --value "$NEW_AUTH0_SECRET" \
      --output none
    
    echo "${GREEN}✅ Auth0 secret updated${NC}"
fi

# Update Google Maps API Key
if [[ "$rotate_google" == "true" ]]; then
    echo ""
    echo "${BLUE}🗺️  Google Maps API Key Rotation${NC}"
    echo "1. Go to https://console.cloud.google.com/apis/credentials"
    echo "2. Create a new API key or regenerate existing one"
    echo "3. Restrict the key to Maps JavaScript API and Places API"
    echo "4. Copy the new key"
    echo ""
    
    NEW_GOOGLE_KEY=$(read_secret "Enter new Google Maps API Key: ")
    
    if [[ -z "$NEW_GOOGLE_KEY" ]]; then
        echo "${RED}❌ Google Maps key cannot be empty${NC}"
        exit 1
    fi
    
    echo "🔄 Updating Google Maps key in Key Vault..."
    az keyvault secret set \
      --vault-name pathfinder-kv-dev \
      --name google-maps-api-key \
      --value "$NEW_GOOGLE_KEY" \
      --output none
    
    echo "${GREEN}✅ Google Maps key updated${NC}"
fi

# Update OpenAI API Key
if [[ "$rotate_openai" == "true" ]]; then
    echo ""
    echo "${BLUE}🤖 OpenAI API Key Rotation${NC}"
    echo "1. Go to https://platform.openai.com/api-keys"
    echo "2. Create a new secret key"
    echo "3. Copy the new key (starts with sk-)"
    echo ""
    
    NEW_OPENAI_KEY=$(read_secret "Enter new OpenAI API Key: ")
    
    if [[ -z "$NEW_OPENAI_KEY" ]]; then
        echo "${RED}❌ OpenAI key cannot be empty${NC}"
        exit 1
    fi
    
    echo "🔄 Updating OpenAI key in Key Vault..."
    az keyvault secret set \
      --vault-name pathfinder-kv-dev \
      --name openai-api-key \
      --value "$NEW_OPENAI_KEY" \
      --output none
    
    echo "${GREEN}✅ OpenAI key updated${NC}"
fi

echo ""
echo "${BLUE}🔄 Restarting container apps to pick up new secrets...${NC}"

# Restart backend
echo "Restarting backend..."
az containerapp revision restart \
  --name pathfinder-backend \
  --resource-group pathfinder-rg-dev \
  --output none

# Restart frontend  
echo "Restarting frontend..."
az containerapp revision restart \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --output none

echo ""
echo "${GREEN}🎉 Key rotation completed successfully!${NC}"
echo ""
echo "${BLUE}Next steps:${NC}"
echo "• Test your application to ensure it's working correctly"
echo "• Update any local development environment files"
echo "• Document the rotation in your security logs"
echo "• Monitor application logs for any authentication issues"
echo ""
echo "${YELLOW}Security reminder:${NC}"
echo "• Revoke/delete the old keys from their respective platforms"
echo "• Clear any local copies of the old keys"
echo "• Update team members about the key rotation"

# Clean up variables
unset NEW_AUTH0_SECRET
unset NEW_GOOGLE_KEY  
unset NEW_OPENAI_KEY
