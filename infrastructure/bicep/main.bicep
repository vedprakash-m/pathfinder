// Main Bicep template for Pathfinder infrastructure
// Deploys all Azure resources in a single resource group

targetScope = 'subscription'

@description('Environment name (used for resource naming)')
@allowed(['dev', 'prod'])
param environment string = 'prod'

@description('Azure region for resources')
param location string = 'westus2'

@description('Unique suffix for resource names')
param uniqueSuffix string = substring(uniqueString(subscription().subscriptionId), 0, 6)

// Resource group name
var resourceGroupName = 'pathfinder-rg'

// Create resource group
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: {
    project: 'pathfinder'
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
    uniqueSuffix: uniqueSuffix
    environment: environment
  }
}

module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage-deployment'
  params: {
    location: location
    uniqueSuffix: uniqueSuffix
    environment: environment
  }
}

module keyVault 'modules/keyvault.bicep' = {
  scope: rg
  name: 'key-vault-deployment'
  params: {
    location: location
    uniqueSuffix: uniqueSuffix
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
    uniqueSuffix: uniqueSuffix
    environment: environment
  }
}

module functionApp 'modules/functionapp.bicep' = {
  scope: rg
  name: 'function-app-deployment'
  params: {
    location: location
    uniqueSuffix: uniqueSuffix
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
    uniqueSuffix: uniqueSuffix
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
