# Manual Deployment Steps for Pathfinder

## Prerequisites Checklist
- [ ] Azure CLI installed (`brew install azure-cli`)
- [ ] Authenticated with Azure (`az login`)
- [ ] Code changes committed and pushed to GitHub

## Step 1: Authenticate with Azure
```bash
cd /Users/vedprakashmishra/pathfinder
az login
```

## Step 2: Set Environment Variables
```bash
export LOCATION=westus2
export DATA_RG=pathfinder-db-rg
export COMPUTE_RG=pathfinder-rg
```

## Step 3: Deploy Data Layer (One-time, Persistent)
```bash
# Make script executable
chmod +x scripts/deploy-data-layer.sh

# Deploy data layer
./scripts/deploy-data-layer.sh
```

Expected output:
- Creates `pathfinder-db-rg` resource group
- Deploys SQL Server, Database, Cosmos DB, Key Vault
- Takes ~10-15 minutes

## Step 4: Deploy Compute Layer (Ephemeral)
```bash
# Make script executable
chmod +x scripts/resume-environment.sh

# Deploy compute layer
./scripts/resume-environment.sh
```

Expected output:
- Creates `pathfinder-rg` resource group
- Deploys Container Apps, App Service Plans, etc.
- Takes ~5-10 minutes

## Step 5: Verify Deployment
```bash
# Check data layer
az resource list --resource-group pathfinder-db-rg --output table

# Check compute layer
az resource list --resource-group pathfinder-rg --output table
```

## Alternative: Use GitHub Actions

### Option A: Manual Workflow Trigger
1. Go to your GitHub repository
2. Click "Actions" tab
3. Select "Deploy Infrastructure" workflow
4. Click "Run workflow"
5. Set `deploy_data_layer: true` for first run
6. Click "Run workflow"

### Option B: Automatic via Push
1. Make any small change to infrastructure files
2. Commit and push to main branch
3. GitHub Actions will automatically deploy

## Verification Commands

### Check Resource Groups
```bash
az group list --query "[?contains(name, 'pathfinder')].{Name:name, Location:location, Status:properties.provisioningState}" -o table
```

### Check Application Health
```bash
# Backend health check
curl https://pathfinder-backend-xxx.westus2.azurecontainerapps.io/health

# Frontend check
curl https://pathfinder-frontend-xxx.westus2.azurecontainerapps.io
```

### Monitor Costs
```bash
# Get cost information
az consumption usage list --top 5 --output table
```

## Troubleshooting

### If Authentication Fails
```bash
az logout
az login --use-device-code
```

### If Data Layer Deployment Fails
- Check if resource names are globally unique
- Verify subscription limits
- Check westus2 region availability

### If Compute Layer Deployment Fails
- Ensure data layer deployed successfully first
- Check container registry permissions
- Verify Bicep template syntax

### If GitHub Actions Fail
- Check repository secrets are configured
- Verify service principal permissions
- Check workflow file syntax

## Cost Management

### Current Cost (Both RGs Running)
~$45-65/month

### Paused Cost (Data Layer Only)
~$15-25/month (70% savings)

### Pause Environment
```bash
./scripts/pause-environment.sh
```

### Resume Environment
```bash
./scripts/resume-environment.sh
```

## Next Steps After Deployment

1. **Test Application Endpoints**
   - Backend API documentation: `https://<backend-url>/docs`
   - Frontend application: `https://<frontend-url>`

2. **Configure Monitoring**
   - Set up alerts in Azure Monitor
   - Configure cost alerts

3. **Set Up CI/CD Pipeline**
   - Trigger the main CI/CD pipeline by pushing code changes
   - Verify automated deployments work

4. **Document Endpoints**
   - Update documentation with actual URLs
   - Share access information with team
