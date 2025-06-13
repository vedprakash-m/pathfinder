# Pathfinder Pause/Resume Architecture

## 🔄 Overview

The Pathfinder pause/resume architecture enables **70% cost savings** during idle periods by separating persistent data from ephemeral compute resources. You can temporarily delete the compute layer while preserving all user data, trips, and preferences.

## 🏗️ Architecture Design

### Two-Resource Group Strategy

```
┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│          pathfinder-db-rg           │  │          pathfinder-rg              │
│         (Persistent Data)           │  │       (Ephemeral Compute)           │
│                                     │  │                                     │
│  🗄️  Azure SQL Database (Basic)     │  │  🚀 Container Apps Environment      │
│  🌍 Cosmos DB (Serverless)          │  │  📱 Frontend Container App          │
│  🔐 Key Vault (DB secrets)          │  │  ⚙️  Backend Container App          │
│  💾 Data preserved forever          │  │  📊 Application Insights            │
│                                     │  │  📁 Storage Account                 │
│  💰 $15-25/month                    │  │  🔐 Key Vault (App secrets)         │
│  ⚠️  NEVER DELETE                   │  │                                     │
│                                     │  │  💰 $35-50/month                    │
└─────────────────────────────────────┘  │  ✅ Safe to delete                  │
                                          └─────────────────────────────────────┘
```

## 💰 Cost Analysis

| State | Data Layer | Compute Layer | Total Cost | Savings |
|-------|------------|---------------|------------|---------|
| **Active** | $15-25/month | $35-50/month | **$50-75/month** | - |
| **Paused** | $15-25/month | $0/month | **$15-25/month** | **$35-50/month (70%)** |

### Cost Breakdown by Resource

#### Data Layer (Always Running)
- **Azure SQL Database (Basic, DTU 5)**: ~$5/month
- **Cosmos DB (Serverless)**: ~$8-15/month (usage-based)
- **Key Vault**: ~$1/month
- **Total**: $15-25/month

#### Compute Layer (Pausable)
- **Container Apps Environment**: ~$10/month
- **Container Apps (2x)**: ~$15-25/month
- **Application Insights**: ~$5-10/month
- **Storage Account**: ~$2/month
- **Log Analytics**: ~$3-8/month
- **Total**: $35-50/month

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended)

1. **Deploy Data Layer**:
   - Go to Actions → "Pause/Resume Environment Management"
   - Select "deploy-data-layer" and run workflow

2. **Resume Environment**:
   - Select "resume" action and run workflow
   - Application ready in 5-10 minutes

3. **Pause Environment**:
   - Select "pause" action, type "CONFIRM" and run workflow
   - Saves $35-50/month immediately

### Option 2: Local Scripts

```bash
# Deploy persistent data layer (one-time)
./scripts/deploy-data-layer.sh

# Resume full environment
./scripts/resume-environment.sh

# Pause environment (delete compute layer)
./scripts/pause-environment.sh

# Check current status
az group list --query "[?starts_with(name, 'pathfinder')].{Name:name, State:properties.provisioningState}"
```

## 📋 Detailed Workflow

### 1. Initial Setup (One-Time)

```bash
# Deploy the persistent data layer
./scripts/deploy-data-layer.sh
```

This creates:
- `pathfinder-db-rg` with databases and data-specific Key Vault
- SQL Server with Basic tier database
- Cosmos DB in serverless mode
- Secure storage for database connection strings

### 2. Resume Environment

```bash
# Restore compute layer
./scripts/resume-environment.sh
```

This:
- Creates `pathfinder-rg` resource group
- Deploys Container Apps Environment
- Connects to existing databases in `pathfinder-db-rg`
- Deploys frontend/backend apps with placeholder images
- CI/CD pipeline automatically updates with real application images

**Timeline**: 5-10 minutes to full functionality

### 3. Pause Environment

```bash
# Delete compute layer to save costs
./scripts/pause-environment.sh
```

This:
- Backs up current application URLs
- Deletes entire `pathfinder-rg` resource group
- Preserves all data in `pathfinder-db-rg`
- Saves state information for easy resume

**Timeline**: 5-10 minutes to complete deletion

## 🔒 Data Preservation

### What's Preserved During Pause
✅ **All user accounts and profiles**  
✅ **Trip data and itineraries**  
✅ **Family configurations**  
✅ **Chat history and messages**  
✅ **Budget and expense data**  
✅ **AI-generated recommendations**  
✅ **File uploads and attachments**  

### What's Recreated on Resume
🔄 **Container Apps Environment**  
🔄 **Application containers**  
🔄 **Application Insights telemetry**  
🔄 **Storage for temporary files**  
🔄 **Compute-specific secrets**  

### Connection Security
- Cross-resource group references using existing resource syntax
- Database connection strings retrieved from data layer Key Vault
- No connection information stored in compute layer templates
- Automatic firewall rules allow Azure service connections

## 🎯 Use Cases

### Development Workflow
```bash
# Working on features
./scripts/resume-environment.sh

# Deploy and test changes via CI/CD
git push origin main

# Pause when done for the day
./scripts/pause-environment.sh
```

### Demo Preparation
```bash
# Resume before demo
./scripts/resume-environment.sh

# Full environment ready in 10 minutes
# All data preserved from previous sessions
```

### Extended Breaks
```bash
# Going on vacation? Pause the environment
./scripts/pause-environment.sh

# Save $35-50/month while away
# Resume anytime with zero data loss
```

## 🔍 Monitoring and Status

### Check Environment Status
```bash
# Quick status check
az group list --query "[?starts_with(name, 'pathfinder')].[name, properties.provisioningState]" -o table

# Detailed resource inventory
az resource list --resource-group pathfinder-db-rg -o table
az resource list --resource-group pathfinder-rg -o table 2>/dev/null || echo "Compute layer paused"
```

### GitHub Actions Status Dashboard
Use the "status" action in the pause/resume workflow for detailed environment information:
- Resource group states
- Current application URLs
- Cost estimates
- Available actions

## ⚠️ Important Considerations

### Database Connection Handling
- **SQL Database**: Basic tier automatically scales down when not accessed
- **Cosmos DB**: Serverless mode only charges for actual RU consumption
- **Connection pooling**: Applications reconnect automatically on resume

### URL Changes
- Application URLs change each time you resume (Container Apps behavior)
- Use the status workflow or resume script output to get new URLs
- Consider setting up custom domains for production stability

### CI/CD Integration
- Main deployment pipeline works normally when environment is active
- Deployment will fail gracefully if compute layer is paused
- Resume environment first, then trigger deployments

### Security Considerations
- Database firewall allows Azure services by default
- Key Vault access policies preserved in data layer
- Compute layer secrets recreated on each resume
- No security degradation during pause/resume cycles

## 🚨 Troubleshooting

### Resume Fails
```bash
# Check data layer exists
az group show --name pathfinder-db-rg

# Verify SQL server is accessible
az sql server show --name pathfinder-sql-prod --resource-group pathfinder-db-rg

# Check template exists
ls infrastructure/bicep/compute-layer.bicep
```

### Application Not Starting
```bash
# Check container app logs
az containerapp logs show --name pathfinder-backend --resource-group pathfinder-rg

# Verify database connections
az containerapp exec --name pathfinder-backend --resource-group pathfinder-rg
```

### Cost Higher Than Expected
```bash
# Review resource pricing
az consumption usage list --end-date $(date +%Y-%m-%d) --start-date $(date -d '30 days ago' +%Y-%m-%d)

# Check for unexpected resources
az resource list --resource-group pathfinder-rg
az resource list --resource-group pathfinder-db-rg
```

## 📈 Optimization Tips

1. **Pause Daily**: Develop habit of pausing when not actively using
2. **Weekend Pauses**: Save $8-12 per weekend by pausing Friday-Monday
3. **Monitor Usage**: Set up Azure cost alerts for both resource groups
4. **Scale Down Further**: Consider reducing database DTU if usage is very light
5. **Regional Optimization**: Both resource groups should be in same region for best performance

## 🔄 Future Enhancements

- **Scheduled Pausing**: GitHub Actions scheduled workflow for automatic pause/resume
- **Slack Integration**: Notifications when environment state changes
- **Cost Analytics**: Detailed savings tracking and reporting
- **Blue/Green Deployments**: Use pause/resume for zero-downtime deployments
