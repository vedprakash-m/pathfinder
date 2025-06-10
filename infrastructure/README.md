# Pathfinder Infrastructure

This directory contains the Infrastructure as Code (IaC) templates for the Pathfinder application, optimized for solo developer deployment with significant cost savings.

## 🏗️ Architecture Overview

The infrastructure is designed with a **Redis-free, single-environment approach** that saves approximately **$110/month** compared to enterprise setups.

### Key Components

- **Container Apps**: Serverless containers for backend and frontend
- **Azure SQL Database**: Basic tier for cost optimization
- **Cosmos DB**: Serverless mode for pay-per-use pricing
- **Storage Account**: Standard LRS for file uploads
- **Application Insights**: For monitoring and telemetry
- **Key Vault**: For secrets management

### Cost Optimizations

- ❌ **No Redis Cache**: Saves ~$40/month
- 📊 **Basic SQL Tier**: Cost-optimized database
- 🌍 **Serverless Cosmos DB**: Pay-per-use pricing
- 🔧 **Single Environment**: Solo developer approach
- 📦 **Minimal Container Resources**: Right-sized for the workload

## 📁 Directory Structure

```
infrastructure/
├── bicep/
│   ├── redis-free.bicep           # Main Redis-free template
│   ├── redis-free.parameters.json # Parameter file
│   ├── main.bicep                 # Original enterprise template
│   ├── container-apps.bicep       # Container Apps module
│   ├── cosmos-db.bicep           # Cosmos DB module
│   ├── storage.bicep             # Storage module
│   └── ...
├── scripts/                      # Deployment scripts
└── README.md                     # This file
```

## 🚀 Deployment

### Automated Deployment (Recommended)

Infrastructure is automatically deployed via the CI/CD pipeline in `.github/workflows/ci-cd-pipeline.yml`:

1. **Triggers**: On push to `main` branch
2. **Template**: Uses `redis-free.bicep`
3. **Parameters**: Injected from GitHub secrets
4. **Idempotent**: Safe to run multiple times

### Manual Deployment

If you need to deploy manually:

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name pathfinder-rg-dev \
  --location "East US"

# Deploy infrastructure
az deployment group create \
  --resource-group pathfinder-rg-dev \
  --template-file bicep/redis-free.bicep \
  --parameters \
    appName=pathfinder \
    environment=production \
    sqlAdminLogin="your-admin-login" \
    sqlAdminPassword="your-secure-password" \
    openAIApiKey="your-openai-key"
```

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

| Feature | redis-free.bicep | main.bicep |
|---------|------------------|------------|
| Redis Cache | ❌ | ✅ |
| Cost/Month | ~$35 | ~$160 |
| Complexity | Low | High |
| Environments | Single | Multi |
| Best For | Solo Developer | Enterprise |
| Container Resources | 0.25 CPU / 0.5Gi | Standard allocation |

## 🛠️ Customization

### Adding New Resources

1. Add resource to `redis-free.bicep`
2. Update parameters if needed
3. Add outputs for important properties
4. Test deployment in development

### Modifying Existing Resources

1. Update the resource definition
2. Consider backward compatibility
3. Test changes thoroughly
4. Document breaking changes

## ⚠️ Important Notes

1. **Redis-Free Design**: The application is designed to work without Redis
2. **Cost Monitoring**: Monitor Azure costs regularly
3. **Scaling**: Resources are sized for solo developer workloads
4. **Security**: Secrets are managed via Key Vault and GitHub Secrets

## 🔄 Migration from Enterprise Template

If migrating from the enterprise `main.bicep` template:

1. **Backup**: Export current configuration
2. **Plan**: Review resource dependencies
3. **Deploy**: Use `redis-free.bicep` template
4. **Verify**: Test application functionality
5. **Cleanup**: Remove unused resources (especially Redis)

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