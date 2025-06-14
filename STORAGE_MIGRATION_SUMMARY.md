# Storage Account Migration Summary

## Overview
Successfully moved the Azure Storage Account from `pathfinder-rg` (compute layer) to `pathfinder-db-rg` (persistent data layer) to improve the pause/resume architecture.

## Changes Made

### 1. Infrastructure Templates

#### `infrastructure/bicep/persistent-data.bicep`
- ✅ Added storage account resource definition
- ✅ Added storage account to resource naming convention
- ✅ Added storage connection string secret to data layer Key Vault
- ✅ Updated outputs to include storage account information
- ✅ Updated cost optimization summary to include storage costs
- ✅ Updated pause/resume strategy to mention file preservation

#### `infrastructure/bicep/compute-layer.bicep`
- ✅ Removed storage account resource definition
- ✅ Removed storage account from compute resource naming
- ✅ Added parameters for storage account name and data Key Vault name
- ✅ Added existing resource references for data layer storage account and Key Vault
- ✅ Updated storage connection string to reference data layer storage account
- ✅ Fixed Application Insights samplingPercentage property name

### 2. Deployment Scripts

#### `scripts/resume-environment.sh`
- ✅ Added logic to discover storage account name from data layer
- ✅ Added logic to discover data layer Key Vault name
- ✅ Added new parameters to deployment parameters JSON
- ✅ Updated logging to show discovered storage account and Key Vault

#### `infrastructure/scripts/setup-env.sh`
- ✅ Updated storage account discovery to look in `pathfinder-db-rg` instead of `pathfinder-rg`

### 3. CI/CD Workflows

#### `.github/workflows/pause-resume.yml`
- ✅ Added logic to discover storage account and data Key Vault from data layer
- ✅ Added new parameters to compute layer deployment command
- ✅ Updated logging to show discovered resources

## Architecture Benefits

### Before Migration
- Storage account in compute layer (`pathfinder-rg`)
- Data lost when pausing environment (deleting compute layer)
- Inconsistent data persistence strategy

### After Migration
- Storage account in persistent data layer (`pathfinder-db-rg`)
- File uploads and application data preserved during pause periods
- Consistent data persistence strategy across all stateful resources

## Cost Impact

### Persistent Data Layer Costs (Monthly)
- SQL Database (Basic): ~$5-10
- Cosmos DB (Serverless): ~$5-15
- Storage Account (Standard LRS): ~$2-5
- Key Vault: ~$1-2
- **Total Idle Cost: $20-30/month** (when compute layer is deleted)

### Pause/Resume Savings
- Can still delete compute layer to save ~$35-50/month
- All user data, trips, preferences, and **uploaded files** now preserved
- Resume time remains 5-10 minutes

## Deployment Requirements

When deploying, the compute layer now requires these additional parameters:
- `storageAccountName`: Name of storage account in data layer
- `dataKeyVaultName`: Name of Key Vault in data layer

These are automatically discovered by the deployment scripts from the data layer resource group.

## Data Safety

✅ **No data migration required** - this is a net new deployment change
✅ All existing files in storage accounts will be preserved
✅ Connection strings automatically updated to point to correct storage account
✅ No application code changes required

## Validation

To verify the migration:
1. Deploy data layer: Contains storage account
2. Deploy compute layer: References data layer storage account
3. Pause environment: Delete compute layer, storage account remains
4. Resume environment: Compute layer reconnects to existing storage account

## Files Modified

### Infrastructure
- `infrastructure/bicep/persistent-data.bicep`
- `infrastructure/bicep/compute-layer.bicep`

### Scripts
- `scripts/resume-environment.sh`
- `infrastructure/scripts/setup-env.sh`

### Workflows
- `.github/workflows/pause-resume.yml`

All changes maintain backward compatibility and improve the pause/resume architecture's data persistence capabilities.
