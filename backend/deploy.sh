#!/bin/bash

# 🚀 Pathfinder Production Deployment Script
# This script deploys the Pathfinder backend to production

set -e  # Exit on any error

echo "🚀 Starting Pathfinder Production Deployment..."

# Configuration
APP_NAME="pathfinder-backend"
RESOURCE_GROUP="pathfinder-rg"
CONTAINER_ENV="pathfinder-env"
IMAGE_NAME="pathfinder-backend"
TAG="latest"

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "📁 Current directory: $(pwd)"

# Step 1: Build Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME:$TAG .

# Step 2: Tag for registry (adjust registry URL as needed)
if [ ! -z "$AZURE_CONTAINER_REGISTRY" ]; then
    echo "🏷️  Tagging image for Azure Container Registry..."
    FULL_IMAGE_NAME="$AZURE_CONTAINER_REGISTRY.azurecr.io/$IMAGE_NAME:$TAG"
    docker tag $IMAGE_NAME:$TAG $FULL_IMAGE_NAME
    
    echo "📤 Pushing to Azure Container Registry..."
    docker push $FULL_IMAGE_NAME
    
    IMAGE_FOR_DEPLOYMENT=$FULL_IMAGE_NAME
else
    echo "⚠️  AZURE_CONTAINER_REGISTRY not set, using local image"
    IMAGE_FOR_DEPLOYMENT=$IMAGE_NAME:$TAG
fi

# Step 3: Deploy to Azure Container Apps (if Azure CLI available)
if command -v az &> /dev/null; then
    echo "☁️  Deploying to Azure Container Apps..."
    
    # Check if container app exists
    if az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        echo "🔄 Updating existing container app..."
        az containerapp update \
            --name $APP_NAME \
            --resource-group $RESOURCE_GROUP \
            --image $IMAGE_FOR_DEPLOYMENT \
            --environment-variables \
                ENVIRONMENT=production \
                SECRET_KEY="$SECRET_KEY" \
                COSMOS_DB_ENABLED=true \
                COSMOS_DB_ENDPOINT="$COSMOS_DB_ENDPOINT" \
                COSMOS_DB_KEY="$COSMOS_DB_KEY" \
                COSMOS_DB_DATABASE_NAME="$COSMOS_DB_DATABASE_NAME" \
                OPENAI_API_KEY="$OPENAI_API_KEY" \
                AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
                AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
                AZURE_TENANT_ID="$AZURE_TENANT_ID" \
                ALLOWED_HOSTS="$ALLOWED_HOSTS"
    else
        echo "🆕 Creating new container app..."
        az containerapp create \
            --name $APP_NAME \
            --resource-group $RESOURCE_GROUP \
            --environment $CONTAINER_ENV \
            --image $IMAGE_FOR_DEPLOYMENT \
            --target-port 8000 \
            --ingress external \
            --min-replicas 1 \
            --max-replicas 10 \
            --cpu 1.0 \
            --memory 2Gi \
            --environment-variables \
                ENVIRONMENT=production \
                SECRET_KEY="$SECRET_KEY" \
                COSMOS_DB_ENABLED=true \
                COSMOS_DB_ENDPOINT="$COSMOS_DB_ENDPOINT" \
                COSMOS_DB_KEY="$COSMOS_DB_KEY" \
                COSMOS_DB_DATABASE_NAME="$COSMOS_DB_DATABASE_NAME" \
                OPENAI_API_KEY="$OPENAI_API_KEY" \
                AZURE_CLIENT_ID="$AZURE_CLIENT_ID" \
                AZURE_CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
                AZURE_TENANT_ID="$AZURE_TENANT_ID" \
                ALLOWED_HOSTS="$ALLOWED_HOSTS"
    fi
    
    # Get the application URL
    echo "🔍 Getting application URL..."
    APP_URL=$(az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)
    
    if [ ! -z "$APP_URL" ]; then
        echo "✅ Deployment successful!"
        echo "🌐 Application URL: https://$APP_URL"
        echo "🏥 Health check: https://$APP_URL/health"
        echo "📚 API docs: https://$APP_URL/docs"
        
        # Test the deployment
        echo "🧪 Testing deployment..."
        sleep 30  # Wait for deployment to be ready
        
        HEALTH_STATUS=$(curl -s "https://$APP_URL/health" | grep -o '"status":"healthy"' || echo "failed")
        if [ "$HEALTH_STATUS" == '"status":"healthy"' ]; then
            echo "✅ Health check passed!"
        else
            echo "⚠️  Health check failed - please verify deployment"
        fi
    else
        echo "❌ Could not retrieve application URL"
    fi
else
    echo "⚠️  Azure CLI not found. Docker image built successfully."
    echo "🐳 Local image: $IMAGE_NAME:$TAG"
    echo ""
    echo "To deploy manually:"
    echo "1. Push to your container registry"
    echo "2. Deploy using Azure portal or other deployment method"
fi

# Step 4: Local deployment option
echo ""
echo "🖥️  For local deployment:"
echo "docker run -p 8000:8000 -e ENVIRONMENT=production $IMAGE_NAME:$TAG"
echo ""
echo "🎉 Deployment script completed!"
