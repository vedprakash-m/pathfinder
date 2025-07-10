#!/bin/bash

# Pathfinder Single Resource Group Deployment - Production Ready
# Uses the single slot, single environment approach as per Tech Spec

set -e

echo "🚀 Pathfinder Production Deployment - Single Resource Group"
echo "=========================================================="

# Configuration
APP_NAME="pathfinder"
LOCATION="westus2"
RESOURCE_GROUP="${APP_NAME}-rg"
SQL_ADMIN_USERNAME="pathfinderadmin"
SQL_ADMIN_PASSWORD="PathfinderSecure2024!"

# Microsoft Entra External ID Configuration
ENTRA_EXTERNAL_TENANT_ID="2d45675f-5263-415c-8239-a4b82a995639"
ENTRA_EXTERNAL_CLIENT_ID="placeholder-client-id"  # Will be updated after deployment
OPENAI_API_KEY="sk-placeholder-key"  # Replace with actual key

echo "📋 Deployment Configuration:"
echo "App Name: $APP_NAME"
echo "Location: $LOCATION"
echo "Resource Group: $RESOURCE_GROUP"
echo "External ID Tenant: $ENTRA_EXTERNAL_TENANT_ID"
echo ""

# Step 1: Verify Azure CLI login
echo "🔍 Verifying Azure CLI login..."
SUBSCRIPTION=$(az account show --query "name" -o tsv)
echo "✅ Logged in to subscription: $SUBSCRIPTION"

# Step 2: Create Resource Group
echo "📦 Creating resource group..."
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --tags \
    "app=$APP_NAME" \
    "environment=production" \
    "architecture=single-rg" \
    "costOptimization=enabled"

echo "✅ Resource group created: $RESOURCE_GROUP"

# Step 3: Deploy Infrastructure
echo "🏗️ Deploying infrastructure using single resource group template..."
DEPLOYMENT_NAME="pathfinder-prod-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "infrastructure/bicep/pathfinder-single-rg.bicep" \
  --parameters \
    appName="$APP_NAME" \
    sqlAdminLogin="$SQL_ADMIN_USERNAME" \
    sqlAdminPassword="$SQL_ADMIN_PASSWORD" \
    entraTenantId="$ENTRA_EXTERNAL_TENANT_ID" \
    entraClientId="$ENTRA_EXTERNAL_CLIENT_ID" \
    openAIApiKey="$OPENAI_API_KEY" \
  --name "$DEPLOYMENT_NAME" \
  --verbose

echo "✅ Infrastructure deployment completed"

# Step 4: Get Application URLs
echo "🌐 Retrieving application URLs..."
BACKEND_URL=$(az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --query "properties.outputs.backendAppUrl.value" \
  -o tsv)

FRONTEND_URL=$(az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --query "properties.outputs.frontendAppUrl.value" \
  -o tsv)

# Step 5: Display Results
echo ""
echo "✅ Pathfinder deployment completed successfully!"
echo "================================================="
echo ""
echo "🌐 Application URLs:"
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "📋 Next Steps:"
echo "1. Update Microsoft Entra External ID app registration with these URLs:"
echo "   - Redirect URI: $FRONTEND_URL/auth/callback"
echo "   - Single-page application: $FRONTEND_URL"
echo ""
echo "2. Update environment variables with real values:"
echo "   - OpenAI API Key in Azure Key Vault"
echo "   - External ID Client ID: $ENTRA_EXTERNAL_CLIENT_ID"
echo ""
echo "3. Test the deployment:"
echo "   - Backend API: $BACKEND_URL/docs"
echo "   - Frontend App: $FRONTEND_URL"
echo ""
echo "📊 Infrastructure Details:"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Architecture: Single Resource Group (cost-optimized)"
echo ""
echo "💰 Estimated Monthly Cost: \$50-75 (production workload)"
echo "⚡ Auto-scaling: 0-3 instances based on demand"
echo ""
echo "🔗 Management Commands:"
echo "Monitor resources: az resource list --resource-group $RESOURCE_GROUP"
echo "View costs: az consumption usage list --resource-group $RESOURCE_GROUP"
echo ""
