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
RG_NAME="pathfinder-rg"
APP_NAME="pathfinder"
OUTPUT_FILE="../.env"

# Print usage
function print_usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -e, --environment ENV       Deployment environment (dev, test, prod)"
  echo "  -g, --resource-group NAME   Resource group name"
  echo "  -n, --name NAME             Application name"
  echo "  -o, --output FILE           Output file (.env format)"
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
    -g|--resource-group)
      RG_NAME="$2"
      shift
      shift
      ;;
    -n|--name)
      APP_NAME="$2"
      shift
      shift
      ;;
    -o|--output)
      OUTPUT_FILE="$2"
      shift
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

# Check Azure CLI login status
az account show &> /dev/null
if [ $? -ne 0 ]; then
  echo -e "${COLOR_YELLOW}Please login to Azure CLI${COLOR_RESET}"
  az login
fi

echo -e "${COLOR_GREEN}Retrieving environment variables from Azure...${COLOR_RESET}"

# Get Key Vault name from deployment
KEY_VAULT_NAME=$(az deployment group show \
  --resource-group $RG_NAME \
  --name main \
  --query "properties.outputs.keyVaultName.value" \
  --output tsv 2>/dev/null)

if [ -z "$KEY_VAULT_NAME" ]; then
  echo -e "${COLOR_RED}Could not find Key Vault name in deployment. Using default naming.${COLOR_RESET}"
  KEY_VAULT_NAME="${APP_NAME}-kv-${ENV}"
fi

# Get SQL connection string components
SQL_SERVER="${APP_NAME}-sql-${ENV}.database.windows.net"
SQL_DB="${APP_NAME}-db-${ENV}"

SQL_ADMIN_USERNAME=$(az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name "SqlAdminUsername" \
  --query "value" \
  --output tsv 2>/dev/null)

SQL_ADMIN_PASSWORD=$(az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name "SqlAdminPassword" \
  --query "value" \
  --output tsv 2>/dev/null)

# Get OpenAI API key
OPENAI_API_KEY=$(az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name "OpenAiApiKey" \
  --query "value" \
  --output tsv 2>/dev/null)

# Get Cosmos DB connection string
COSMOS_ACCOUNT="${APP_NAME}-cosmos-${ENV}"
COSMOS_CONNECTION_STRING=$(az cosmosdb keys list \
  --resource-group $RG_NAME \
  --name $COSMOS_ACCOUNT \
  --type connection-strings \
  --query "connectionStrings[0].connectionString" \
  --output tsv 2>/dev/null)

# Get Storage Account connection string (from data layer)
STORAGE_ACCOUNT=$(echo "${APP_NAME}storage${ENV}" | tr -d '-')
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group "${APP_NAME}-db-rg" \
  --name $STORAGE_ACCOUNT \
  --query "connectionString" \
  --output tsv 2>/dev/null)

# Get Application Insights connection string
APP_INSIGHTS="${APP_NAME}-insights-${ENV}"
APP_INSIGHTS_CONNECTION_STRING=$(az monitor app-insights component show \
  --resource-group $RG_NAME \
  --app $APP_INSIGHTS \
  --query "connectionString" \
  --output tsv 2>/dev/null)

# Get Redis connection string
REDIS_NAME="${APP_NAME}-redis-${ENV}"
REDIS_HOST=$(az redis show \
  --resource-group $RG_NAME \
  --name $REDIS_NAME \
  --query "hostName" \
  --output tsv 2>/dev/null)
REDIS_KEY=$(az redis list-keys \
  --resource-group $RG_NAME \
  --name $REDIS_NAME \
  --query "primaryKey" \
  --output tsv 2>/dev/null)
REDIS_CONNECTION_STRING="redis://:${REDIS_KEY}@${REDIS_HOST}:6380?ssl=True"

# Create the .env file
echo -e "${COLOR_GREEN}Creating environment file at ${OUTPUT_FILE}...${COLOR_RESET}"

cat > $OUTPUT_FILE << EOF
# Pathfinder Environment Variables
# Generated on $(date)
# Environment: ${ENV}

# Database
DATABASE_URL=mssql+pyodbc://${SQL_ADMIN_USERNAME}:${SQL_ADMIN_PASSWORD}@${SQL_SERVER}:1433/${SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
COSMOS_CONNECTION_STRING=${COSMOS_CONNECTION_STRING}
REDIS_CONNECTION_STRING=${REDIS_CONNECTION_STRING}

# Storage
STORAGE_CONNECTION_STRING=${STORAGE_CONNECTION_STRING}

# AI Services
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_DEFAULT_MODEL=gpt-4o-mini

# Monitoring
APPLICATIONINSIGHTS_CONNECTION_STRING=${APP_INSIGHTS_CONNECTION_STRING}
LOG_LEVEL=info

# Authentication
AUTH0_DOMAIN=dev-jwnud3v8ghqnyygr.us.auth0.com
AUTH0_AUDIENCE=https://api.pathfinder.com
JWT_SECRET=your-jwt-secret-key-here

# Application settings
API_URL=https://localhost:8000
FRONTEND_URL=https://localhost:3000
ENVIRONMENT=${ENV}
AI_DAILY_BUDGET_LIMIT=10.0
EOF

echo -e "${COLOR_GREEN}Environment file created successfully.${COLOR_RESET}"
echo "Note: Some values may require manual updates if they couldn't be retrieved automatically."
echo "For local development, please modify the URLs accordingly."