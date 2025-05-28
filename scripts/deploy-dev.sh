#!/bin/bash
# Development Environment Deployment Script
# This script deploys the Pathfinder infrastructure to Azure for development

set -e

# Configuration
RESOURCE_GROUP="pathfinder-rg-dev"
LOCATION="eastus"
APP_NAME="pathfinder"
ENVIRONMENT="dev"

echo "🚀 Starting Pathfinder Development Deployment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Environment: $ENVIRONMENT"

# Check if logged into Azure
echo "Checking Azure authentication..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

# Generate secure passwords for development
SQL_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
OPENAI_API_KEY="sk-dev-placeholder-key"

echo "Generated secure passwords for development environment..."

# Create resource group if it doesn't exist
echo "Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --tags environment=$ENVIRONMENT project=pathfinder

# Deploy main infrastructure
echo "Deploying main infrastructure..."
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infrastructure/bicep/main.bicep \
    --parameters \
        appName=$APP_NAME \
        environment=$ENVIRONMENT \
        location=$LOCATION \
        sqlAdminLogin="pathadmin" \
        sqlAdminPassword=$SQL_ADMIN_PASSWORD \
        openAIApiKey=$OPENAI_API_KEY

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Infrastructure deployment completed successfully!"
    echo "📝 Development credentials:"
    echo "   SQL Admin: pathadmin"
    echo "   SQL Password: $SQL_ADMIN_PASSWORD"
    echo ""
    echo "🔗 Getting deployment outputs..."
    
    # Get deployment outputs if available
    az deployment group show \
        --resource-group $RESOURCE_GROUP \
        --name main \
        --query properties.outputs \
        --output table
        
    echo ""
    echo "🎉 Development environment ready!"
    echo "Next steps:"
    echo "1. Configure environment variables"
    echo "2. Deploy applications to Container Apps"
    echo "3. Test the complete application"
else
    echo "❌ Infrastructure deployment failed!"
    exit 1
fi