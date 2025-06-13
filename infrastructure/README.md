# Pathfinder Infrastructure

This directory contains the Infrastructure as Code (IaC) templates for the Pathfinder application, optimized for solo developer deployment with **single resource group strategy** and significant cost savings.

## 🏗️ Architecture Overview

The infrastructure is designed with a **single resource group (`pathfinder-rg`) approach** that saves approximately **$60-80/month** compared to multi-environment setups, while using **Bicep exclusively** for Azure-native infrastructure management.

### Key Components

- **Single Resource Group**: All resources in `pathfinder-rg` for simplified management
- **Container Apps**: Serverless containers for backend and frontend
- **Azure SQL Database**: Basic tier for cost optimization
- **Cosmos DB**: Serverless mode for pay-per-use pricing
- **Storage Account**: Standard LRS for file uploads
- **Application Insights**: For monitoring and telemetry
- **Key Vault**: For secrets management

### Cost Optimizations

- 🎯 **Single Resource Group**: Simplified management and better cost tracking
- ❌ **No Redis Cache**: Saves ~$40/month with in-memory caching
- 📊 **Basic SQL Tier**: Cost-optimized database
- 🌍 **Serverless Cosmos DB**: Pay-per-use pricing
- 🔧 **Bicep-Only Infrastructure**: Faster deployments and better Azure integration
- 📦 **Right-Sized Container Resources**: Optimized CPU and memory allocation
- 🔄 **Scale-to-Zero**: Both apps scale to zero when idle

## 📁 Directory Structure

```
infrastructure/
├── bicep/
│   ├── pathfinder-single-rg.bicep     # 🎯 Main production template
│   ├── persistent-data.bicep          # 🔄 Data layer (pause/resume)
│   ├── compute-layer.bicep            # 🔄 Compute layer (pause/resume)
│   └── parameters/                    # Parameter files for different environments
├── scripts/                           # Deployment and management scripts
└── README.md                          # This file
```

### Template Descriptions

| Template | Purpose | Cost | Use Case |
|----------|---------|------|----------|
| **pathfinder-single-rg.bicep** | Complete single-RG deployment | $50-75/month | Standard production, CI/CD |
| **persistent-data.bicep** | Data layer only (databases) | $15-25/month | Pause/resume data layer |
| **compute-layer.bicep** | Compute apps connecting to data | $35-50/month | Pause/resume compute layer |

### Architecture Strategies

1. **Single Resource Group** (`pathfinder-single-rg.bicep`)
   - All resources in one RG for simplicity
   - Used by CI/CD pipeline
   - $50-75/month total cost

2. **Pause/Resume Architecture** (`persistent-data.bicep` + `compute-layer.bicep`)
   - Separate data and compute layers
   - Delete compute layer when idle (70% savings)
   - $15-25/month when paused, $50-75/month when active

## 🚀 Deployment

### Automated Deployment (Recommended)

Infrastructure is automatically deployed via the CI/CD pipeline in `.github/workflows/infrastructure-deploy.yml`:

1. **Triggers**: On push to `main` branch or manual workflow dispatch
2. **Template**: Uses `pathfinder-single-rg.bicep`
3. **Parameters**: Injected from GitHub secrets
4. **Idempotent**: Safe to run multiple times

### Manual Deployment Options

#### Option 1: Standard Single Resource Group
```bash
# Login to Azure
az login

# Deploy complete infrastructure
./scripts/deploy-single-rg.sh
```

#### Option 2: Pause/Resume Architecture
```bash
# Deploy data layer (one-time)
./scripts/deploy-data-layer.sh

# Deploy/resume compute layer
./scripts/resume-environment.sh

# Pause (delete compute layer)
./scripts/pause-environment.sh
```

### GitHub Actions Workflows

- **Infrastructure Deploy**: `.github/workflows/infrastructure-deploy.yml`
- **Pause/Resume Management**: `.github/workflows/pause-resume.yml`

## 🔧 Required Secrets

The following secrets must be configured in GitHub repository settings:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AZURE_CREDENTIALS` | Azure service principal credentials | JSON object |
| `SQL_ADMIN_LOGIN` | SQL Server admin username | `pathfinder-admin` |
| `SQL_ADMIN_PASSWORD` | SQL Server admin password | `SecureP@ssw0rd123!` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |

## 📊 Resource Naming Convention

Resources are named using the pattern: `{appName}-{resourceType}-{environment}`

Example:
- Container Apps Environment: `pathfinder-env`
- Backend App: `pathfinder-backend`
- Frontend App: `pathfinder-frontend`
- SQL Server: `pathfinder-sql`
- Cosmos Account: `pathfinder-cosmos`

## 🔍 Monitoring

- **Application Insights**: Collects telemetry and performance data
- **Log Analytics**: Centralized logging for Container Apps
- **Health Checks**: Automated health monitoring in CI/CD

## 🆚 Template Comparison

| Feature | Single RG | Pause/Resume |
|---------|-----------|--------------|
| **Templates** | 1 file | 2 files |
| **Resource Groups** | 1 (pathfinder-rg) | 2 (pathfinder-rg + pathfinder-db-rg) |
| **Cost (Active)** | $50-75/month | $50-75/month |
| **Cost (Paused)** | Not applicable | $15-25/month |
| **Complexity** | Low | Medium |
| **Best For** | Always-on production | Cost-optimized development |
| **Data Safety** | High | Very High (isolated data layer) |

## 🛠️ Template Selection Guide

### Use Single Resource Group (`pathfinder-single-rg.bicep`) when:
- ✅ Always-on production environment
- ✅ Consistent traffic patterns
- ✅ Simplicity is preferred
- ✅ CI/CD automation is primary deployment method

### Use Pause/Resume Architecture when:
- ✅ Development or staging environments
- ✅ Irregular usage patterns
- ✅ Cost optimization is critical
- ✅ Need to pause during weekends/nights

## 🛠️ Customization

### Adding New Resources

1. Choose the appropriate template:
   - `pathfinder-single-rg.bicep` for always-on resources
   - `persistent-data.bicep` for data resources
   - `compute-layer.bicep` for application resources

2. Add the resource definition with proper tags
3. Add outputs for important properties
4. Test deployment in development
5. Update documentation

### Modifying Existing Resources

1. Identify which template contains the resource
2. Update the resource definition
3. Consider backward compatibility
4. Test changes thoroughly
5. Document breaking changes

## ⚠️ Important Notes

1. **Template Focus**: Only 3 production-ready templates remain
2. **CI/CD Integration**: Main pipeline uses `pathfinder-single-rg.bicep`
3. **Cost Monitoring**: Monitor both RGs if using pause/resume
4. **Data Safety**: Never delete `pathfinder-db-rg` in pause/resume architecture
5. **Scaling**: Resources are sized for solo developer/small team workloads

## ⚠️ Important Notes

1. **Template Focus**: Only 3 production-ready templates remain
2. **CI/CD Integration**: Main pipeline uses `pathfinder-single-rg.bicep`
3. **Cost Monitoring**: Monitor both RGs if using pause/resume
4. **Data Safety**: Never delete `pathfinder-db-rg` in pause/resume architecture
5. **Scaling**: Resources are sized for solo developer/small team workloads

## 🔄 Pause/Resume Quick Reference

```bash
# Deploy data layer (one-time setup)
./scripts/deploy-data-layer.sh

# Resume environment
./scripts/resume-environment.sh

# Pause environment (save $35-50/month)
./scripts/pause-environment.sh

# Check status
az group list --query "[?starts_with(name, 'pathfinder')]"
```

## 📈 Performance Considerations

- **Container Apps**: Auto-scaling based on HTTP requests with aggressive resource constraints (0.25 CPU / 0.5Gi memory per container)
- **Cosmos DB**: Serverless mode scales automatically
- **SQL Database**: Basic tier suitable for moderate workloads
- **Storage**: Standard LRS for cost-effective file storage
- **Resource Optimization**: 75% reduction from standard allocations for maximum cost efficiency

## 🆘 Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check Azure permissions
   - Verify parameter values
   - Review deployment logs

2. **Resource Naming Conflicts**
   - Ensure unique resource names
   - Check existing resources in subscription

3. **Connection Issues**
   - Verify firewall rules
   - Check connection strings
   - Validate network configuration

### Support

For issues or questions:
1. Check GitHub Actions logs
2. Review Azure portal deployment history
3. Consult Azure documentation
4. Create GitHub issue for persistent problems 