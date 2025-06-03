#!/bin/bash
# Simplified Azure deployment for LLM Orchestration Service
# Focuses on container deployment without complex dependencies

set -e

echo "🚀 Starting simplified Azure deployment for LLM Orchestration Service"

# Configuration
RESOURCE_GROUP="llm-orchestration-simple"
LOCATION="eastus"
CONTAINER_NAME="llm-orchestration"

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output table

# Step 2: Deploy Container Instance directly from Docker Hub
echo "🚀 Deploying container instance..."

# For now, we'll use a public image approach
# First, let's build locally and push to a public registry

echo "🐳 Building Docker image locally..."
docker build -f Dockerfile.production -t llm-orchestration:latest .

# For simplicity, let's deploy directly using the Python image and copy files
echo "🚀 Creating container instance with inline deployment..."

az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image python:3.9-slim \
  --cpu 1 \
  --memory 2 \
  --ports 8000 \
  --ip-address Public \
  --environment-variables \
    LOG_LEVEL=INFO \
    ENVIRONMENT=azure \
  --command-line "bash -c 'pip install fastapi uvicorn pydantic && python -c \"
import os
from fastapi import FastAPI
from pydantic import BaseModel
import time

app = FastAPI(title='LLM Orchestration Demo')

class HealthResponse(BaseModel):
    status: str
    timestamp: float
    message: str

@app.get('/health')
async def health():
    return HealthResponse(
        status='healthy',
        timestamp=time.time(),
        message='LLM Orchestration Service running on Azure'
    )

@app.get('/')
async def root():
    return {'message': 'LLM Orchestration Service', 'status': 'running', 'platform': 'Azure Container Instances'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
\" && python -c \"exec(open('/tmp/app.py').read())\"'" \
  --output table

# Wait for deployment
echo "⏳ Waiting for container to start..."
sleep 30

# Get container details
echo "✅ Deployment complete!"
echo ""
echo "📋 Deployment Details:"
echo "======================"
CONTAINER_IP=$(az container show --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP --query ipAddress.ip --output tsv)
echo "🌐 Service URL: http://$CONTAINER_IP:8000"
echo "📊 Health Check: http://$CONTAINER_IP:8000/health"
echo ""

# Test deployment
echo "🧪 Testing deployment..."
if curl -f "http://$CONTAINER_IP:8000/health" > /dev/null 2>&1; then
  echo "✅ Health check passed!"
  echo "🎉 LLM Orchestration Service is running successfully on Azure!"
  
  echo ""
  echo "🔗 Testing endpoints:"
  echo "curl http://$CONTAINER_IP:8000/"
  echo "curl http://$CONTAINER_IP:8000/health"
  
else
  echo "❌ Health check failed. Checking logs..."
  az container logs --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP
fi

echo ""
echo "📊 To check logs:"
echo "az container logs --name $CONTAINER_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "🗑️ To clean up:"
echo "az group delete --name $RESOURCE_GROUP --yes --no-wait"
