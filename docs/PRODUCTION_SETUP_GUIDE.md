# Production Deployment Guide

## 🚀 Phase 1 MVP Production Setup

This guide will help you complete the remaining 15% to achieve full Phase 1 MVP compliance with the North Star specification.

## Current Status ✅

**Infrastructure**: ✅ COMPLETE  
**Application**: ✅ DEPLOYED  
**Core Services**: ⚠️ NEEDS CONFIGURATION  

Live URLs:
- Frontend: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/
- Backend: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/

## 🎯 Next Steps to Complete Phase 1

### Priority 1: Configure Production Services (Critical)

#### 1. Set up Auth0 (User Authentication)
```bash
# 1. Create Auth0 account at https://auth0.com
# 2. Create a new application (Single Page Application)
# 3. Get the following values:
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=https://pathfinder-api.com

# 4. Configure allowed callback URLs:
# - https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/callback
# - https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/

# 5. Configure allowed logout URLs:
# - https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/
```

#### 2. Set up OpenAI API (AI Trip Planning)
```bash
# 1. Create OpenAI account at https://platform.openai.com
# 2. Generate API key
# 3. Set usage limits to control costs
OPENAI_API_KEY=sk-your-openai-api-key
AI_DAILY_BUDGET_LIMIT=50.00
```

#### 3. Set up SendGrid (Email Notifications)
```bash
# 1. Create SendGrid account at https://sendgrid.com
# 2. Generate API key
# 3. Verify sender email
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
```

#### 4. Set up Google Maps API (Location Services)
```bash
# 1. Go to Google Cloud Console
# 2. Enable Maps JavaScript API, Places API, Geocoding API
# 3. Generate API key with appropriate restrictions
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### Priority 2: Update Container Apps Configuration

#### Update Backend Environment Variables
```bash
# Use Azure CLI or Azure Portal to set environment variables
az containerapp update \
  --name pathfinder-backend \
  --resource-group pathfinder-rg-dev \
  --set-env-vars \
    "SECRET_KEY=your-production-secret-key" \
    "AUTH0_DOMAIN=your-tenant.auth0.com" \
    "AUTH0_CLIENT_ID=your-client-id" \
    "AUTH0_CLIENT_SECRET=your-client-secret" \
    "AUTH0_AUDIENCE=https://pathfinder-api.com" \
    "OPENAI_API_KEY=sk-your-openai-api-key" \
    "GOOGLE_MAPS_API_KEY=your-google-maps-api-key" \
    "SENDGRID_API_KEY=your-sendgrid-api-key" \
    "ENVIRONMENT=production" \
    "DEBUG=false"
```

#### Update Frontend Environment Variables
```bash
az containerapp update \
  --name pathfinder-frontend \
  --resource-group pathfinder-rg-dev \
  --set-env-vars \
    "VITE_AUTH0_DOMAIN=your-tenant.auth0.com" \
    "VITE_AUTH0_CLIENT_ID=your-client-id" \
    "VITE_AUTH0_AUDIENCE=https://pathfinder-api.com" \
    "VITE_API_BASE_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
    "VITE_GOOGLE_MAPS_API_KEY=your-google-maps-api-key"
```

### Priority 3: Deploy Production Database

#### Option A: Use Azure SQL Database (Recommended)
```bash
# 1. Create Azure SQL Database
az sql server create \
  --name pathfinder-sql-server \
  --resource-group pathfinder-rg-dev \
  --location eastus \
  --admin-user pathfinder-admin \
  --admin-password "YourSecurePassword123!"

az sql db create \
  --server pathfinder-sql-server \
  --resource-group pathfinder-rg-dev \
  --name pathfinder-db \
  --service-objective Basic

# 2. Update DATABASE_URL
DATABASE_URL=postgresql+asyncpg://pathfinder-admin:YourSecurePassword123!@pathfinder-sql-server.database.windows.net:1433/pathfinder-db
```

#### Option B: Use Azure Database for PostgreSQL
```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --name pathfinder-postgres \
  --resource-group pathfinder-rg-dev \
  --location eastus \
  --admin-user pathfinder \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 14

# Create database
az postgres flexible-server db create \
  --server-name pathfinder-postgres \
  --resource-group pathfinder-rg-dev \
  --database-name pathfinder
```

### Priority 4: Test Complete User Workflow

#### 4.1 Test Authentication
1. Visit the frontend URL
2. Click "Sign In" 
3. Verify Auth0 login flow works
4. Check user profile creation

#### 4.2 Test Family Management
1. Create a new family
2. Invite family members
3. Verify email invitations work

#### 4.3 Test Trip Planning
1. Create a new trip
2. Add family members to trip
3. Generate AI itinerary
4. Verify itinerary generation works

#### 4.4 Test Core Features
1. Real-time chat in trip
2. Expense tracking
3. PDF export functionality
4. Mobile responsiveness

## 🔧 Quick Start Script

Create a script to automate the environment setup:

```bash
#!/bin/bash
# production-setup.sh

echo "🚀 Pathfinder Production Setup"
echo "================================"

# Check if required tools are installed
command -v az >/dev/null 2>&1 || { echo "Azure CLI is required but not installed."; exit 1; }

# Set variables (you'll need to fill these in)
RESOURCE_GROUP="pathfinder-rg-dev"
BACKEND_APP="pathfinder-backend"
FRONTEND_APP="pathfinder-frontend"

# Read configuration from user
read -p "Enter Auth0 Domain: " AUTH0_DOMAIN
read -p "Enter Auth0 Client ID: " AUTH0_CLIENT_ID
read -s -p "Enter Auth0 Client Secret: " AUTH0_CLIENT_SECRET
echo
read -s -p "Enter OpenAI API Key: " OPENAI_API_KEY
echo
read -s -p "Enter Google Maps API Key: " GOOGLE_MAPS_API_KEY
echo
read -s -p "Enter SendGrid API Key: " SENDGRID_API_KEY
echo
read -s -p "Enter Production Secret Key: " SECRET_KEY
echo

echo "🔧 Updating backend configuration..."
az containerapp update \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    "SECRET_KEY=$SECRET_KEY" \
    "AUTH0_DOMAIN=$AUTH0_DOMAIN" \
    "AUTH0_CLIENT_ID=$AUTH0_CLIENT_ID" \
    "AUTH0_CLIENT_SECRET=$AUTH0_CLIENT_SECRET" \
    "AUTH0_AUDIENCE=https://pathfinder-api.com" \
    "OPENAI_API_KEY=$OPENAI_API_KEY" \
    "GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY" \
    "SENDGRID_API_KEY=$SENDGRID_API_KEY" \
    "ENVIRONMENT=production" \
    "DEBUG=false" \
    "AI_DAILY_BUDGET_LIMIT=50.0"

echo "🔧 Updating frontend configuration..."
az containerapp update \
  --name $FRONTEND_APP \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    "VITE_AUTH0_DOMAIN=$AUTH0_DOMAIN" \
    "VITE_AUTH0_CLIENT_ID=$AUTH0_CLIENT_ID" \
    "VITE_AUTH0_AUDIENCE=https://pathfinder-api.com" \
    "VITE_API_BASE_URL=https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io" \
    "VITE_GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY"

echo "✅ Production setup complete!"
echo "🌐 Frontend: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo "🔧 Backend: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/"
echo ""
echo "Next steps:"
echo "1. Test authentication workflow"
echo "2. Create a test family and trip"
echo "3. Verify AI itinerary generation"
echo "4. Test end-to-end user journey"
```

## 📊 Success Metrics

After completing the setup, verify these work:
- [ ] User registration and login via Auth0
- [ ] Family creation and invitations
- [ ] Trip creation with multiple families
- [ ] AI-powered itinerary generation
- [ ] Real-time chat and notifications
- [ ] PDF export functionality
- [ ] Mobile responsive design

## 🚨 Security Checklist

- [ ] All API keys are stored as environment variables
- [ ] Secret keys are properly generated and secure
- [ ] CORS is configured for production domains only
- [ ] Rate limiting is enabled
- [ ] HTTPS is enforced everywhere
- [ ] Database connections are encrypted

## 📞 Support

If you encounter issues during setup:
1. Check the application logs in Azure Container Apps
2. Verify environment variables are set correctly
3. Test each service individually
4. Review the troubleshooting section in the documentation

**Current Status**: Infrastructure is deployed and working. Only service configuration is needed to achieve full Phase 1 MVP functionality.
