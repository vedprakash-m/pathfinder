# Azure Infrastructure Deployment

This directory contains Bicep templates for deploying Pathfinder infrastructure to Azure.

## Architecture

The deployment creates:

- **Azure Cosmos DB** (Serverless) - Document database with single container and composite partition key
- **Azure Storage Account** - Queue storage for async processing
- **Azure Key Vault** - Secure storage for secrets and connection strings
- **Azure SignalR Service** (Free tier) - Real-time messaging hub
- **Azure Functions** (Flex Consumption) - Serverless API backend
- **Azure Static Web Apps** (Free tier) - React frontend hosting

## Prerequisites

1. Azure CLI installed and logged in
2. Bicep CLI installed (`az bicep install`)
3. Subscription with appropriate permissions

## Deployment

### Deploy to Production

```bash
# Navigate to infrastructure directory
cd infrastructure/bicep

# Deploy at subscription scope
az deployment sub create \
  --name pathfinder-deployment \
  --location westus2 \
  --template-file main.bicep \
  --parameters @parameters/prod.parameters.json
```

### Post-Deployment Steps

After deployment, you need to manually configure:

1. **OpenAI API Key**
   ```bash
   az keyvault secret set \
     --vault-name pf-kv-<suffix> \
     --name openai-api-key \
     --value "<your-openai-api-key>"
   ```

2. **Entra ID Client ID**
   ```bash
   az keyvault secret set \
     --vault-name pf-kv-<suffix> \
     --name entra-client-id \
     --value "<your-entra-client-id>"
   ```

3. **Configure Static Web App Deployment Token**
   - Get token from Azure Portal: Static Web Apps > pf-swa-<suffix> > Manage deployment token
   - Add as GitHub secret: `AZURE_STATIC_WEB_APPS_API_TOKEN`

## Cost Estimates

| Resource | Tier | Estimated Cost |
|----------|------|----------------|
| Cosmos DB | Serverless | ~$0.25/100K RU |
| Storage | Standard LRS | ~$0.02/GB |
| Key Vault | Standard | ~$0.03/10K operations |
| SignalR | Free | $0 (20K messages/day) |
| Functions | Flex Consumption | ~$0.20/million executions |
| Static Web Apps | Free | $0 |

**Estimated Monthly Cost**: $5-20 (depending on usage)

## Resource Naming

All resources follow the pattern: `pf-{resource}-{unique-suffix}`

- `pf-cosmos-{suffix}` - Cosmos DB account
- `pf-kv-{suffix}` - Key Vault
- `pf-signalr-{suffix}` - SignalR service
- `pf-func-{suffix}` - Function App
- `pf-swa-{suffix}` - Static Web App
- `pfstore{suffix}` - Storage account (no hyphens)

The unique suffix is automatically generated from the subscription ID.
