#!/bin/bash

# Pathfinder Production Completion Script
# Builds and deploys actual application containers and configures production environment

set -e

echo "🚀 Completing Pathfinder Production Deployment"
echo "=============================================="

# Configuration
APP_NAME="pathfinder"
RESOURCE_GROUP="${APP_NAME}-rg"
REGISTRY_NAME="pathfinderdevregistry"
REGISTRY_SERVER="${REGISTRY_NAME}.azurecr.io"

# Get deployment outputs
echo "📋 Retrieving deployment configuration..."
BACKEND_URL=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "${APP_NAME}-backend" --query "properties.configuration.ingress.fqdn" -o tsv)
FRONTEND_URL=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "${APP_NAME}-frontend" --query "properties.configuration.ingress.fqdn" -o tsv)

echo "✅ Current URLs:"
echo "Backend:  https://$BACKEND_URL"
echo "Frontend: https://$FRONTEND_URL"
echo ""

# Step 1: Login to Azure Container Registry
echo "🔐 Logging into Azure Container Registry..."
az acr login --name "$REGISTRY_NAME"
echo "✅ ACR login successful"

# Step 2: Build Backend Container
echo "🏗️ Building backend container..."
cd backend

# Create production Dockerfile if it doesn't exist
if [ ! -f "Dockerfile.prod" ]; then
    echo "📝 Creating production Dockerfile..."
    cat > Dockerfile.prod << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
EOF
fi

# Build and push backend image
BACKEND_IMAGE="${REGISTRY_SERVER}/${APP_NAME}-backend:latest"
echo "Building: $BACKEND_IMAGE"
docker build -t "$BACKEND_IMAGE" -f Dockerfile.prod .
docker push "$BACKEND_IMAGE"
echo "✅ Backend image built and pushed"

cd ..

# Step 3: Build Frontend Container
echo "🏗️ Building frontend container..."
cd frontend

# Create production Dockerfile if it doesn't exist  
if [ ! -f "Dockerfile.prod" ]; then
    echo "📝 Creating production Dockerfile..."
    cat > Dockerfile.prod << 'EOF'
# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
EOF
fi

# Create nginx configuration if it doesn't exist
if [ ! -f "nginx.conf" ]; then
    echo "📝 Creating nginx configuration..."
    cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/javascript
        application/json;

    # Handle SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy to backend
    location /api/ {
        proxy_pass https://${BACKEND_URL}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy for real-time features
    location /ws/ {
        proxy_pass https://${BACKEND_URL}/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
fi

# Build and push frontend image
FRONTEND_IMAGE="${REGISTRY_SERVER}/${APP_NAME}-frontend:latest"
echo "Building: $FRONTEND_IMAGE"
docker build -t "$FRONTEND_IMAGE" -f Dockerfile.prod .
docker push "$FRONTEND_IMAGE"
echo "✅ Frontend image built and pushed"

cd ..

# Step 4: Update Container Apps with new images
echo "🚀 Updating container apps with new images..."

# Update backend container app
echo "Updating backend container app..."
az containerapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "${APP_NAME}-backend" \
    --image "$BACKEND_IMAGE" \
    --set-env-vars \
        "ENVIRONMENT=production" \
        "DATABASE_URL=@microsoft.keyvault(secreturi=https://pf-kv-$(az group show --name $RESOURCE_GROUP --query 'tags.uniqueString' -o tsv).vault.azure.net/secrets/database-url)" \
        "OPENAI_API_KEY=@microsoft.keyvault(secreturi=https://pf-kv-$(az group show --name $RESOURCE_GROUP --query 'tags.uniqueString' -o tsv).vault.azure.net/secrets/openai-api-key)" \
        "ENTRA_TENANT_ID=@microsoft.keyvault(secreturi=https://pf-kv-$(az group show --name $RESOURCE_GROUP --query 'tags.uniqueString' -o tsv).vault.azure.net/secrets/entra-tenant-id)" \
        "ENTRA_CLIENT_ID=@microsoft.keyvault(secreturi=https://pf-kv-$(az group show --name $RESOURCE_GROUP --query 'tags.uniqueString' -o tsv).vault.azure.net/secrets/entra-client-id)"

echo "✅ Backend container app updated"

# Update frontend container app
echo "Updating frontend container app..."
az containerapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "${APP_NAME}-frontend" \
    --image "$FRONTEND_IMAGE"

echo "✅ Frontend container app updated"

# Step 5: Wait for deployment to complete
echo "⏳ Waiting for containers to restart..."
sleep 60

# Step 6: Validate deployment
echo "🔍 Validating deployment..."

# Check backend health
echo "Checking backend health..."
BACKEND_HEALTH_URL="https://$BACKEND_URL/health"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_HEALTH_URL" || echo "000")

if [ "$BACKEND_STATUS" = "200" ]; then
    echo "✅ Backend health check passed"
else
    echo "⚠️ Backend health check failed (Status: $BACKEND_STATUS)"
    echo "Backend URL: $BACKEND_HEALTH_URL"
fi

# Check frontend
echo "Checking frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$FRONTEND_URL" || echo "000")

if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend check passed"
else
    echo "⚠️ Frontend check failed (Status: $FRONTEND_STATUS)"
    echo "Frontend URL: https://$FRONTEND_URL"
fi

# Step 7: Display final results
echo ""
echo "🎉 Production Deployment Completed!"
echo "================================="
echo ""
echo "🌐 Application URLs:"
echo "Frontend: https://$FRONTEND_URL"
echo "Backend:  https://$BACKEND_URL"
echo "API Docs: https://$BACKEND_URL/docs"
echo ""
echo "📋 Next Steps:"
echo "1. Update Microsoft Entra External ID app registration:"
echo "   - Redirect URI: https://$FRONTEND_URL/auth/callback"
echo "   - Single-page application: https://$FRONTEND_URL"
echo ""
echo "2. Configure production secrets in Azure Key Vault:"
echo "   - OpenAI API Key"
echo "   - Entra Client ID and Tenant ID"
echo "   - Database connection string"
echo ""
echo "3. Test the application:"
echo "   - Visit: https://$FRONTEND_URL"
echo "   - Check API: https://$BACKEND_URL/docs"
echo ""
echo "💰 Deployment Status:"
echo "Architecture: Single Resource Group (cost-optimized)"
echo "Auto-scaling: 0-3 instances"
echo "Estimated cost: \$50-75/month"
echo ""
