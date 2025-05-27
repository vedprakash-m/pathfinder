@description('Name of the application')
param appName string = 'pathfinder'

@description('Environment (dev, test, prod)')
param environment string = 'dev'

@description('Location for resources')
param location string = resourceGroup().location

@description('SQL Server admin username')
@secure()
param sqlAdminLogin string

@description('SQL Server admin password')
@secure()
param sqlAdminPassword string

@description('OpenAI API key')
@secure()
param openAIApiKey string = ''

// Tags for all resources
var tags = {
  app: appName
  environment: environment
}

// Resource naming
var resourceNames = {
  containerAppsEnv: '${appName}-env-${environment}'
  backendApp: '${appName}-backend-${environment}'
  frontendApp: '${appName}-frontend-${environment}'
  cosmosAccount: '${appName}-cosmos-${environment}'
  sqlServer: '${appName}-sql-${environment}'
  sqlDatabase: '${appName}-db-${environment}'
  redisCache: '${appName}-redis-${environment}'
  logAnalytics: '${appName}-logs-${environment}'
  appInsights: '${appName}-insights-${environment}'
  storageAccount: replace('${appName}storage${environment}', '-', '')
  keyVault: '${appName}-kv-${environment}'
  staticWebApp: '${appName}-static-${environment}'
}

// Log Analytics workspace for monitoring
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: resourceNames.logAnalytics
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights for telemetry
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: resourceNames.appInsights
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Container Apps Environment
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: resourceNames.containerAppsEnv
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    daprAIInstrumentationKey: appInsights.properties.InstrumentationKey
  }
}

// Azure SQL Server
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: resourceNames.sqlServer
  location: location
  tags: tags
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
  }

  // Allow Azure services to access
  resource firewallRule 'firewallRules' = {
    name: 'AllowAzureServices'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  }
}

// Azure SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: resourceNames.sqlDatabase
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648 // 2GB
    zoneRedundant: false
  }
}

// Import other modules
module cosmos './cosmos-db.bicep' = {
  name: 'cosmosDbDeploy'
  params: {
    accountName: resourceNames.cosmosAccount
    location: location
    tags: tags
  }
}

module storage './storage.bicep' = {
  name: 'storageDeploy'
  params: {
    accountName: resourceNames.storageAccount
    location: location
    tags: tags
  }
}

module backendApp './container-apps.bicep' = {
  name: 'backendAppDeploy'
  params: {
    appName: resourceNames.backendApp
    containerEnvId: containerAppsEnv.id
    location: location
    tags: tags
    cosmosConnectionString: cosmos.outputs.connectionString
    sqlConnectionString: 'Server=tcp:${sqlServer.name}.database.windows.net,1433;Initial Catalog=${sqlDatabase.name};Persist Security Info=False;User ID=${sqlAdminLogin};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
    openAIApiKey: openAIApiKey
    appInsightsConnectionString: appInsights.properties.ConnectionString
    storageAccountConnectionString: storage.outputs.connectionString
  }
}

module staticWebApp './static-web-app.bicep' = {
  name: 'staticWebAppDeploy'
  params: {
    appName: resourceNames.staticWebApp
    location: location
    tags: tags
    apiBackendUrl: 'https://${backendApp.outputs.appUrl}'
  }
}

// Key Vault for secrets management
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: resourceNames.keyVault
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enableRbacAuthorization: true
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: true
    publicNetworkAccess: 'Enabled'
  }
}

// Redis Cache for caching layer
resource redisCache 'Microsoft.Cache/redis@2023-04-01' = {
  name: resourceNames.redisCache
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// Outputs
output backendAppUrl string = backendApp.outputs.appUrl
output frontendAppUrl string = staticWebApp.outputs.appUrl
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output cosmosAccountName string = cosmos.outputs.accountName
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output keyVaultName string = keyVault.name
