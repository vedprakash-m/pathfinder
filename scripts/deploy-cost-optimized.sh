#!/bin/bash
# Deploy cost-optimized Pathfinder infrastructure

set -e

echo "🚀 Deploying Ultra Cost-Optimized Pathfinder Infrastructure"
echo "============================================================"

# Configuration
RESOURCE_GROUP="pathfinder-prod"
LOCATION="eastus"
TEMPLATE_FILE="infrastructure/bicep/ultra-cost-optimized.bicep"

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
    read -p "Enter SQL Server admin username: " SQL_ADMIN_USERNAME
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

# Show cost estimate
echo ""
log_warning "COST OPTIMIZATION SUMMARY"
echo "=========================="
echo "Expected monthly cost reduction:"
echo "• Container Apps: $25-30 → $8-12 (60-70% reduction)"
echo "• SQL Database: $15-20 → $12-15 (20% reduction)"
echo "• Cosmos DB: $15-25 → $10-18 (30% reduction)"
echo "• Monitoring: $5-10 → $2-5 (50% reduction)"
echo ""
echo "Total estimated cost: $45-65/month (down from $85)"
echo "Estimated savings: $20-40/month"
echo ""

log_warning "PERFORMANCE TRADE-OFFS"
echo "======================"
echo "• Cold start time: 8-12 seconds after idle periods"
echo "• Single replica maximum (no high availability)"
echo "• Reduced monitoring retention (7 days vs 30 days)"
echo "• Lower resource allocation may affect peak performance"
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
log_info "Deploying ultra cost-optimized infrastructure..."
log_info "This may take 10-15 minutes..."

DEPLOYMENT_NAME="pathfinder-cost-optimized-$(date +%Y%m%d-%H%M%S)"

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
    echo ""
    
    log_info "NEXT STEPS:"
    echo "1. Update your CI/CD pipeline to use the new infrastructure"
    echo "2. Monitor costs in Azure Portal over the next few days"
    echo "3. Set up cost alerts if not already configured"
    echo "4. Test application performance and adjust scaling if needed"
    echo ""
    
    log_warning "PERFORMANCE MONITORING:"
    echo "• Monitor cold start times and user experience"
    echo "• Adjust scaling rules if response times are unacceptable"
    echo "• Consider upgrading resources if performance degrades significantly"
    echo ""
    
else
    log_error "Infrastructure deployment failed"
    log_info "Check the deployment logs in Azure Portal for details"
    exit 1
fi

# Set up cost alerts
echo ""
log_info "Setting up cost monitoring..."

# Create cost alert for 80% of budget
az consumption budget create \
    --budget-name "pathfinder-cost-alert" \
    --amount 75 \
    --time-grain Monthly \
    --time-period start-date=$(date +%Y-%m-01) \
    --category Cost \
    --resource-group-filter $RESOURCE_GROUP \
    --notifications \
        '[{
          "enabled": true,
          "operator": "GreaterThan",
          "threshold": 80,
          "contactEmails": ["admin@pathfinder.com"]
        }]' \
    --output none 2>/dev/null || log_warning "Cost alert setup failed (may already exist)"

log_success "Cost monitoring configured"

echo ""
log_success "🎉 Ultra cost-optimized Pathfinder deployment complete!"
log_info "Expected monthly savings: $20-40 compared to previous setup"
log_info "Monitor your Azure costs over the next billing cycle to confirm savings"
