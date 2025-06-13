#!/bin/bash
# Deploy Pathfinder to Single Resource Group
# Optimized for cost-effective solo developer deployment

set -e

echo "🚀 Deploying Pathfinder with Single Resource Group Strategy"
echo "=========================================================="

# Configuration
RESOURCE_GROUP="pathfinder-rg"
LOCATION="eastus"
TEMPLATE_FILE="infrastructure/bicep/pathfinder-single-rg.bicep"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed"
    exit 1
fi

if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Run 'az login' first"
    exit 1
fi

log_success "Prerequisites check passed"

# Get required parameters
echo ""
log_info "Gathering deployment parameters..."

if [ -z "$SQL_ADMIN_USERNAME" ]; then
    read -p "Enter SQL Server admin username (default: pathfinderadmin): " SQL_ADMIN_USERNAME
    SQL_ADMIN_USERNAME=${SQL_ADMIN_USERNAME:-pathfinderadmin}
fi

if [ -z "$SQL_ADMIN_PASSWORD" ]; then
    read -s -p "Enter SQL Server admin password: " SQL_ADMIN_PASSWORD
    echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
    read -s -p "Enter OpenAI API key (optional): " OPENAI_API_KEY
    echo ""
fi

# Validate template
log_info "Validating Bicep template..."
if az deployment group validate \
    --resource-group $RESOURCE_GROUP \
    --template-file $TEMPLATE_FILE \
    --parameters \
        sqlAdminLogin="$SQL_ADMIN_USERNAME" \
        sqlAdminPassword="$SQL_ADMIN_PASSWORD" \
        openAIApiKey="$OPENAI_API_KEY" \
    --output none; then
    log_success "Template validation passed"
else
    log_error "Template validation failed"
    exit 1
fi

# Show deployment details
echo ""
log_info "Deployment Details:"
echo "• Resource Group: $RESOURCE_GROUP"
echo "• Location: $LOCATION"
echo "• Template: $TEMPLATE_FILE"
echo "• SQL Admin: $SQL_ADMIN_USERNAME"
echo "• Strategy: Single Resource Group for Cost Optimization"
echo ""
echo "💰 Cost Benefits:"
echo "• Single resource group for simplified management"
echo "• No Redis cache (saves ~$40/month)"
echo "• Serverless Cosmos DB (pay-per-use)"
echo "• Basic SQL tier (cost-optimized)"
echo "• Scale-to-zero containers"
echo "• Bicep-only infrastructure (faster deployments)"
echo ""

read -p "Continue with deployment? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Deployment cancelled"
    exit 0
fi

# Create resource group if it doesn't exist
log_info "Ensuring resource group exists..."
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    log_info "Creating resource group $RESOURCE_GROUP..."
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    log_success "Resource group created"
else
    log_success "Resource group already exists"
fi

# Deploy infrastructure
echo ""
log_info "Deploying cost-optimized infrastructure..."
log_info "This may take 8-12 minutes..."

DEPLOYMENT_NAME="pathfinder-single-rg-$(date +%Y%m%d-%H%M%S)"

if az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --name $DEPLOYMENT_NAME \
    --template-file $TEMPLATE_FILE \
    --parameters \
        sqlAdminLogin="$SQL_ADMIN_USERNAME" \
        sqlAdminPassword="$SQL_ADMIN_PASSWORD" \
        openAIApiKey="$OPENAI_API_KEY" \
    --output none; then
    
    log_success "Infrastructure deployment completed!"
    
    # Get deployment outputs
    log_info "Getting deployment outputs..."
    
    BACKEND_URL=$(az deployment group show \
        --resource-group $RESOURCE_GROUP \
        --name $DEPLOYMENT_NAME \
        --query "properties.outputs.backendAppUrl.value" \
        --output tsv)
    
    FRONTEND_URL=$(az deployment group show \
        --resource-group $RESOURCE_GROUP \
        --name $DEPLOYMENT_NAME \
        --query "properties.outputs.frontendAppUrl.value" \
        --output tsv)
    
    # Display results
    echo ""
    log_success "DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "=================================="
    echo "Frontend URL: $FRONTEND_URL"
    echo "Backend URL: $BACKEND_URL"
    echo "Resource Group: $RESOURCE_GROUP"
    echo ""
    echo "💰 Cost Optimization Benefits Applied:"
    echo "✅ Single resource group for unified management"
    echo "✅ Redis-free architecture (saves ~$40/month)"
    echo "✅ Serverless Cosmos DB (pay-per-use pricing)"
    echo "✅ Basic SQL tier (cost-optimized)"
    echo "✅ Scale-to-zero containers (no idle costs)"
    echo "✅ Bicep-exclusive infrastructure"
    echo ""
    echo "🔗 Next Steps:"
    echo "1. Update your CI/CD pipeline to use the new resource group"
    echo "2. Configure container app images through CI/CD or manually"
    echo "3. Set up monitoring alerts for cost control"
    echo "4. Review Azure costs in the Azure portal"
    echo ""
    echo "📊 Estimated Monthly Cost: $45-65 (vs $110+ for multi-environment)"
    
else
    log_error "Deployment failed!"
    exit 1
fi
