#!/bin/bash
# Azure Infrastructure Deployment Script
# This script deploys the Pathfinder infrastructure to Azure

set -e

# Configuration
RESOURCE_GROUP="pathfinder-rg-prod"
LOCATION="eastus"
APP_NAME="pathfinder"
ENVIRONMENT="prod"

echo "🚀 Starting Pathfinder Azure Infrastructure Deployment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Environment: $ENVIRONMENT"

# Check if logged into Azure
echo "Checking Azure authentication..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

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
        location=$LOCATION

# Get deployment outputs
echo "Getting deployment outputs..."
COSMOS_CONNECTION_STRING=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.cosmosConnectionString.value \
    --output tsv)

SQL_CONNECTION_STRING=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.sqlConnectionString.value \
    --output tsv)

REDIS_CONNECTION_STRING=$(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main \
    --query properties.outputs.redisConnectionString.value \
    --output tsv)

# Create GitHub secrets for CI/CD
echo "Setting up GitHub secrets..."
gh secret set AZURE_RESOURCE_GROUP --body "$RESOURCE_GROUP"
gh secret set COSMOS_CONNECTION_STRING --body "$COSMOS_CONNECTION_STRING"
gh secret set SQL_CONNECTION_STRING --body "$SQL_CONNECTION_STRING"
gh secret set REDIS_CONNECTION_STRING --body "$REDIS_CONNECTION_STRING"

echo "✅ Infrastructure deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update environment variables in backend/.env"
echo "2. Run database migrations"
echo "3. Deploy application containers"
echo ""
echo "Connection strings have been set as GitHub secrets for CI/CD."
