#!/bin/bash

# Simple Pathfinder Deployment Script - Microsoft Entra External ID
# This script deploys Pathfinder with the new authentication system

set -e

echo "🚀 Pathfinder Simple Deployment - Microsoft Entra External ID"
echo "============================================================"

# Configuration (you can modify these)
APP_NAME="pathfinder"
LOCATION="westus2"
DATA_RG="${APP_NAME}-db-rg"
COMPUTE_RG="${APP_NAME}-rg"
SQL_ADMIN_USERNAME="pathfinderadmin"
SQL_ADMIN_PASSWORD="PathfinderSecure2024!"

# Your External ID tenant configuration
ENTRA_EXTERNAL_TENANT_ID="2d45675f-5263-415c-8239-a4b82a995639"
ENTRA_EXTERNAL_CLIENT_ID="placeholder-client-id"  # Will update after getting URLs
ENTRA_EXTERNAL_AUTHORITY="https://VedID.onmicrosoft.com"

echo "📋 Configuration:"
echo "App Name: $APP_NAME"
echo "Location: $LOCATION"
echo "External ID Tenant: $ENTRA_EXTERNAL_TENANT_ID"
echo ""

# Step 1: Check Azure login
echo "🔍 Checking Azure login..."
az account show --query "name" -o tsv

# Step 2: Create Data Resource Group
echo "📦 Creating data resource group..."
az group create --name "$DATA_RG" --location "$LOCATION" --tags "app=$APP_NAME" "type=data-layer" "autoDelete=never"

# Step 3: Deploy Data Layer
echo "🗄️ Deploying data layer..."
az deployment group create \
  --resource-group "$DATA_RG" \
  --template-file "infrastructure/bicep/persistent-data.bicep" \
  --parameters \
    appName="$APP_NAME" \
    sqlAdminLogin="$SQL_ADMIN_USERNAME" \
    sqlAdminPassword="$SQL_ADMIN_PASSWORD" \
  --name "data-layer-$(date +%Y%m%d-%H%M%S)"

# Step 4: Create Compute Resource Group  
echo "📦 Creating compute resource group..."
az group create --name "$COMPUTE_RG" --location "$LOCATION" --tags "app=$APP_NAME" "type=compute-layer" "dataLayer=$DATA_RG"

# Step 5: Deploy Compute Layer
echo "🚀 Deploying compute layer..."
az deployment group create \
  --resource-group "$COMPUTE_RG" \
  --template-file "infrastructure/bicep/compute-layer.bicep" \
  --parameters \
    appName="$APP_NAME" \
    dataResourceGroup="$DATA_RG" \
    sqlServerName="${APP_NAME}-sql-prod" \
    cosmosAccountName="${APP_NAME}-cosmos-prod" \
    storageAccountName="pathfinderstorageprod" \
    dataKeyVaultName="${APP_NAME}-db-kv-prod" \
    sqlAdminLogin="$SQL_ADMIN_USERNAME" \
    sqlAdminPassword="$SQL_ADMIN_PASSWORD" \
    entraTenantId="$ENTRA_EXTERNAL_TENANT_ID" \
    entraClientId="$ENTRA_EXTERNAL_CLIENT_ID" \
  --name "compute-layer-$(date +%Y%m%d-%H%M%S)"

# Step 6: Get Application URLs
echo "🌐 Getting application URLs..."
BACKEND_URL=$(az containerapp show --name pathfinder-backend --resource-group "$COMPUTE_RG" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "Not deployed yet")
FRONTEND_URL=$(az containerapp show --name pathfinder-frontend --resource-group "$COMPUTE_RG" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null || echo "Not deployed yet")

echo ""
echo "✅ Infrastructure deployment complete!"
echo ""
echo "🌐 Application URLs:"
echo "Frontend: https://$FRONTEND_URL"
echo "Backend:  https://$BACKEND_URL"
echo ""
echo "📋 Next steps:"
echo "1. Update your External ID app registration with these URLs:"
echo "   - https://$FRONTEND_URL"
echo "   - https://$FRONTEND_URL/auth/callback"
echo "2. Update this script with your Client ID: $ENTRA_EXTERNAL_CLIENT_ID"
echo "3. Deploy application code via CI/CD or manually"
echo ""
echo "🎉 Ready for application deployment!" 