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
  architecture: 'redis-free'
  deploymentType: 'solo-developer'
}

// Resource naming (simplified for single environment)
var resourceNames = {
  containerAppsEnv: '${appName}-env'
  backendApp: '${appName}-backend'
  frontendApp: '${appName}-frontend'
  cosmosAccount: '${appName}-cosmos'
  sqlServer: '${appName}-sql'
  sqlDatabase: '${appName}-db'
  logAnalytics: '${appName}-logs'
  appInsights: '${appName}-insights'
  storageAccount: replace('${appName}storage', '-', '')
  keyVault: '${appName}-kv'
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

// Azure SQL Server (cost-optimized)
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

// Azure SQL Database (Basic tier for cost optimization)
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

// Cosmos DB (optional, can be disabled for further cost savings)
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: resourceNames.cosmosAccount
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

// Cosmos Database
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'pathfinder'
  properties: {
    resource: {
      id: 'pathfinder'
    }
  }
}

// Storage Account for file uploads
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: resourceNames.storageAccount
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: true
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

// Backend Container App
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: resourceNames.backendApp
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['*']
          allowedHeaders: ['*']
        }
      }
      secrets: [
        {
          name: 'sql-connection-string'
          value: 'Server=tcp:${sqlServer.name}.database.windows.net,1433;Initial Catalog=${sqlDatabase.name};Persist Security Info=False;User ID=${sqlAdminLogin};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        }
        {
          name: 'cosmos-connection-string'
          value: cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
        }
        {
          name: 'openai-api-key'
          value: openAIApiKey
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'nginx:alpine'  // Placeholder - will be updated by CI/CD
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'DATABASE_URL'
              secretRef: 'sql-connection-string'
            }
            {
              name: 'COSMOS_CONNECTION_STRING'
              secretRef: 'cosmos-connection-string'
            }
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
            {
              name: 'USE_REDIS_CACHE'
              value: 'false'
            }
            {
              name: 'CELERY_BROKER_URL'
              value: ''
            }
            {
              name: 'CELERY_RESULT_BACKEND'
              value: ''
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// Frontend Container App
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: resourceNames.frontendApp
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
      }
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: 'nginx:alpine'  // Placeholder - will be updated by CI/CD
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            {
              name: 'REACT_APP_API_URL'
              value: 'https://${backendApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

// Key Vault for secrets management (optional)
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

// Outputs
output backendAppUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output frontendAppUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output backendAppName string = backendApp.name
output frontendAppName string = frontendApp.name
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output cosmosAccountName string = cosmosAccount.name
output resourceGroupName string = resourceGroup().name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output keyVaultName string = keyVault.name

// Cost optimization summary
output costOptimizations object = {
  redisRemoved: 'Saves ~$40/month'
  basicSqlTier: 'Cost-optimized database tier'
  serverlessCosmosDb: 'Pay-per-use pricing'
  minimalContainerResources: 'Right-sized for solo developer'
  estimatedMonthlySavings: '$110 vs enterprise setup'
} 
