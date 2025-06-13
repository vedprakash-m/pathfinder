#!/bin/bash
# Deploy Data Layer Only - pathfinder-db-rg
# This should be deployed once and never deleted

set -e

# Configuration
DATA_RG="pathfinder-db-rg"
LOCATION="eastus"
TEMPLATE_FILE="infrastructure/bicep/persistent-data.bicep"

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

echo "🏗️  Deploying Pathfinder Data Layer"
echo "===================================="
echo ""
log_info "This deploys ONLY the persistent data layer ($DATA_RG)"
log_warning "This resource group should NEVER be deleted"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    log_error "Not logged into Azure CLI. Please run 'az login' first."
    exit 1
fi

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    log_error "Template file not found: $TEMPLATE_FILE"
    exit 1
fi

# Get current subscription info
SUBSCRIPTION=$(az account show --query name -o tsv)
TENANT=$(az account show --query tenantId -o tsv)
log_info "Subscription: $SUBSCRIPTION"

# Get required parameters
log_info "Collecting deployment parameters..."

if [[ -z "$SQL_ADMIN_USERNAME" ]]; then
    read -p "SQL Admin Username: " SQL_ADMIN_USERNAME
fi

if [[ -z "$SQL_ADMIN_PASSWORD" ]]; then
    read -s -p "SQL Admin Password: " SQL_ADMIN_PASSWORD
    echo
fi

# Validate password complexity
if [[ ${#SQL_ADMIN_PASSWORD} -lt 8 ]]; then
    log_error "Password must be at least 8 characters long"
    exit 1
fi

# Check if resource group already exists
if az group show --name "$DATA_RG" &> /dev/null; then
    log_warning "Data resource group '$DATA_RG' already exists"
    
    # Check if it has resources
    RESOURCE_COUNT=$(az resource list --resource-group "$DATA_RG" --query "length(@)")
    if [[ $RESOURCE_COUNT -gt 0 ]]; then
        log_warning "Resource group contains $RESOURCE_COUNT resources"
        read -p "Do you want to update the deployment? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Operation cancelled"
            exit 0
        fi
    fi
else
    # Create resource group
    log_info "Creating data resource group: $DATA_RG"
    az group create --name "$DATA_RG" --location "$LOCATION" --tags \
        "app=pathfinder" \
        "type=data-layer" \
        "persistence=true" \
        "autoDelete=never" \
        "createdAt=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
fi

# Deploy data layer
log_info "Deploying persistent data layer..."
log_warning "This will take 5-10 minutes..."

DEPLOYMENT_NAME="data-layer-$(date +%Y%m%d-%H%M%S)"

# Create temporary parameters file
cat > data-params.json << EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appName": {
      "value": "pathfinder"
    },
    "environment": {
      "value": "prod"
    },
    "sqlAdminLogin": {
      "value": "$SQL_ADMIN_USERNAME"
    },
    "sqlAdminPassword": {
      "value": "$SQL_ADMIN_PASSWORD"
    },
    "enablePrivateEndpoints": {
      "value": false
    }
  }
}
EOF

# Deploy template
az deployment group create \
    --resource-group "$DATA_RG" \
    --template-file "$TEMPLATE_FILE" \
    --parameters @data-params.json \
    --name "$DEPLOYMENT_NAME" \
    --verbose

# Clean up
rm -f data-params.json

# Get deployment outputs
log_info "Retrieving deployment outputs..."
SQL_SERVER_FQDN=$(az deployment group show --resource-group "$DATA_RG" --name "$DEPLOYMENT_NAME" --query "properties.outputs.sqlServerFqdn.value" -o tsv)
COSMOS_ACCOUNT_NAME=$(az deployment group show --resource-group "$DATA_RG" --name "$DEPLOYMENT_NAME" --query "properties.outputs.cosmosAccountName.value" -o tsv)
KEY_VAULT_NAME=$(az deployment group show --resource-group "$DATA_RG" --name "$DEPLOYMENT_NAME" --query "properties.outputs.keyVaultName.value" -o tsv)

# Save data layer info
cat > data-layer-info.json << EOF
{
  "deployedAt": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "resourceGroup": "$DATA_RG",
  "subscription": "$SUBSCRIPTION",
  "location": "$LOCATION",
  "resources": {
    "sqlServerFqdn": "$SQL_SERVER_FQDN",
    "cosmosAccountName": "$COSMOS_ACCOUNT_NAME",
    "keyVaultName": "$KEY_VAULT_NAME"
  },
  "costEstimate": {
    "monthlyBaseline": "\$15-25",
    "description": "Serverless Cosmos DB + Basic SQL tier"
  }
}
EOF

echo ""
log_success "🎉 Data Layer Successfully Deployed!"
echo "===================================="
log_info "✅ Resource Group: $DATA_RG"
log_info "✅ SQL Server: $SQL_SERVER_FQDN"
log_info "✅ Cosmos Account: $COSMOS_ACCOUNT_NAME"
log_info "✅ Key Vault: $KEY_VAULT_NAME"
echo ""
log_info "💰 Estimated monthly cost: \$15-25 (data layer only)"
log_info "📁 Info saved: data-layer-info.json"
echo ""
log_success "Next Steps:"
log_info "1. Deploy compute layer: ./scripts/resume-environment.sh"
log_info "2. Or use CI/CD pipeline for full deployment"
echo ""
log_warning "⚠️  IMPORTANT: Never delete this resource group!"
log_warning "   All your application data is stored here."
