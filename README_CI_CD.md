# Pathfinder CI/CD Pipeline - Solo Developer Edition

**🎯 Optimized for single developer with cost-conscious Azure deployment**

## Overview

This CI/CD pipeline is designed for solo developers who want automation benefits without the cost overhead of multiple environments. It provides quality assurance while deploying directly to production.

## 🚀 Pipeline Flow

```
Push to Main → Quality Checks → Deploy to Production → Health Check
```

### What Happens:
1. **Quality Checks**: Linting, testing, type checking (prevents bad code)
2. **Direct Deploy**: Updates your existing Azure Container Apps
3. **Health Check**: Ensures deployment succeeded
4. **Emergency Deploy**: Skip tests option for hotfixes

## 💰 Cost Optimization

- **Single Environment**: Uses your existing `pathfinder-rg-dev` resources
- **No Staging**: Saves ~70% on infrastructure costs
- **Redis-Free Architecture**: SQLite + in-memory cache saves $40/month vs Redis
- **Smart Caching**: Reduces build times and GitHub Actions minutes
- **Direct Updates**: Fast deployments without rebuilding containers
- **Total Savings**: ~$70-90/month vs enterprise multi-environment setup

## 📋 Simplified Workflow

### Branch Strategy:
```
main (production) ← You work here
├── feature/quick-fix (optional, for experimentation)
└── hotfix/* (emergency fixes)
```

### Daily Workflow:
1. Work directly on `main` branch (you're the only developer)
2. Commit and push changes
3. Pipeline automatically runs quality checks
4. If quality checks pass → auto-deploy to production
5. Check your live app at existing URLs

## 🔧 Configuration

### GitHub Secrets (Already Set):
- `AZURE_CREDENTIALS`: Service principal for Azure deployment
- `AZURE_SUBSCRIPTION_ID`: Your Azure subscription
- All your API keys and configuration

### Environment Variables:
- Uses your existing `pathfinder-rg-dev` resource group
- Deploys to your current Container Apps
- Maintains all existing functionality

## 🚨 Emergency Procedures

### Quick Deploy (Skip Tests):
1. Go to GitHub Actions tab
2. Click "Run workflow" on "Pathfinder CI/CD - Solo"
3. Check "Skip quality checks" box
4. Click "Run workflow"

### Rollback:
```bash
# Simple rollback via Azure CLI
az containerapp revision list --name pathfinder-backend --resource-group pathfinder-rg-dev
az containerapp revision activate --name pathfinder-backend --resource-group pathfinder-rg-dev --revision [previous-revision]
```

## 📊 Monitoring

### Check Pipeline Status:
- GitHub Actions tab shows all runs
- Green checkmark = successful deployment
- Red X = fix needed before deployment

### Check Live App:
- **Frontend**: https://pathfinder-frontend.yellowdune-9b8d769a.eastus.azurecontainerapps.io
- **Backend**: https://pathfinder-backend.yellowdune-9b8d769a.eastus.azurecontainerapps.io/health

## 🏗️ When to Add Complexity

**Keep it simple until you need:**
- Multiple developers (then add staging)
- Preview environments (then add feature branch deployments)
- Blue/green deployments (then add advanced pipeline)

**Current approach is perfect for:**
- Solo development
- Cost optimization
- Fast iteration
- Learning and experimentation

## 🎯 Benefits vs Traditional Multi-Environment

| Traditional | Solo Optimized |
|-------------|----------------|
| 3+ environments | 1 environment |
| Complex branching | Simple workflow |
| Higher costs | ~70% cost savings |
| Slower deploys | Fast direct updates |
| Over-engineering | Right-sized for needs |

## 🚀 Quick Start

1. **Push to main** → Pipeline runs automatically
2. **Check GitHub Actions** → See pipeline status
3. **Visit your app** → Verify deployment
4. **Iterate fast** → Quality checks prevent issues

Perfect for your hobby project needs while maintaining professional CI/CD practices! 🎉 