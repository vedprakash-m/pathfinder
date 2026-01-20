// Main Bicep template for Pathfinder infrastructure
// Deploys all Azure resources in a single resource group
// IDEMPOTENT: Uses fixed naming convention - resources are updated, not recreated

targetScope = 'subscription'

@description('Environment name (used for resource naming)')
@allowed(['dev', 'prod'])
param environment string = 'prod'

@description('Azure region for resources')
param location string = 'westus2'

@description('Project name prefix for all resources')
param projectPrefix string = 'pathfinder'

// Fixed naming convention - deterministic and idempotent
// Same names on every deployment = resources updated, not duplicated
var resourceGroupName = '${projectPrefix}-rg'
var nameSuffix = environment == 'prod' ? 'prod' : 'dev'
// For globally unique resources (SignalR, etc.) - still deterministic per subscription
var uniqueId = uniqueString(subscription().subscriptionId, projectPrefix)

// Create resource group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: {
    project: projectPrefix
    environment: environment
    managedBy: 'bicep'
  }
}

// Deploy infrastructure modules
module cosmosDb 'modules/cosmosdb.bicep' = {
  scope: rg
  name: 'cosmos-db-deployment'
  params: {
    location: location
    nameSuffix: nameSuffix
    environment: environment
  }
}

module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage-deployment'
  params: {
    location: location
    nameSuffix: nameSuffix
    environment: environment
  }
}

module keyVault 'modules/keyvault.bicep' = {
  scope: rg
  name: 'key-vault-deployment'
  params: {
    location: location
    nameSuffix: nameSuffix
    environment: environment
    cosmosDbAccountName: cosmosDb.outputs.accountName
    storageAccountName: storage.outputs.storageAccountName
  }
}

module signalR 'modules/signalr.bicep' = {
  scope: rg
  name: 'signalr-deployment'
  params: {
    location: location
    uniqueId: uniqueId
    environment: environment
  }
}

module functionApp 'modules/functionapp.bicep' = {
  scope: rg
  name: 'function-app-deployment'
  params: {
    location: location
    nameSuffix: nameSuffix
    environment: environment
    storageAccountName: storage.outputs.storageAccountName
    keyVaultName: keyVault.outputs.keyVaultName
    signalRName: signalR.outputs.signalRName
    cosmosDbEndpoint: cosmosDb.outputs.endpoint
  }
}

module staticWebApp 'modules/staticwebapp.bicep' = {
  scope: rg
  name: 'static-web-app-deployment'
  params: {
    location: location
    nameSuffix: nameSuffix
    environment: environment
    functionAppUrl: functionApp.outputs.functionAppUrl
  }
}

// Outputs
output resourceGroupName string = rg.name
output cosmosDbEndpoint string = cosmosDb.outputs.endpoint
output storageAccountName string = storage.outputs.storageAccountName
output keyVaultName string = keyVault.outputs.keyVaultName
output signalRHostName string = signalR.outputs.hostName
output functionAppUrl string = functionApp.outputs.functionAppUrl
output staticWebAppUrl string = staticWebApp.outputs.defaultHostname
