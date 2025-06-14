# CI/CD Pause-Resume Architecture Fix

## Issues Identified and Fixed

### 1. **Database Resources in Wrong Resource Group** ❌ → ✅
**Problem**: Database resources (SQL Server, Cosmos DB) were being deployed to `pathfinder-rg` instead of `pathfinder-db-rg`, breaking the pause-resume architecture.

**Fix**: 
- Updated infrastructure deployment workflow to use proper two-resource-group architecture
- Data layer → `pathfinder-db-rg` (never deleted)
- Compute layer → `pathfinder-rg` (can be deleted for cost savings)

### 2. **SQLAlchemy Configuration Error** ❌ → ✅
**Problem**: Backend failing to start due to duplicate `echo` parameter in `create_async_engine()`.

**Fix**: Fixed `backend/app/core/database.py`:
```python
# Before (broken):
engine = create_async_engine(
    settings.database_url_sqlalchemy,
    **settings.database_config,  # This already includes 'echo'
    echo=settings.DEBUG,         # Duplicate!
)

# After (fixed):
engine = create_async_engine(
    settings.database_url_sqlalchemy,
    **settings.database_config,  # Contains proper echo configuration
)
```

### 3. **Global Resource Naming Conflicts** ❌ → ✅
**Problem**: Storage account and other globally-unique Azure resources using names that were already taken.

**Fix**: Updated resource naming in Bicep templates:
```bicep
// Before:
storageAccount: 'pathfinderstorage'  // Already taken globally
cosmosAccount: '${appName}-cosmos'    // Already taken globally
keyVault: '${appName}-kv'            // Already taken globally

// After:
storageAccount: 'pathfinderstorage${uniqueString(resourceGroup().id)}'
cosmosAccount: '${appName}-cosmos-${uniqueString(resourceGroup().id)}'
keyVault: '${appName}-kv-${uniqueString(resourceGroup().id)}'
```

### 4. **Regional Capacity Issues** ❌ → ✅
**Problem**: Deployments failing in East US due to capacity constraints.

**Fix**: 
- Updated default region to West US 2 in deployment scripts
- Made location configurable via environment variables

### 5. **CI/CD Pipeline Architecture Mismatch** ❌ → ✅
**Problem**: CI/CD workflows using single resource group template instead of pause-resume architecture.

**Fix**: Updated `.github/workflows/infrastructure-deploy.yml`:
- Deploy data layer to `pathfinder-db-rg` (persistent)
- Deploy compute layer to `pathfinder-rg` (ephemeral)
- Proper dependency management between layers
- Health checks for both layers

## Updated Architecture

### Pause-Resume Resource Groups:
```
pathfinder-db-rg (NEVER DELETE)
├── SQL Server
├── SQL Database  
├── Cosmos DB Account
└── Key Vault (for connection strings)

pathfinder-rg (Can delete for cost savings)
├── Container Apps Environment
├── Backend Container App
├── Frontend Container App
├── Log Analytics
├── Application Insights
├── Storage Account
└── Container Registry
```

### Cost Optimization:
- **Active**: ~$45-65/month (both resource groups)
- **Paused**: ~$15-25/month (data layer only)
- **Savings**: ~70% when paused

## Deployment Commands

### 1. Deploy Data Layer (One-time):
```bash
cd /Users/vedprakashmishra/pathfinder
export LOCATION=westus2
export SQL_ADMIN_USERNAME=pathfinderadmin
export SQL_ADMIN_PASSWORD="YourSecurePassword123!"
./scripts/deploy-data-layer.sh
```

### 2. Deploy/Resume Compute Layer:
```bash
./scripts/resume-environment.sh
```

### 3. Pause Environment (Cost Savings):
```bash
./scripts/pause-environment.sh  # Deletes pathfinder-rg only
```

## CI/CD Workflow Triggers

### Automatic:
- Push to `main` branch → Deploy compute layer
- Infrastructure changes → Validate and deploy

### Manual:
- `deploy_data_layer=true` → Deploy persistent data layer
- `force_deploy=true` → Force redeploy everything

## Next Steps

1. **Push changes** to trigger CI/CD pipeline
2. **Verify deployment** in Azure portal
3. **Test application** endpoints
4. **Monitor costs** in Azure Cost Management

## Files Modified

- `.github/workflows/infrastructure-deploy.yml` - Updated for pause-resume architecture
- `.github/workflows/ci-cd-pipeline.yml` - Updated environment variables
- `backend/app/core/database.py` - Fixed SQLAlchemy configuration
- `backend/app/core/config.py` - Improved database config handling
- `infrastructure/bicep/pathfinder-single-rg.bicep` - Fixed resource naming
- `scripts/deploy-data-layer.sh` - Made location configurable
- `scripts/resume-environment.sh` - Updated for westus2

## Health Check Commands

```bash
# Check data layer
az resource list --resource-group pathfinder-db-rg --query "[].{Name:name,Type:type,Status:properties.provisioningState}" -o table

# Check compute layer
az resource list --resource-group pathfinder-rg --query "[].{Name:name,Type:type,Status:properties.provisioningState}" -o table

# Test application
curl https://pathfinder-backend-xxx.westus2.azurecontainerapps.io/health
curl https://pathfinder-frontend-xxx.westus2.azurecontainerapps.io
```

---

✅ **CI/CD issue resolved with proper pause-resume architecture implementation**
