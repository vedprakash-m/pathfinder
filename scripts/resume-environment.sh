#!/bin/bash
# Resume Environment - Recreate Compute Layer (pathfinder-rg)
# Connects to existing data layer in pathfinder-db-rg

set -e

# Configuration
COMPUTE_RG="pathfinder-rg"
DATA_RG="pathfinder-db-rg"
LOCATION="${LOCATION:-westus2}"  # Use environment variable or default to westus2
COMPUTE_TEMPLATE="infrastructure/bicep/compute-layer.bicep"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🚀 Resuming Pathfinder Environment"
echo "=================================="
echo ""

# Check if Azure CLI is logged in
log_info "Checking Azure CLI login..."
if ! az account show &> /dev/null; then
    log_error "Not logged into Azure CLI. Please run 'az login' first."
    exit 1
fi

# Verify data layer exists
log_info "Verifying data layer..."
if ! az group show --name "$DATA_RG" &> /dev/null; then
    log_error "Data resource group '$DATA_RG' not found!"
    log_error "You need to deploy the persistent data layer first:"
    log_error "  ./scripts/deploy-data-layer.sh"
    exit 1
fi

# Check if compute layer already exists
if az group show --name "$COMPUTE_RG" &> /dev/null; then
    log_warning "Compute resource group '$COMPUTE_RG' already exists"
    read -p "Do you want to redeploy it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
fi

# Load pause state if available
PAUSE_STATE_FILE="pause-state.json"
if [[ -f "$PAUSE_STATE_FILE" ]]; then
    log_info "Found pause state file: $PAUSE_STATE_FILE"
    PAUSED_AT=$(jq -r '.pausedAt' "$PAUSE_STATE_FILE")
    log_info "Environment was paused at: $PAUSED_AT"
fi

# Get required secrets from environment or prompt
log_info "Checking required configuration..."

# SQL Admin credentials
if [[ -z "$SQL_ADMIN_USERNAME" ]]; then
    read -p "SQL Admin Username: " SQL_ADMIN_USERNAME
fi

if [[ -z "$SQL_ADMIN_PASSWORD" ]]; then
    read -s -p "SQL Admin Password: " SQL_ADMIN_PASSWORD
    echo
fi

# Optional: OpenAI API Key
if [[ -z "$OPENAI_API_KEY" ]]; then
    read -p "OpenAI API Key (optional, press enter to skip): " OPENAI_API_KEY
fi

# Get data layer connection strings
log_info "Retrieving data layer connection details..."

# Get SQL connection string from Key Vault
SQL_SERVER_NAME=$(az sql server list --resource-group "$DATA_RG" --query "[0].name" -o tsv)
if [[ -z "$SQL_SERVER_NAME" ]]; then
    log_error "Could not find SQL server in data layer"
    exit 1
fi

# Get Cosmos connection string
COSMOS_ACCOUNT_NAME=$(az cosmosdb list --resource-group "$DATA_RG" --query "[0].name" -o tsv)
if [[ -z "$COSMOS_ACCOUNT_NAME" ]]; then
    log_error "Could not find Cosmos account in data layer"
    exit 1
fi

# Get Storage account name
STORAGE_ACCOUNT_NAME=$(az storage account list --resource-group "$DATA_RG" --query "[0].name" -o tsv)
if [[ -z "$STORAGE_ACCOUNT_NAME" ]]; then
    log_error "Could not find Storage account in data layer"
    exit 1
fi

# Get Data layer Key Vault name
DATA_KEY_VAULT_NAME=$(az keyvault list --resource-group "$DATA_RG" --query "[0].name" -o tsv)
if [[ -z "$DATA_KEY_VAULT_NAME" ]]; then
    log_error "Could not find Key Vault in data layer"
    exit 1
fi

log_success "Found data layer resources:"
log_info "  SQL Server: $SQL_SERVER_NAME"
log_info "  Cosmos Account: $COSMOS_ACCOUNT_NAME"
log_info "  Storage Account: $STORAGE_ACCOUNT_NAME"
log_info "  Data Key Vault: $DATA_KEY_VAULT_NAME"

# Create compute resource group
log_info "Checking compute resource group: $COMPUTE_RG"
if az group show --name "$COMPUTE_RG" &> /dev/null; then
    log_warning "Compute resource group '$COMPUTE_RG' already exists"
else
    log_info "Creating compute resource group: $COMPUTE_RG"
    az group create --name "$COMPUTE_RG" --location "$LOCATION" --tags \
        "app=pathfinder" \
        "type=compute-layer" \
        "dataLayer=$DATA_RG" \
        "resumedAt=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
fi

# Deploy compute layer template
log_info "Deploying compute layer infrastructure..."
log_warning "This will take 10-15 minutes..."

DEPLOYMENT_NAME="compute-layer-$(date +%Y%m%d-%H%M%S)"

# Create deployment parameters
cat > compute-params.json << EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appName": {
      "value": "pathfinder"
    },
    "dataResourceGroup": {
      "value": "$DATA_RG"
    },
    "sqlServerName": {
      "value": "$SQL_SERVER_NAME"
    },
    "cosmosAccountName": {
      "value": "$COSMOS_ACCOUNT_NAME"
    },
    "storageAccountName": {
      "value": "$STORAGE_ACCOUNT_NAME"
    },
    "dataKeyVaultName": {
      "value": "$DATA_KEY_VAULT_NAME"
    },
    "sqlAdminLogin": {
      "value": "$SQL_ADMIN_USERNAME"
    },
    "sqlAdminPassword": {
      "value": "$SQL_ADMIN_PASSWORD"
    },
    "openAIApiKey": {
      "value": "$OPENAI_API_KEY"
    }
  }
}
EOF

# Deploy infrastructure
az deployment group create \
    --resource-group "$COMPUTE_RG" \
    --template-file "$COMPUTE_TEMPLATE" \
    --parameters @compute-params.json \
    --name "$DEPLOYMENT_NAME"

# Clean up temporary files
rm -f compute-params.json

# Get deployment outputs
log_info "Retrieving deployment outputs..."
BACKEND_URL=$(az deployment group show --resource-group "$COMPUTE_RG" --name "$DEPLOYMENT_NAME" --query "properties.outputs.backendAppUrl.value" -o tsv)
FRONTEND_URL=$(az deployment group show --resource-group "$COMPUTE_RG" --name "$DEPLOYMENT_NAME" --query "properties.outputs.frontendAppUrl.value" -o tsv)

# Update pause state with new URLs
if [[ -f "$PAUSE_STATE_FILE" ]]; then
    TEMP_JSON=$(mktemp)
    jq --arg backend "$BACKEND_URL" --arg frontend "$FRONTEND_URL" --arg resumed "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")" \
        '.resumedAt = $resumed | .newEndpoints = {"backend": $backend, "frontend": $frontend}' \
        "$PAUSE_STATE_FILE" > "$TEMP_JSON"
    mv "$TEMP_JSON" "$PAUSE_STATE_FILE"
fi

echo ""
log_success "🎉 Environment Successfully Resumed!"
echo "===================================="
log_info "✅ Compute layer deployed ($COMPUTE_RG)"
log_info "✅ Connected to data layer ($DATA_RG)"
log_info "🌐 Backend URL: $BACKEND_URL"
log_info "🌐 Frontend URL: $FRONTEND_URL"
echo ""
log_info "⏱️  Application will be ready in 5-10 minutes"
log_info "🔗 Health check: $BACKEND_URL/health"
echo ""
log_warning "Note: CI/CD pipeline deployment will update container images"
log_info "📋 To pause again: ./scripts/pause-environment.sh"
