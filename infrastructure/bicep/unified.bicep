// ============================================================================
// UNIFIED INFRASTRUCTURE TEMPLATE FOR PATHFINDER
// Consolidates all deployment scenarios into a single, parameter-driven template
// Implements the Infrastructure Template Consolidation from tech debt remediation
// ============================================================================

@description('Name of the application')
param appName string = 'pathfinder'

@description('Environment (development, production, testing)')
@allowed(['development', 'production', 'testing'])
param environment string = 'development'

@description('Location for resources')
param location string = resourceGroup().location

@description('Deployment timestamp')
param deploymentTimestamp string = utcNow()

// ==================== FEATURE FLAGS ====================
@description('Enable Redis cache (adds ~$40/month cost)')
param enableRedis bool = false

@description('Enable Cosmos DB (adds ~$25/month cost)')
param enableCosmosDb bool = true

@description('Enable Application Insights telemetry')
param enableApplicationInsights bool = true

@description('Enable Key Vault for secrets management')
param enableKeyVault bool = true

@description('Enable static web app (alternative to container app frontend)')
param enableStaticWebApp bool = false

// ==================== RESOURCE CONFIGURATION ====================
@description('Resource optimization level')
@allowed(['minimal', 'standard', 'premium'])
param resourceLevel string = 'standard'

@description('Database tier configuration')
@allowed(['Basic', 'Standard', 'Premium'])
param databaseTier string = 'Basic'

@description('Database capacity (DTU for Basic, vCore for others)')
param databaseCapacity int = 5

@description('Auto-scaling configuration')
param autoScaling object = {
  minReplicas: environment == 'production' ? 1 : 0
  maxReplicas: environment == 'production' ? 5 : 2
  concurrentRequests: environment == 'production' ? 30 : 50
}

// ==================== SECURITY PARAMETERS ====================
@description('SQL Server admin username')
@secure()
param sqlAdminLogin string

@description('SQL Server admin password')
@secure()
param sqlAdminPassword string

@description('OpenAI API key')
@secure()
param openAIApiKey string = ''

@description('Auth0 configuration')
param auth0Config object = {
  domain: 'dev-jwnud3v8ghqnyygr.us.auth0.com'
  audience: 'https://pathfinder-api.com'
  clientId: 'KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn'
  clientSecret: ''
}

@description('Additional API keys and secrets')
@secure()
param secrets object = {}

// ==================== COMPUTED VARIABLES ====================
var tags = {
  app: appName
  environment: environment
  deploymentType: 'unified-template'
  resourceLevel: resourceLevel
  costOptimized: string(resourceLevel == 'minimal')
  deployedBy: 'infrastructure-consolidation'
}

// Resource naming strategy
var resourceNames = {
  // Core resources
  containerAppsEnv: '${appName}-env'
  backendApp: '${appName}-backend'
  frontendApp: '${appName}-frontend'
  
  // Data layer
  sqlServer: '${appName}-sql'
  sqlDatabase: '${appName}-db'
  cosmosAccount: enableCosmosDb ? '${appName}-cosmos' : ''
  redisCache: enableRedis ? '${appName}-redis' : ''
  
  // Storage and monitoring
  storageAccount: replace('${appName}storage', '-', '')
  logAnalytics: '${appName}-logs'
  appInsights: enableApplicationInsights ? '${appName}-insights' : ''
  keyVault: enableKeyVault ? '${appName}-kv' : ''
  
  // Static web app (alternative frontend)
  staticWebApp: enableStaticWebApp ? '${appName}-static' : ''
}

// Resource configurations based on level
var resourceConfigs = {
  minimal: {
    cpu: json('0.25')
    memory: '0.5Gi'
    sqlTier: 'Basic'
    sqlCapacity: 5
    logRetentionDays: 7
    costTarget: 'under-40-per-month'
  }
  standard: {
    cpu: json('0.5')
    memory: '1Gi'
    sqlTier: 'Standard'
    sqlCapacity: 10
    logRetentionDays: 30
    costTarget: 'under-100-per-month'
  }
  premium: {
    cpu: json('1.0')
    memory: '2Gi'
    sqlTier: 'Standard'
    sqlCapacity: 20
    logRetentionDays: 90
    costTarget: 'performance-optimized'
  }
}

var currentConfig = resourceConfigs[resourceLevel]

// ==================== MONITORING INFRASTRUCTURE ====================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: resourceNames.logAnalytics
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: currentConfig.logRetentionDays
    workspaceCapping: resourceLevel == 'minimal' ? {
      dailyQuotaGb: 1
    } : null
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = if (enableApplicationInsights) {
  name: resourceNames.appInsights
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    SamplingPercentage: resourceLevel == 'minimal' ? 50 : 100
  }
}

// ==================== CONTAINER APPS ENVIRONMENT ====================
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
    daprAIInstrumentationKey: enableApplicationInsights ? appInsights.properties.InstrumentationKey : null
  }
}

// ==================== DATABASE INFRASTRUCTURE ====================
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

  resource firewallRule 'firewallRules' = {
    name: 'AllowAzureServices'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: resourceNames.sqlDatabase
  location: location
  tags: tags
  sku: {
    name: databaseTier
    tier: databaseTier
    capacity: databaseCapacity
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: resourceLevel == 'minimal' ? 1073741824 : 2147483648 // 1GB vs 2GB
    zoneRedundant: environment == 'production' && resourceLevel == 'premium'
  }
}

// ==================== COSMOS DB (OPTIONAL) ====================
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = if (enableCosmosDb) {
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
        backupIntervalInMinutes: environment == 'production' ? 720 : 1440
        backupRetentionIntervalInHours: environment == 'production' ? 720 : 168
        backupStorageRedundancy: resourceLevel == 'premium' ? 'Geo' : 'Local'
      }
    }
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = if (enableCosmosDb) {
  parent: cosmosAccount
  name: 'pathfinder'
  properties: {
    resource: {
      id: 'pathfinder'
    }
  }
}

// ==================== REDIS CACHE (OPTIONAL) ====================
resource redisCache 'Microsoft.Cache/redis@2023-04-01' = if (enableRedis) {
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

// ==================== STORAGE ACCOUNT ====================
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: resourceNames.storageAccount
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: resourceLevel == 'minimal' ? 'Cool' : 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
}

// ==================== KEY VAULT (OPTIONAL) ====================
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = if (enableKeyVault) {
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

// ==================== BACKEND CONTAINER APP ====================
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
      secrets: concat([
        {
          name: 'sql-connection-string'
          value: 'Server=tcp:${sqlServer.name}.${az.environment().suffixes.sqlServerHostname},1433;Initial Catalog=${sqlDatabase.name};Persist Security Info=False;User ID=${sqlAdminLogin};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        }
        {
          name: 'openai-api-key'
          value: openAIApiKey
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'auth0-client-secret'
          value: auth0Config.clientSecret
        }
        {
          name: 'google-maps-api-key'
          value: secrets.googleMapsApiKey
        }
        {
          name: 'secret-key'
          value: secrets.secretKey
        }
      ], enableCosmosDb ? [{
        name: 'cosmos-connection-string'
        value: cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
      }] : [], enableRedis ? [{
        name: 'redis-connection-string'
        value: '${redisCache.name}.redis.cache.windows.net:6380,password=${redisCache.listKeys().primaryKey},ssl=True,abortConnect=False'
      }] : [])
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'nginx:alpine'  // Placeholder - will be updated by CI/CD
          resources: {
            cpu: currentConfig.cpu
            memory: currentConfig.memory
          }
          env: concat([
            {
              name: 'DATABASE_URL'
              secretRef: 'sql-connection-string'
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
              name: 'AUTH0_DOMAIN'
              value: auth0Config.domain
            }
            {
              name: 'AUTH0_AUDIENCE'
              value: auth0Config.audience
            }
            {
              name: 'AUTH0_CLIENT_ID'
              value: auth0Config.clientId
            }
            {
              name: 'AUTH0_CLIENT_SECRET'
              secretRef: 'auth0-client-secret'
            }
            {
              name: 'GOOGLE_MAPS_API_KEY'
              secretRef: 'google-maps-api-key'
            }
            {
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
            {
              name: 'RESOURCE_LEVEL'
              value: resourceLevel
            }
            {
              name: 'USE_REDIS_CACHE'
              value: string(enableRedis)
            }
            {
              name: 'COSMOS_DB_ENABLED'
              value: string(enableCosmosDb)
            }
            {
              name: 'LLM_ORCHESTRATION_URL'
              value: secrets.llmOrchestrationUrl
            }
            {
              name: 'LLM_ORCHESTRATION_API_KEY'
              value: secrets.llmOrchestrationApiKey
            }
            {
              name: 'LLM_ORCHESTRATION_ENABLED'
              value: string(!empty(secrets.llmOrchestrationUrl))
            }
          ], enableApplicationInsights ? [{
            name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
            value: appInsights.properties.ConnectionString
          }] : [], enableCosmosDb ? [{
            name: 'COSMOS_CONNECTION_STRING'
            secretRef: 'cosmos-connection-string'
          }] : [], enableRedis ? [{
            name: 'REDIS_URL'
            secretRef: 'redis-connection-string'
          }] : [])
        }
      ]
      scale: {
        minReplicas: autoScaling.minReplicas
        maxReplicas: autoScaling.maxReplicas
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: string(autoScaling.concurrentRequests)
              }
            }
          }
        ]
      }
    }
  }
}

// ==================== FRONTEND CONTAINER APP ====================
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = if (!enableStaticWebApp) {
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
        // No Auth0 secrets here as they are public configuration values
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: 'nginx:alpine'  // Placeholder - will be updated by CI/CD
          resources: {
            cpu: currentConfig.cpu
            memory: currentConfig.memory
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
              value: auth0Config.domain
            }
            {
              name: 'VITE_AUTH0_CLIENT_ID'
              value: auth0Config.clientId
            }
            {
              name: 'VITE_AUTH0_AUDIENCE'
              value: auth0Config.audience
            }
            {
              name: 'ENVIRONMENT'
              value: environment
            }
          ]
        }
      ]
      scale: {
        minReplicas: autoScaling.minReplicas
        maxReplicas: autoScaling.maxReplicas
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: string(autoScaling.concurrentRequests * 2) // Frontend can handle more concurrent requests
              }
            }
          }
        ]
      }
    }
  }
}

// ==================== STATIC WEB APP (ALTERNATIVE FRONTEND) ====================
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = if (enableStaticWebApp) {
  name: resourceNames.staticWebApp
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    repositoryUrl: ''
    branch: ''
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    provider: 'None'
    enterpriseGradeCdnStatus: 'Disabled'
  }
}

resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2022-09-01' = if (enableStaticWebApp) {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    REACT_APP_API_BASE_URL: 'https://${backendApp.properties.configuration.ingress.fqdn}'
    VITE_API_URL: 'https://${backendApp.properties.configuration.ingress.fqdn}'
    VITE_AUTH0_DOMAIN: auth0Config.domain
    VITE_AUTH0_CLIENT_ID: auth0Config.clientId
    VITE_AUTH0_AUDIENCE: auth0Config.audience
    ENVIRONMENT: environment
  }
}

// ==================== OUTPUTS ====================
output deploymentInfo object = {
  template: 'unified.bicep'
  version: '1.0.0'
  environment: environment
  resourceLevel: resourceLevel
  features: {
    redis: enableRedis
    cosmosDb: enableCosmosDb
    applicationInsights: enableApplicationInsights
    keyVault: enableKeyVault
    staticWebApp: enableStaticWebApp
  }
  costTarget: currentConfig.costTarget
  deploymentTimestamp: deploymentTimestamp
}

output applicationUrls object = {
  backend: 'https://${backendApp.properties.configuration.ingress.fqdn}'
  frontend: enableStaticWebApp ? 'https://${staticWebApp.properties.defaultHostname}' : 'https://${frontendApp.properties.configuration.ingress.fqdn}'
  api: 'https://${backendApp.properties.configuration.ingress.fqdn}/api'
  docs: 'https://${backendApp.properties.configuration.ingress.fqdn}/docs'
}

output infrastructure object = {
  resourceGroupName: resourceGroup().name
  sqlServerFqdn: sqlServer.properties.fullyQualifiedDomainName
  cosmosAccountName: enableCosmosDb ? cosmosAccount.name : null
  redisHostname: enableRedis ? '${redisCache.name}.redis.cache.windows.net' : null
  storageAccountName: storageAccount.name
  logAnalyticsWorkspaceId: logAnalytics.id
  appInsightsInstrumentationKey: enableApplicationInsights ? appInsights.properties.InstrumentationKey : null
  keyVaultName: enableKeyVault ? keyVault.name : null
}

output costOptimization object = {
  estimatedMonthlyCost: resourceLevel == 'minimal' ? '$25-40' : resourceLevel == 'standard' ? '$50-100' : '$100-200'
  redisEnabled: enableRedis
  cosmosDbEnabled: enableCosmosDb
  resourceLevel: resourceLevel
  databaseTier: databaseTier
  autoScaling: autoScaling
  optimizations: [
    'Unified template reduces deployment complexity'
    'Parameter-driven configuration eliminates template proliferation'
    'Feature flags enable cost control'
    'Resource scaling based on environment needs'
    resourceLevel == 'minimal' ? 'Aggressive resource constraints for maximum cost savings' : 'Balanced performance and cost'
  ]
}
