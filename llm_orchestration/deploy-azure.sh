#!/bin/bash
# Azure deployment script for LLM Orchestration Service
# This script deploys the service to Azure Container Instances with required infrastructure

set -e

echo "🚀 Starting Azure deployment for LLM Orchestration Service"

# Configuration
RESOURCE_GROUP="llm-orchestration-rg"
LOCATION="eastus"
CONTAINER_NAME="llm-orchestration-service"
KEY_VAULT_NAME="llm-orchestration-vault"
REDIS_NAME="llm-orchestration-redis"
STORAGE_ACCOUNT="llmorchestrationstore"

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Step 2: Create Azure Key Vault
echo "🔐 Creating Azure Key Vault..."
az keyvault create \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku standard \
  --enable-rbac-authorization false

# Get current user object ID
USER_OBJECT_ID=$(az ad signed-in-user show --query id --output tsv)

# Set access policy for current user
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $USER_OBJECT_ID \
  --secret-permissions get list set delete

# Step 3: Add secrets to Key Vault
echo "🔑 Adding secrets to Key Vault..."
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "openai-api-key" --value "sk-placeholder-key"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "gemini-api-key" --value "placeholder-key"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "anthropic-api-key" --value "placeholder-key"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name "redis-password" --value "$(openssl rand -base64 32)"

# Step 4: Create Redis Cache
echo "📊 Creating Redis Cache..."
az redis create \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --vm-size C0

# Step 5: Create Storage Account for logs
echo "💾 Creating Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Step 6: Build and push Docker image to Azure Container Registry
echo "🐳 Setting up Container Registry..."
ACR_NAME="llmorchestrationacr"
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic \
  --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Build and push image
echo "🏗️ Building and pushing Docker image..."
az acr build \
  --registry $ACR_NAME \
  --image llm-orchestration:latest \
  --file Dockerfile.production \
  .

# Step 7: Create managed identity for container
echo "🆔 Creating managed identity..."
IDENTITY_NAME="llm-orchestration-identity"
az identity create \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP

# Get identity details
IDENTITY_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query id --output tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query principalId --output tsv)

# Grant Key Vault access to managed identity
echo "🔐 Granting Key Vault access..."
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $IDENTITY_PRINCIPAL_ID \
  --secret-permissions get list

# Step 8: Deploy Container Instance
echo "🚀 Deploying container instance..."

# Get Redis connection details
REDIS_HOST=$(az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query hostName --output tsv)
REDIS_KEY=$(az redis list-keys --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query primaryKey --output tsv)

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Deploy container
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $ACR_LOGIN_SERVER/llm-orchestration:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --assign-identity $IDENTITY_ID \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --ip-address Public \
  --environment-variables \
    AZURE_KEY_VAULT_NAME=$KEY_VAULT_NAME \
    REDIS_URL=redis://$REDIS_HOST:6380 \
    REDIS_PASSWORD=$REDIS_KEY \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# Step 9: Get deployment details
echo "✅ Deployment complete!"
echo ""
echo "📋 Deployment Details:"
echo "======================"
CONTAINER_IP=$(az container show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --query ipAddress.ip --output tsv)
echo "🌐 Service URL: http://$CONTAINER_IP:8000"
echo "📊 Health Check: http://$CONTAINER_IP:8000/health"
echo "📖 API Docs: http://$CONTAINER_IP:8000/docs"
echo "🔐 Key Vault: $KEY_VAULT_NAME"
echo "📊 Redis Cache: $REDIS_NAME"
echo ""

# Step 10: Test deployment
echo "🧪 Testing deployment..."
sleep 30  # Wait for container to start

if curl -f "http://$CONTAINER_IP:8000/health" > /dev/null 2>&1; then
  echo "✅ Health check passed!"
  echo "🎉 LLM Orchestration Service is running successfully on Azure!"
else
  echo "❌ Health check failed. Checking logs..."
  az container logs --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP
fi

echo ""
echo "🔧 To update API keys, use:"
echo "az keyvault secret set --vault-name $KEY_VAULT_NAME --name 'openai-api-key' --value 'your-real-key'"
echo ""
echo "📊 To check logs:"
echo "az container logs --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "🗑️ To clean up:"
echo "az group delete --name $RESOURCE_GROUP --yes --no-wait"
