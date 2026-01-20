// Azure Functions Flex Consumption module
// IDEMPOTENT: Uses deterministic naming based on subscription

@description('Azure region for resources')
param location string

@description('Unique ID for globally unique resources')
param uniqueId string

@description('Environment name')
param environment string

@description('Storage account name for Functions')
param storageAccountName string

@description('Key Vault name for secrets')
param keyVaultName string

@description('SignalR service name')
param signalRName string

@description('Cosmos DB endpoint')
param cosmosDbEndpoint string

// Resource names - globally unique, deterministic per subscription
var functionAppName = 'pf-func-${uniqueId}'
var hostingPlanName = 'pf-plan-${uniqueId}'
var appInsightsName = 'pf-insights-${uniqueId}'

// Reference existing storage account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

// Reference existing Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

// Reference existing SignalR
resource signalR 'Microsoft.SignalRService/signalR@2023-08-01-preview' existing = {
  name: signalRName
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  properties: {
    Application_Type: 'web'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    RetentionInDays: 30
  }
}

// Flex Consumption hosting plan
resource hostingPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: hostingPlanName
  location: location
  kind: 'functionapp'
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {
    reserved: true // Linux
  }
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: hostingPlan.id
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.13'
      pythonVersion: '3.13'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'COSMOS_DB_URL'
          value: cosmosDbEndpoint
        }
        {
          name: 'COSMOS_DB_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/cosmos-db-primary-key/)'
        }
        {
          name: 'COSMOS_DB_NAME'
          value: 'pathfinder'
        }
        {
          name: 'SIGNALR_CONNECTION_STRING'
          value: signalR.listKeys().primaryConnectionString
        }
        {
          name: 'OPENAI_API_KEY'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/openai-api-key/)'
        }
        {
          name: 'OPENAI_MODEL'
          value: 'gpt-5-mini'
        }
        {
          name: 'ENTRA_TENANT_ID'
          value: 'vedid.onmicrosoft.com'
        }
        {
          name: 'ENTRA_CLIENT_ID'
          value: '@Microsoft.KeyVault(SecretUri=${keyVault.properties.vaultUri}secrets/entra-client-id/)'
        }
        {
          name: 'FRONTEND_URL'
          value: 'https://pf-swa-${uniqueId}.azurestaticapps.net'
        }
      ]
      cors: {
        allowedOrigins: [
          'https://pf-swa-${uniqueId}.azurestaticapps.net'
          'http://localhost:4280'
          'http://localhost:5173'
        ]
        supportCredentials: true
      }
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
  }
}

// Grant Function App access to Key Vault
resource keyVaultAccessPolicy 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output functionAppPrincipalId string = functionApp.identity.principalId
