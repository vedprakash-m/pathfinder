#!/bin/bash

# Exit on error
set -e

# Define colors for output
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RESET='\033[0m'

# Default values
ENV="dev"
LOCATION="eastus"
APP_NAME="pathfinder"
RG_NAME="pathfinder-rg"
SQL_ADMIN_USERNAME="pathfinderadmin"
SQL_ADMIN_PASSWORD=""
OPENAI_API_KEY=""
SKIP_CONFIRM=0

# Print usage
function print_usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -e, --environment ENV       Deployment environment (dev, test, prod)"
  echo "  -l, --location LOCATION     Azure region location"
  echo "  -n, --name NAME             Application name"
  echo "  -g, --resource-group NAME   Resource group name"
  echo "  -u, --sql-admin USERNAME    SQL Server admin username"
  echo "  -p, --sql-password PASSWORD SQL Server admin password"
  echo "  -o, --openai-key KEY        OpenAI API key"
  echo "  -y, --yes                   Skip confirmation prompt"
  echo "  -h, --help                  Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -e|--environment)
      ENV="$2"
      shift
      shift
      ;;
    -l|--location)
      LOCATION="$2"
      shift
      shift
      ;;
    -n|--name)
      APP_NAME="$2"
      shift
      shift
      ;;
    -g|--resource-group)
      RG_NAME="$2"
      shift
      shift
      ;;
    -u|--sql-admin)
      SQL_ADMIN_USERNAME="$2"
      shift
      shift
      ;;
    -p|--sql-password)
      SQL_ADMIN_PASSWORD="$2"
      shift
      shift
      ;;
    -o|--openai-key)
      OPENAI_API_KEY="$2"
      shift
      shift
      ;;
    -y|--yes)
      SKIP_CONFIRM=1
      shift
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      echo -e "${COLOR_RED}Unknown option: $key${COLOR_RESET}"
      print_usage
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$SQL_ADMIN_PASSWORD" ]; then
  echo -e "${COLOR_YELLOW}SQL admin password is required.${COLOR_RESET}"
  read -sp "Enter SQL admin password: " SQL_ADMIN_PASSWORD
  echo ""
fi

# Check if password meets complexity requirements
if [[ ${#SQL_ADMIN_PASSWORD} -lt 12 ]]; then
  echo -e "${COLOR_RED}SQL password must be at least 12 characters long.${COLOR_RESET}"
  exit 1
fi

# Generate random OpenAI API key if not provided (for testing only)
if [ -z "$OPENAI_API_KEY" ]; then
  echo -e "${COLOR_YELLOW}OpenAI API key not provided. Using dummy key for deployment.${COLOR_RESET}"
  OPENAI_API_KEY="sk-dummy-key-for-testing-purposes-only"
fi

# Print deployment information
echo -e "${COLOR_GREEN}Pathfinder Deployment${COLOR_RESET}"
echo "===================="
echo "Environment: $ENV"
echo "Location: $LOCATION"
echo "Application Name: $APP_NAME"
echo "Resource Group: $RG_NAME"
echo "SQL Admin Username: $SQL_ADMIN_USERNAME"
echo "OpenAI API Key: [HIDDEN]"
echo ""

# Confirm deployment
if [ $SKIP_CONFIRM -eq 0 ]; then
  read -p "Continue with deployment? (y/N): " confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${COLOR_YELLOW}Deployment canceled.${COLOR_RESET}"
    exit 0
  fi
fi

# Check Azure CLI login status
az account show &> /dev/null
if [ $? -ne 0 ]; then
  echo -e "${COLOR_YELLOW}Please login to Azure CLI${COLOR_RESET}"
  az login
fi

# Create resource group if it doesn't exist
echo -e "${COLOR_GREEN}Creating resource group if it doesn't exist...${COLOR_RESET}"
az group create --name $RG_NAME --location $LOCATION --output none

# Deploy Bicep template
echo -e "${COLOR_GREEN}Deploying infrastructure...${COLOR_RESET}"
az deployment group create \
  --resource-group $RG_NAME \
  --template-file ../bicep/main.bicep \
  --parameters \
    appName=$APP_NAME \
    environment=$ENV \
    location=$LOCATION \
    sqlAdminLogin=$SQL_ADMIN_USERNAME \
    sqlAdminPassword=$SQL_ADMIN_PASSWORD \
    openAIApiKey=$OPENAI_API_KEY

# Get deployment outputs
echo -e "${COLOR_GREEN}Getting deployment outputs...${COLOR_RESET}"
BACKEND_URL=$(az deployment group show \
  --resource-group $RG_NAME \
  --name main \
  --query "properties.outputs.backendAppUrl.value" \
  --output tsv)

FRONTEND_URL=$(az deployment group show \
  --resource-group $RG_NAME \
  --name main \
  --query "properties.outputs.frontendAppUrl.value" \
  --output tsv)

KEY_VAULT_NAME=$(az deployment group show \
  --resource-group $RG_NAME \
  --name main \
  --query "properties.outputs.keyVaultName.value" \
  --output tsv)

# Store key secrets in Key Vault
echo -e "${COLOR_GREEN}Storing secrets in Key Vault...${COLOR_RESET}"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "SqlAdminUsername" --value "$SQL_ADMIN_USERNAME" --output none
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "SqlAdminPassword" --value "$SQL_ADMIN_PASSWORD" --output none
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "OpenAiApiKey" --value "$OPENAI_API_KEY" --output none

# Print summary
echo -e "${COLOR_GREEN}Deployment Complete!${COLOR_RESET}"
echo "===================="
echo "Backend URL: https://$BACKEND_URL"
echo "Frontend URL: https://$FRONTEND_URL"
echo "Key Vault: $KEY_VAULT_NAME"
echo ""
echo -e "${COLOR_YELLOW}Note: It may take several minutes for all services to start.${COLOR_RESET}"