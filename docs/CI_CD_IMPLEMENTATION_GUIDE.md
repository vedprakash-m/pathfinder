# Pathfinder CI/CD Implementation Guide

## Overview

This guide walks you through implementing the complete CI/CD pipeline for Pathfinder, from initial setup to advanced features. We'll start with the simple pipeline and then evolve it with advanced capabilities.

## Quick Start

### 1. Run the Automated Setup Script

```bash
# Navigate to the project root
cd pathfinder

# Run the setup script
./scripts/setup-ci-cd.sh
```

This script will:
- ✅ Check prerequisites (Azure CLI, jq)
- 🔐 Create Azure service principal
- 📝 Generate GitHub secrets template
- 🚀 Optionally set up GitHub secrets (if GitHub CLI is available)

### 2. Verify Your Current Setup

Check if you already have the required secrets by looking at your current production deployment:

```bash
# Check current Azure resources
az group list --query "[?contains(name, 'pathfinder')].{Name:name, Location:location}" --output table

# Check current Container Apps
az containerapp list --resource-group rg-pathfinder-prod --output table
```

Based on PROJECT_METADATA.md, you already have:
- **Frontend**: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/
- **Backend**: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/
- **Auth0 Domain**: dev-jwnud3v8ghqnyygr.us.auth0.com

## Phase 1: Simple Pipeline Implementation

### Step 1: Enable the Simple Pipeline

1. **Rename the current workflow** (backup):
   ```bash
   mv .github/workflows/ci-cd-pipeline.yml .github/workflows/ci-cd-pipeline-backup.yml
   ```

2. **Activate the simple pipeline**:
   ```bash
   mv .github/workflows/ci-cd-simple.yml .github/workflows/ci-cd-pipeline.yml
   ```

3. **Commit and push to test**:
   ```bash
   git add .github/workflows/
   git commit -m "feat: implement simple CI/CD pipeline"
   git push origin develop  # Test on develop first
   ```

### Step 2: Required GitHub Secrets

Set these secrets in your GitHub repository (Settings > Secrets and variables > Actions):

#### Essential Secrets (You likely already have these)
```bash
# Azure Authentication
AZURE_CREDENTIALS          # Service principal JSON
AZURE_SUBSCRIPTION_ID       # Your Azure subscription ID

# Database (from your current deployment)
SQL_ADMIN_LOGIN            # Current SQL admin username
SQL_ADMIN_PASSWORD         # Current SQL admin password

# APIs (from your current deployment)
OPENAI_API_KEY             # Your existing OpenAI key

# Auth0 (from your current deployment)
AUTH0_DOMAIN               # dev-jwnud3v8ghqnyygr.us.auth0.com
AUTH0_AUDIENCE             # Your API audience
AUTH0_CLIENT_ID            # Your client ID for frontend
```

#### Auto-Generated Secrets (Get these from Azure)
```bash
# Get these from your existing deployment
az cosmosdb keys list --name pathfinder-cosmos-prod --resource-group rg-pathfinder-prod --type keys
az sql db show-connection-string --server pathfinder-sql-prod --name pathfinder-db-prod --client ado.net

# Then set:
AZURE_COSMOS_ENDPOINT       # Your Cosmos DB endpoint
AZURE_COSMOS_KEY           # Primary key from above command
SQL_CONNECTION_STRING      # Connection string from above command
```

### Step 3: Test the Simple Pipeline

1. **Push to develop branch**:
   ```bash
   git checkout develop
   # Make a small change
   echo "# CI/CD Pipeline Implemented" >> README.md
   git add README.md
   git commit -m "test: trigger CI/CD pipeline on develop"
   git push origin develop
   ```

2. **Check GitHub Actions**:
   - Go to your GitHub repository
   - Click "Actions" tab
   - Watch the "Pathfinder CI/CD - Simple" workflow run
   - Verify that quality checks pass

3. **Deploy to production**:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

   This will trigger the full deployment pipeline.

## Phase 2: Enhanced Pipeline Implementation

### Step 1: Enable Advanced Features

Once the simple pipeline is working, upgrade to the enhanced version:

```bash
# Backup the simple pipeline
mv .github/workflows/ci-cd-pipeline.yml .github/workflows/ci-cd-simple-backup.yml

# Activate the enhanced pipeline
mv .github/workflows/ci-cd-enhanced.yml .github/workflows/ci-cd-pipeline.yml

# Commit the change
git add .github/workflows/
git commit -m "feat: upgrade to enhanced CI/CD pipeline with multi-environment support"
git push origin develop
```

### Step 2: Enhanced Features Overview

The enhanced pipeline adds:

#### 🌍 Multi-Environment Support
- **dev**: Development environment (PRs and feature branches)
- **staging**: Staging environment (develop branch)
- **prod**: Production environment (main branch)
- **preview-***: Preview environments (feature branches)

#### 🔍 Advanced Quality Checks
- Parallel execution of frontend and backend quality checks
- Security scanning with Trivy and CodeQL
- Advanced caching for dependencies and build artifacts
- Retry logic for network-dependent operations

#### 🚀 Deployment Features
- Branch-based deployment rules
- Blue/green deployment strategy with rollback
- Comprehensive health checks
- Performance baseline monitoring
- Automatic rollback on health check failures

#### 📊 Enhanced Monitoring
- Detailed deployment summaries
- Performance metrics collection
- Resource usage tracking
- Automatic cleanup of preview environments

### Step 3: Test Enhanced Features

#### Manual Deployment to Different Environments
```bash
# Deploy to staging manually
gh workflow run "Pathfinder CI/CD - Enhanced" --field environment=staging

# Deploy to dev manually  
gh workflow run "Pathfinder CI/CD - Enhanced" --field environment=dev
```

#### Feature Branch Preview Environments
```bash
# Create a feature branch
git checkout -b feature/test-preview-deployment
echo "# Testing preview deployment" >> README.md
git add README.md
git commit -m "feat: test preview environment deployment"
git push origin feature/test-preview-deployment
```

This will create a preview environment: `preview-test-preview-deployment`

#### Test Rollback Functionality
```bash
# Trigger a rollback manually
gh workflow run "Pathfinder CI/CD - Enhanced" --field rollback=true --field environment=staging
```

## Advanced Configuration

### Azure Key Vault Integration

For enhanced security, integrate with Azure Key Vault:

```bash
# Create Key Vault (if not exists)
az keyvault create \
  --name pathfinder-kv-prod \
  --resource-group rg-pathfinder-prod \
  --location eastus

# Add secrets to Key Vault
az keyvault secret set --vault-name pathfinder-kv-prod --name openai-api-key --value "your-key"
az keyvault secret set --vault-name pathfinder-kv-prod --name auth0-client-secret --value "your-secret"
```

### Performance Testing Integration

Add performance testing to the pipeline:

```bash
# Create performance test configuration
mkdir -p .github/performance
cat > .github/performance/load-test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  let response = http.get(`${__ENV.BASE_URL}/health`);
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
EOF
```

### Notification Integration

Add Slack/Teams notifications:

```yaml
# Add to the notify job in the enhanced pipeline
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    channel: '#pathfinder-deployments'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Migration from Existing Deployment

### Step 1: Backup Current Configuration

```bash
# Export current Container App configuration
az containerapp show --name pathfinder-backend-prod --resource-group rg-pathfinder-prod > current-backend-config.json
az containerapp show --name pathfinder-frontend-prod --resource-group rg-pathfinder-prod > current-frontend-config.json

# Export environment variables
az containerapp show --name pathfinder-backend-prod --resource-group rg-pathfinder-prod \
  --query "properties.configuration.secrets" > current-secrets.json
```

### Step 2: Migrate Environment Variables

Extract current environment variables and add them to GitHub Secrets:

```bash
# Get current environment variables
az containerapp show --name pathfinder-backend-prod --resource-group rg-pathfinder-prod \
  --query "properties.template.containers[0].env" --output table

# Use these values to set up GitHub secrets
```

### Step 3: Test Migration

1. **Deploy to staging first**:
   ```bash
   git checkout develop
   git push origin develop  # This will deploy to staging
   ```

2. **Verify staging deployment**:
   ```bash
   curl https://pathfinder-backend-staging.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health
   ```

3. **Deploy to production**:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Failures
```bash
# Verify service principal permissions
az role assignment list --assignee "your-sp-object-id" --output table

# Recreate service principal if needed
az ad sp delete --id "your-sp-object-id"
./scripts/setup-ci-cd.sh
```

#### 2. Build Failures
```bash
# Check Docker build locally
docker build -t pathfinder-backend:test ./backend
docker build -t pathfinder-frontend:test ./frontend

# Test locally
docker run -p 8000:8000 pathfinder-backend:test
docker run -p 3000:80 pathfinder-frontend:test
```

#### 3. Deployment Failures
```bash
# Check Azure deployment status
az deployment group list --resource-group rg-pathfinder-prod --output table

# Check Container App logs
az containerapp logs show --name pathfinder-backend-prod --resource-group rg-pathfinder-prod
```

#### 4. Health Check Failures
```bash
# Manual health check
curl -v https://pathfinder-backend-prod.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health

# Check application logs
az containerapp logs tail --name pathfinder-backend-prod --resource-group rg-pathfinder-prod
```

### Pipeline Debugging

Enable debug logging in GitHub Actions:

```bash
# Set repository secret for debug logging
gh secret set ACTIONS_STEP_DEBUG --body "true"
gh secret set ACTIONS_RUNNER_DEBUG --body "true"
```

### Resource Monitoring

Monitor Azure resource usage:

```bash
# Check resource group costs
az consumption usage list --resource-group rg-pathfinder-prod

# Monitor Container App metrics
az monitor metrics list --resource-type "Microsoft.App/containerApps" \
  --resource pathfinder-backend-prod --resource-group rg-pathfinder-prod
```

## Cost Optimization

### Azure Resource Optimization

1. **Use Basic tiers for non-production**:
   - SQL Database: Basic tier for dev/staging
   - Cosmos DB: Autoscale for production, manual for dev/staging
   - Container Apps: Scale to zero for preview environments

2. **Set up cost alerts**:
   ```bash
   az consumption budget create \
     --resource-group rg-pathfinder-prod \
     --budget-name pathfinder-monthly-budget \
     --amount 100 \
     --time-grain Monthly
   ```

### GitHub Actions Optimization

1. **Use change detection** to skip unnecessary builds
2. **Cache dependencies** aggressively
3. **Use self-hosted runners** for heavy workloads (if cost-effective)

## Security Best Practices

### Secret Management
- Rotate secrets every 90 days
- Use Azure Key Vault for production secrets
- Enable secret scanning in GitHub repository
- Monitor secret usage and access

### Access Control
- Limit GitHub repository access
- Use branch protection rules
- Require code reviews for main branch
- Enable dependency vulnerability alerts

### Compliance
- Enable audit logging for all Azure resources
- Set up compliance monitoring
- Regular security assessments
- Monitor for unusual deployment patterns

## Next Steps

After implementing the CI/CD pipeline:

1. **Monitor and optimize** pipeline performance
2. **Add integration tests** for critical user journeys
3. **Implement blue/green deployments** for zero-downtime updates
4. **Set up monitoring dashboards** for pipeline metrics
5. **Plan for disaster recovery** and backup strategies

## Resources

- 📚 [Pipeline Documentation](CI_CD_PIPELINE.md)
- 🔧 [Setup Script](../scripts/setup-ci-cd.sh)
- 🏗️ [PROJECT_METADATA.md](PROJECT_METADATA.md)
- 🌐 [Azure Container Apps Documentation](https://docs.microsoft.com/azure/container-apps/)
- 🔄 [GitHub Actions Documentation](https://docs.github.com/actions) 