# Pathfinder Deployment Guide

This guide covers deploying Pathfinder to Azure.

## Prerequisites

1. **Azure CLI** installed and logged in
2. **GitHub repository** with secrets configured
3. **Azure subscription** with Contributor access
4. **Microsoft Entra ID** app registration

## Quick Start

### 1. Deploy Infrastructure

```bash
# Login to Azure
az login

# Deploy infrastructure
cd infrastructure/bicep
az deployment sub create \
  --name pathfinder-$(date +%Y%m%d-%H%M%S) \
  --location westus2 \
  --template-file main.bicep \
  --parameters @parameters/prod.parameters.json
```

### 2. Configure Secrets

After infrastructure deployment:

```bash
# Get the Key Vault name (includes unique suffix)
KV_NAME=$(az keyvault list --resource-group pathfinder-rg --query "[0].name" -o tsv)

# Set OpenAI API Key
az keyvault secret set --vault-name $KV_NAME --name openai-api-key --value "YOUR_OPENAI_API_KEY"

# Set Entra Client ID
az keyvault secret set --vault-name $KV_NAME --name entra-client-id --value "YOUR_ENTRA_CLIENT_ID"
```

### 3. Configure GitHub Secrets

Add these secrets to your GitHub repository:

| Secret Name | Description |
|-------------|-------------|
| `AZURE_CREDENTIALS` | Service principal JSON for Azure login |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web Apps deployment token |
| `ENTRA_CLIENT_ID` | Microsoft Entra ID client ID |

#### Create Azure Credentials

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "pathfinder-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/pathfinder-rg \
  --json-auth

# Copy the JSON output to AZURE_CREDENTIALS secret
```

#### Get Static Web Apps Token

```bash
# Get SWA name
SWA_NAME=$(az staticwebapp list --resource-group pathfinder-rg --query "[0].name" -o tsv)

# Get deployment token
az staticwebapp secrets list --name $SWA_NAME --query "properties.apiKey" -o tsv
```

### 4. Deploy Application

Push to `main` branch to trigger deployments:

```bash
git push origin main
```

Or manually trigger via GitHub Actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Azure West US 2                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │  Static Web App  │────▶│     Azure Functions (Flex)       │  │
│  │  (React Frontend)│     │                                  │  │
│  └──────────────────┘     │  ┌────────────┐ ┌────────────┐  │  │
│                           │  │ HTTP Funcs │ │ Queue Funcs│  │  │
│                           │  └────────────┘ └────────────┘  │  │
│                           │  ┌────────────┐ ┌────────────┐  │  │
│                           │  │Timer Funcs │ │ SignalR    │  │  │
│                           │  └────────────┘ └────────────┘  │  │
│                           └───────────┬──────────────────────┘  │
│                                       │                          │
│           ┌───────────────────────────┼───────────────────────┐ │
│           │                           │                       │ │
│  ┌────────▼────────┐  ┌───────────────▼───────┐  ┌───────────┐│ │
│  │   Cosmos DB     │  │     Key Vault         │  │  SignalR  ││ │
│  │  (Serverless)   │  │  (Secrets Storage)    │  │  (Free)   ││ │
│  └─────────────────┘  └───────────────────────┘  └───────────┘│ │
│           │                                                    │ │
│  ┌────────▼────────┐                                          │ │
│  │ Storage Account │                                          │ │
│  │ (Queue Storage) │                                          │ │
│  └─────────────────┘                                          │ │
└─────────────────────────────────────────────────────────────────┘
```

## Environment Variables

### Backend (Azure Functions)

| Variable | Description | Source |
|----------|-------------|--------|
| `COSMOS_DB_URL` | Cosmos DB endpoint | Bicep output |
| `COSMOS_DB_KEY` | Cosmos DB key | Key Vault |
| `COSMOS_DB_NAME` | Database name | `pathfinder` |
| `SIGNALR_CONNECTION_STRING` | SignalR connection | Bicep output |
| `OPENAI_API_KEY` | OpenAI API key | Key Vault |
| `OPENAI_MODEL` | AI model name | `gpt-5-mini` |
| `ENTRA_TENANT_ID` | Entra tenant | `vedid.onmicrosoft.com` |
| `ENTRA_CLIENT_ID` | Entra client ID | Key Vault |

### Frontend (Static Web App)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL |
| `VITE_ENTRA_EXTERNAL_TENANT_ID` | Entra tenant ID |
| `VITE_ENTRA_EXTERNAL_CLIENT_ID` | Entra client ID |
| `VITE_ENABLE_SIGNALR` | Enable real-time features |
| `VITE_ENABLE_AI_ASSISTANT` | Enable AI assistant |

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy local settings
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your values

# Start Azure Functions
func start
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.template .env.local
# Edit .env.local with your values

# Start development server
npm run dev
```

## Monitoring

### Application Insights

All Azure Functions automatically log to Application Insights. Access via Azure Portal:

1. Go to `pathfinder-rg` resource group
2. Open `pf-insights-*` Application Insights
3. View Live Metrics, Failures, Performance

### Health Checks

- Backend: `https://<function-app>/api/health`
- Backend Readiness: `https://<function-app>/api/health/ready`
- Backend Liveness: `https://<function-app>/api/health/live`

## Cost Optimization

| Resource | Tier | Estimated Cost |
|----------|------|----------------|
| Cosmos DB | Serverless | $0.25/100K RUs |
| Storage | Standard LRS | $0.02/GB |
| Key Vault | Standard | $0.03/10K ops |
| SignalR | Free | $0 (20K msg/day) |
| Functions | Flex Consumption | $0.20/M executions |
| Static Web Apps | Free | $0 |

**Estimated Monthly: $5-20** (vs. $150-300 with Container Apps)

## Troubleshooting

### Common Issues

1. **Token validation fails**
   - Verify ENTRA_TENANT_ID and ENTRA_CLIENT_ID
   - Check app registration in Entra ID

2. **SignalR connection fails**
   - Verify SIGNALR_CONNECTION_STRING
   - Check CORS settings in Functions

3. **Cosmos DB errors**
   - Verify connection string in Key Vault
   - Check database/container exists

4. **AI generation fails**
   - Verify OPENAI_API_KEY
   - Check rate limits and quotas

### Logs

```bash
# View Function App logs
az webapp log tail --name pf-func-<suffix> --resource-group pathfinder-rg

# Query Application Insights
az monitor app-insights query \
  --app pf-insights-<suffix> \
  --analytics-query "traces | where timestamp > ago(1h) | order by timestamp desc"
```
