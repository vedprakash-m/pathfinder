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
  architecture: 'ultra-cost-optimized'
  deploymentType: 'solo-developer'
  costTarget: 'under-75-per-month'
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
}

// Log Analytics workspace for monitoring (cost optimized)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: resourceNames.logAnalytics
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 7  // Reduced from 30 days
    workspaceCapping: {
      dailyQuotaGb: 1    // Cap at 1GB daily to control costs
    }
  }
}

// Application Insights for telemetry (cost optimized)
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
    samplingPercentage: 50  // Sample only 50% of telemetry
    disableIpMasking: true   // Reduce processing overhead
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

// Azure SQL Database (Ultra cost-optimized - DTU 5)
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: resourceNames.sqlDatabase
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5  // DTU 5 - lowest possible
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 1073741824 // 1GB instead of 2GB
    zoneRedundant: false
  }
}

// Cosmos DB (serverless with minimal throughput)
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
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 1440  // Daily backups only
        backupRetentionIntervalInHours: 168  // 7 days retention
        backupStorageRedundancy: 'Local'  // Local instead of geo-redundant
      }
    }
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

// Storage Account for file uploads (optimized)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: resourceNames.storageAccount
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'  // Local redundancy only
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Cool'    // Cool tier for lower storage costs
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// Backend Container App (ultra-optimized)
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
            cpu: json('0.25')    // Aggressive but viable CPU allocation (75% reduction from 1.0)
            memory: '0.5Gi'      // Aggressive but viable memory allocation (75% reduction from 2Gi)
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
              name: 'LOG_LEVEL'
              value: 'WARNING'  // Reduced logging to save costs
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0        // Scale to zero when not in use
        maxReplicas: 1        // Maximum 1 replica
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '50'  // Higher threshold before scaling
              }
            }
          }
        ]
      }
    }
  }
}

// Frontend Container App (ultra-optimized)
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: resourceNames.frontendApp
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
      }
      secrets: [
        {
          name: 'auth0-domain'
          value: 'dev-jwnud3v8ghqnyygr.us.auth0.com'
        }
        {
          name: 'auth0-client-id'
          value: 'KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn'
        }
        {
          name: 'auth0-audience'
          value: 'https://pathfinder-api.com'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: 'nginx:alpine'  // Placeholder - will be updated by CI/CD
          resources: {
            cpu: json('0.25')    // Aggressive but viable CPU allocation (75% reduction)
            memory: '0.5Gi'      // Aggressive but viable memory allocation (75% reduction)
          }
          env: [
            {
              name: 'REACT_APP_API_URL'
              value: 'https://${backendApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'VITE_API_URL'
              value: 'https://${backendApp.properties.configuration.ingress.fqdn}'
            }
            {
              name: 'VITE_AUTH0_DOMAIN'
              secretRef: 'auth0-domain'
            }
            {
              name: 'VITE_AUTH0_CLIENT_ID'
              secretRef: 'auth0-client-id'
            }
            {
              name: 'VITE_AUTH0_AUDIENCE'
              secretRef: 'auth0-audience'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0        // Scale to zero when not in use
        maxReplicas: 1        // Maximum 1 replica
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '100'  // High threshold for static content
              }
            }
          }
        ]
      }
    }
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

// Ultra cost optimization summary
output ultraCostOptimizations object = {
  scaleToZero: 'Both frontend and backend scale to zero when idle'
  aggressiveResources: 'CPU: 0.25 cores, Memory: 0.5Gi per container (75% reduction from current 1.0/2Gi)'
  reducedSqlSize: '1GB database instead of 2GB'
  coolStorage: 'Cool tier storage for 20% savings'
  reducedLogging: '7-day retention, 1GB daily cap, 50% sampling'
  localBackups: 'Local redundancy instead of geo-redundant'
  estimatedMonthlyCost: '$45-65 (down from $85)'
  potentialSavings: '$20-40 per month (24-47% total reduction)'
}
