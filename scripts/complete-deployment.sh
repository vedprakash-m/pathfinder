#!/bin/bash
# Complete Pathfinder Deployment Script
# Handles authentication, data layer, and compute layer deployment

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_RG="pathfinder-db-rg"
COMPUTE_RG="pathfinder-rg"
LOCATION="westus2"

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

echo "🚀 Pathfinder Complete Deployment"
echo "=================================="
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Check Azure CLI
log_info "Checking Azure CLI..."
if ! command -v az &> /dev/null; then
    log_error "Azure CLI not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install azure-cli
    else
        log_error "Please install Azure CLI manually: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
fi

log_success "Azure CLI found"

# Step 2: Check authentication
log_info "Checking Azure authentication..."
if ! az account show &> /dev/null; then
    log_warning "Not authenticated with Azure. Starting login process..."
    echo ""
    echo "Please follow the authentication prompts..."
    az login
else
    SUBSCRIPTION=$(az account show --query name -o tsv)
    log_success "Already authenticated with subscription: $SUBSCRIPTION"
fi

# Step 3: Check if data layer exists
log_info "Checking if data layer exists..."
if az group show --name "$DATA_RG" &> /dev/null; then
    log_success "Data layer resource group '$DATA_RG' already exists"
    DATA_EXISTS=true
else
    log_warning "Data layer resource group '$DATA_RG' does not exist"
    DATA_EXISTS=false
fi

# Step 4: Check if compute layer exists
log_info "Checking if compute layer exists..."
if az group show --name "$COMPUTE_RG" &> /dev/null; then
    log_success "Compute layer resource group '$COMPUTE_RG' already exists"
    COMPUTE_EXISTS=true
else
    log_warning "Compute layer resource group '$COMPUTE_RG' does not exist"
    COMPUTE_EXISTS=false
fi

# Step 5: Deploy data layer if needed
if [ "$DATA_EXISTS" = false ]; then
    echo ""
    log_info "Deploying data layer (this may take 10-15 minutes)..."
    export LOCATION="$LOCATION"
    
    if [ -f "scripts/deploy-data-layer.sh" ]; then
        chmod +x scripts/deploy-data-layer.sh
        ./scripts/deploy-data-layer.sh
        log_success "Data layer deployment completed"
    else
        log_error "Data layer deployment script not found"
        exit 1
    fi
else
    log_info "Skipping data layer deployment (already exists)"
fi

# Step 6: Deploy compute layer
echo ""
log_info "Deploying compute layer..."
if [ -f "scripts/resume-environment.sh" ]; then
    chmod +x scripts/resume-environment.sh
    export LOCATION="$LOCATION"
    ./scripts/resume-environment.sh
    log_success "Compute layer deployment completed"
else
    log_error "Compute layer deployment script not found"
    exit 1
fi

# Step 7: Final verification
echo ""
log_info "Verifying deployment..."

# Check data layer resources
log_info "Data layer resources:"
az resource list --resource-group "$DATA_RG" --query "[].{Name:name,Type:type,Status:properties.provisioningState}" -o table

echo ""

# Check compute layer resources
log_info "Compute layer resources:"
az resource list --resource-group "$COMPUTE_RG" --query "[].{Name:name,Type:type,Status:properties.provisioningState}" -o table

echo ""
log_success "🎉 Pathfinder deployment completed!"
echo ""
echo "Next steps:"
echo "1. Check application endpoints in Azure portal"
echo "2. Test backend: https://<backend-url>/docs"
echo "3. Test frontend: https://<frontend-url>"
echo "4. Monitor costs in Azure Cost Management"
echo ""
echo "To pause environment (save ~70% costs):"
echo "  ./scripts/pause-environment.sh"
echo ""
echo "To resume environment:"
echo "  ./scripts/resume-environment.sh"
