#!/bin/bash
# Pause Environment - Delete Compute Layer (pathfinder-rg)
# Preserves all data in pathfinder-db-rg

set -e

# Configuration
COMPUTE_RG="pathfinder-rg"
DATA_RG="pathfinder-db-rg"

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

echo "🛑 Pausing Pathfinder Environment"
echo "================================="
echo ""
log_warning "This will delete the compute layer ($COMPUTE_RG) to save costs"
log_info "All your data will be preserved in $DATA_RG"
echo ""

# Skip prompt in non-interactive environments (CI) or when FORCE_PAUSE is set
if [[ -n "$CI" || -n "$FORCE_PAUSE" ]]; then
    log_info "Non-interactive or forced pause requested, proceeding without confirmation"
else
    read -p "Are you sure you want to pause the environment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
fi

# Check if Azure CLI is logged in
log_info "Checking Azure CLI login..."
if ! az account show &> /dev/null; then
    log_error "Not logged into Azure CLI. Please run 'az login' first."
    exit 1
fi

# Check if data RG exists
log_info "Verifying data layer exists..."
if ! az group show --name "$DATA_RG" &> /dev/null; then
    log_error "Data resource group '$DATA_RG' not found!"
    log_error "Make sure you've deployed the persistent data layer first."
    exit 1
fi

# Get current account info
SUBSCRIPTION=$(az account show --query name -o tsv)
log_info "Subscription: $SUBSCRIPTION"

# Backup current app URLs before deletion
log_info "Documenting current endpoints..."
if az group show --name "$COMPUTE_RG" &> /dev/null; then
    # Try to get app URLs
    BACKEND_URL=$(az containerapp show --name pathfinder-backend --resource-group "$COMPUTE_RG" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "not-found")
    FRONTEND_URL=$(az containerapp show --name pathfinder-frontend --resource-group "$COMPUTE_RG" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "not-found")
    
    # Save to file for resume
    cat > pause-state.json << EOF
{
  "pausedAt": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "subscription": "$SUBSCRIPTION",
  "computeResourceGroup": "$COMPUTE_RG",
  "dataResourceGroup": "$DATA_RG",
  "previousEndpoints": {
    "backend": "$BACKEND_URL",
    "frontend": "$FRONTEND_URL"
  }
}
EOF
    log_success "Environment state saved to pause-state.json"
else
    log_warning "Compute resource group not found - may already be paused"
fi

# Delete the compute resource group
log_info "Deleting compute resource group: $COMPUTE_RG"
log_warning "This will take 5-10 minutes..."

if az group show --name "$COMPUTE_RG" &> /dev/null; then
    az group delete --name "$COMPUTE_RG" --yes --no-wait
    log_success "Deletion initiated for $COMPUTE_RG"
    
    # Wait for deletion to complete
    log_info "Monitoring deletion progress..."
    while az group show --name "$COMPUTE_RG" &> /dev/null; do
        echo -n "."
        sleep 30
    done
    echo ""
    log_success "Compute layer deleted successfully!"
else
    log_info "Compute resource group already deleted"
fi

# Verify data layer is still intact
log_info "Verifying data layer integrity..."
if az group show --name "$DATA_RG" &> /dev/null; then
    RESOURCE_COUNT=$(az resource list --resource-group "$DATA_RG" --query "length(@)")
    log_success "Data layer preserved: $RESOURCE_COUNT resources in $DATA_RG"
else
    log_error "Data layer resource group not found!"
    exit 1
fi

# Calculate cost savings
echo ""
log_success "🎉 Environment Successfully Paused!"
echo "====================================="
log_info "✅ Compute layer deleted ($COMPUTE_RG)"
log_info "✅ Data layer preserved ($DATA_RG)"
log_info "💰 Estimated savings: \$35-50/month"
log_info "📊 Remaining cost: \$15-25/month (data layer only)"
echo ""
log_info "📋 To resume: Run ./scripts/resume-environment.sh"
log_info "📁 State saved: pause-state.json"
echo ""
log_warning "Note: Your app URLs will change when you resume"
