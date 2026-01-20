// Azure Key Vault module
// IDEMPOTENT: Uses deterministic naming based on subscription

@description('Azure region for resources')
param location string

@description('Unique ID for globally unique resources')
param uniqueId string

@description('Environment name')
param environment string

@description('Cosmos DB account name')
param cosmosDbAccountName string

@description('Storage account name')
param storageAccountName string

// Key Vault name - globally unique, deterministic per subscription
var keyVaultName = 'pf-kv-${uniqueId}'

// Reference existing Cosmos DB account
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosDbAccountName
}

// Reference existing storage account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Store Cosmos DB connection string
resource cosmosDbSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cosmos-db-connection-string'
  properties: {
    value: cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
    contentType: 'text/plain'
  }
}

// Store Cosmos DB primary key
resource cosmosDbKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'cosmos-db-primary-key'
  properties: {
    value: cosmosAccount.listKeys().primaryMasterKey
    contentType: 'text/plain'
  }
}

// Store Storage connection string
resource storageSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'storage-connection-string'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
    contentType: 'text/plain'
  }
}

// Placeholder for OpenAI API key (must be set manually)
resource openAiKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: 'REPLACE_WITH_ACTUAL_KEY'
    contentType: 'text/plain'
  }
}

// Placeholder for Entra Client ID (must be set manually)
resource entraClientIdSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'entra-client-id'
  properties: {
    value: 'REPLACE_WITH_ACTUAL_CLIENT_ID'
    contentType: 'text/plain'
  }
}

// Outputs
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
