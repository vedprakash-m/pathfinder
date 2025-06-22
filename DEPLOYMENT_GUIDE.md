# Pathfinder Deployment Guide - Microsoft Entra External ID

**Post-Migration Deployment Guide**  
**Updated:** December 22, 2024  
**Authentication System:** Microsoft Entra External ID  

---

## 🎯 Overview

This guide covers the complete deployment process for Pathfinder after the successful Auth0 → Microsoft Entra External ID migration. The application now uses simplified authentication with only 3 environment variables instead of 6.

## 📋 Prerequisites

### Required Tools
- Azure CLI (latest version)
- Docker Desktop 
- Git (for deployment)
- GitHub account with repository access

### Required Azure Subscriptions
- Azure subscription with sufficient credits
- Permission to create resource groups and deploy resources

### GitHub Repository Secrets (Required)
```bash
# Core Azure Configuration
AZURE_CREDENTIALS          # Service principal JSON for deployment
SQL_ADMIN_USERNAME         # Database admin username  
SQL_ADMIN_PASSWORD         # Database admin password (strong password)

# New Authentication System (Microsoft Entra External ID)
ENTRA_EXTERNAL_TENANT_ID   # Your Entra External ID tenant ID
ENTRA_EXTERNAL_CLIENT_ID   # Your Entra External ID application client ID

# Optional Services
OPENAI_API_KEY            # OpenAI API key (optional, has fallbacks)
LLM_ORCHESTRATION_URL     # LLM service URL (optional)
LLM_ORCHESTRATION_API_KEY # LLM service API key (optional)
```

---

## 🚀 Phase 1: Azure Entra External ID Setup

### Step 1: Create Microsoft Entra External ID Tenant

1. **Navigate to Azure Portal**
   ```bash
   https://portal.azure.com
   ```

2. **Create External ID Tenant**
   - Go to "Microsoft Entra ID" 
   - Click "Manage tenants" → "Create tenant"
   - Choose "External ID (for customers)" 
   - Follow the setup wizard

3. **Configure Your External ID Tenant**
   - **Tenant Name**: `pathfinder-external-id` (or your preference)
   - **Domain**: Your custom domain (optional) or use default `.onmicrosoft.com`
   - **Region**: Choose closest to your users

### Step 2: Register Application

1. **App Registrations**
   - Navigate to your External ID tenant
   - Go to "App registrations" → "New registration"

2. **Application Details**
   ```
   Name: Pathfinder Web App
   Supported account types: Accounts in this organizational directory only
   Redirect URI: 
     - Type: Single-page application (SPA)
     - URL: http://localhost:3000 (for development)
   ```

3. **Production Redirect URIs** (Add after deployment)
   ```
   https://your-frontend-url.region.azurecontainerapps.io
   ```

4. **Note Required Values**
   ```bash
   Application (client) ID: [Copy this - needed for ENTRA_EXTERNAL_CLIENT_ID]
   Directory (tenant) ID: [Copy this - needed for ENTRA_EXTERNAL_TENANT_ID]
   ```

### Step 3: Configure Application

1. **API Permissions**
   - Add "Microsoft Graph" → "User.Read" (delegated permission)
   - Grant admin consent

2. **Authentication Settings**
   - Enable "Access tokens" and "ID tokens"
   - Configure logout URL: `https://your-frontend-url/logout`

3. **CORS Configuration** 
   - Add your frontend domain to allowed origins
   - For development: `http://localhost:3000`
   - For production: `https://your-frontend-url`

---

## 🏗️ Phase 2: Azure Infrastructure Deployment

### Step 1: GitHub Repository Secrets Setup

```bash
# In your GitHub repository, go to Settings → Secrets and variables → Actions
# Add these repository secrets:

AZURE_CREDENTIALS='{"clientId":"your-service-principal-id","clientSecret":"your-client-secret","subscriptionId":"your-subscription-id","tenantId":"your-tenant-id"}'
SQL_ADMIN_USERNAME='pathfinderadmin'
SQL_ADMIN_PASSWORD='your-strong-password-here!'
ENTRA_EXTERNAL_TENANT_ID='your-external-id-tenant-id'
ENTRA_EXTERNAL_CLIENT_ID='your-external-id-client-id'
OPENAI_API_KEY='your-openai-key-optional'
```

### Step 2: Deploy Data Layer (One-time)

The persistent data layer needs to be deployed once and is never deleted:

```bash
# Option 1: Use GitHub Actions
# Go to Actions → "Infrastructure Management" → "Run workflow"
# Select: "Deploy Data Layer"

# Option 2: Deploy locally
./scripts/deploy-data-layer.sh
```

**Expected Resources Created:**
- `pathfinder-db-rg` resource group
- Azure SQL Database (Basic tier)
- Cosmos DB (serverless)
- Storage Account (files/uploads)
- Key Vault (data layer secrets)

### Step 3: Deploy Compute Layer

Deploy the application layer (can be paused for cost savings):

```bash
# Option 1: Use GitHub Actions  
# Go to Actions → "Infrastructure Management" → "Run workflow"
# Select: "Resume Environment" 

# Option 2: Deploy locally
./scripts/resume-environment.sh
```

**Expected Resources Created:**
- `pathfinder-rg` resource group
- Container Apps Environment
- Backend Container App
- Frontend Container App
- Container Registry
- Application Insights

---

## 🔄 Phase 3: Application Deployment

### Step 1: Deploy Application Code

```bash
# Option 1: Use GitHub Actions (Recommended)
# Go to Actions → "CI/CD Pipeline" → "Run workflow"
# This will build and deploy the latest code

# Option 2: Manual deployment
git push origin main  # Triggers automatic deployment
```

### Step 2: Verify Deployment

1. **Check Application URLs**
   ```bash
   # GitHub Actions will output URLs, or get them manually:
   az containerapp show --name pathfinder-frontend --resource-group pathfinder-rg --query "properties.configuration.ingress.fqdn" -o tsv
   az containerapp show --name pathfinder-backend --resource-group pathfinder-rg --query "properties.configuration.ingress.fqdn" -o tsv
   ```

2. **Test Health Endpoints**
   ```bash
   # Backend health check
   curl https://your-backend-url/health
   
   # Expected response:
   {"status": "healthy", "timestamp": "...", "version": "..."}
   ```

3. **Test Frontend Application**
   - Navigate to frontend URL
   - Click "Login" 
   - Should redirect to Microsoft Entra External ID login
   - After login, should return to dashboard

---

## ⚙️ Phase 4: Configuration Updates

### Step 1: Update Redirect URIs

Once you have your production URLs, update the app registration:

1. **Go to Azure Portal** → External ID Tenant → App registrations → Your app
2. **Authentication** → **Redirect URIs**
3. **Add Production URLs:**
   ```
   https://your-frontend-url.region.azurecontainerapps.io
   https://your-frontend-url.region.azurecontainerapps.io/auth/callback
   ```

### Step 2: Update CORS Settings

1. **API Permissions** → **CORS Configuration** 
2. **Add Production Domains:**
   ```
   https://your-frontend-url.region.azurecontainerapps.io
   ```

### Step 3: Environment Variable Verification

Verify the deployment is using correct environment variables:

```bash
# Check backend container environment
az containerapp show --name pathfinder-backend --resource-group pathfinder-rg --query "properties.template.containers[0].env"

# Should include:
# ENTRA_EXTERNAL_TENANT_ID: your-tenant-id
# ENTRA_EXTERNAL_CLIENT_ID: your-client-id  
# ENTRA_EXTERNAL_AUTHORITY: https://your-tenant-id.ciamlogin.com/...
```

---

## 💰 Cost Management

### Pause Environment (70% cost savings)
```bash
# Using GitHub Actions
Actions → "Infrastructure Management" → "Pause Environment"

# Or locally  
./scripts/pause-environment.sh
```

**Cost Impact:**
- **Active**: $50-75/month (full functionality)
- **Paused**: $15-25/month (data preserved, compute deleted)

### Resume Environment
```bash
# Using GitHub Actions
Actions → "Infrastructure Management" → "Resume Environment"

# Or locally
./scripts/resume-environment.sh  
```

**Resume Time:** 5-10 minutes

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Verify Entra configuration
curl https://your-tenant-id.ciamlogin.com/your-tenant-id.onmicrosoft.com/.well-known/openid_configuration

# Check if redirect URIs match exactly (including trailing slashes)
```

#### 2. CORS Errors  
```bash
# Add your frontend domain to:
# 1. Entra External ID app registration CORS settings
# 2. Backend container app CORS policy (already configured)
```

#### 3. Container Startup Issues
```bash
# Check container logs
az containerapp logs show --name pathfinder-backend --resource-group pathfinder-rg --follow

# Check environment variables
az containerapp show --name pathfinder-backend --resource-group pathfinder-rg --query "properties.template.containers[0].env"
```

#### 4. Database Connection Issues
```bash
# Verify SQL server firewall rules include Azure services
az sql server firewall-rule list --server pathfinder-sql --resource-group pathfinder-db-rg
```

### Health Check Commands

```bash
# Backend health
curl https://your-backend-url/health

# Database connectivity  
curl https://your-backend-url/health/ready

# Detailed system status
curl https://your-backend-url/health/detailed
```

---

## 📊 Migration Benefits Achieved

### ✅ **Cost Savings**
- **Annual Savings**: $276+ (Auth0 $23/month → Entra 50K free MAU)
- **Infrastructure**: 70% cost reduction when paused

### ✅ **Simplified Configuration**  
- **Environment Variables**: 6 → 3 (50% reduction)
- **Setup Complexity**: Significantly reduced

### ✅ **Improved Reliability**
- **Test Reliability**: Expected 73.5% → 95%+ pass rate
- **Azure Integration**: Unified Microsoft ecosystem

### ✅ **Enhanced Security**
- **Zero Trust**: Built-in with Azure AD
- **Enterprise Features**: Conditional access, MFA, risk detection

---

## 📞 Support & Next Steps

### Production Readiness Checklist
- [ ] Entra External ID tenant configured
- [ ] Production redirect URIs added
- [ ] GitHub secrets configured
- [ ] Data layer deployed
- [ ] Compute layer deployed  
- [ ] Application code deployed
- [ ] Authentication flow tested
- [ ] Health checks passing

### Additional Configuration (Optional)
- [ ] Custom domain setup
- [ ] SSL certificate configuration
- [ ] Monitoring and alerting
- [ ] Backup and disaster recovery
- [ ] Load testing and performance optimization

### Support Resources
- **Repository**: https://github.com/vedprakashmishra/pathfinder
- **Documentation**: `docs/` directory
- **Issues**: GitHub Issues for bug reports
- **Migration Notes**: `docs/metadata.md` for complete migration history

---

**🎉 Congratulations!** Your Pathfinder application is now running with Microsoft Entra External ID authentication, providing enterprise-grade security with simplified configuration and significant cost savings. 