// Compute Layer - pathfinder-rg
// This contains only compute resources that can be safely deleted for cost savings
// Connects to existing data layer in pathfinder-db-rg

@description('Name of the application')
param appName string = 'pathfinder'

@description('Location for resources')
param location string = resourceGroup().location

@description('Data layer resource group name')
param dataResourceGroup string = 'pathfinder-db-rg'

@description('SQL Server name from data layer')
param sqlServerName string

@description('Cosmos account name from data layer')
param cosmosAccountName string

@description('Storage account name from data layer')
param storageAccountName string

@description('SQL Server admin username')
@secure()
param sqlAdminLogin string

@description('SQL Server admin password')
@secure()
param sqlAdminPassword string

@description('OpenAI API key')
@secure()
param openAIApiKey string = ''

@description('Auth0 domain for authentication')
@secure()
param auth0Domain string = ''

@description('Auth0 client ID for authentication')
@secure()
param auth0ClientId string = ''

@description('Auth0 audience for API authorization')
@secure()
param auth0Audience string = ''

@description('LLM Orchestration Service URL')
param llmOrchestrationUrl string = ''

@description('LLM Orchestration API Key')
@secure()
param llmOrchestrationApiKey string = ''

@description('Azure Container Registry name (optional). If blank, a unique name will be generated.')
param acrName string = ''

@description('Azure Container Registry SKU')
param acrSku string = 'Basic'

// Generate globally-unique ACR name when param not supplied
var resolvedAcrName = empty(acrName) ? toLower('${appName}acr${uniqueString(resourceGroup().id)}') : acrName

// Compute layer tags - ephemeral resources
var computeTags = {
  app: appName
  architecture: 'compute-layer'
  resourceType: 'ephemeral'
  dataLayer: dataResourceGroup
  costOptimization: 'enabled'
  autoDelete: 'allowed'
  resumable: 'true'
}

// Compute resource naming
var computeResourceNames = {
  containerAppsEnv: '${appName}-env'
  backendApp: '${appName}-backend'
  frontendApp: '${appName}-frontend'
  logAnalytics: '${appName}-logs'
  appInsights: '${appName}-insights'
  keyVault: '${appName}-kv' // Compute-specific Key Vault
}

// ==================== MONITORING INFRASTRUCTURE ====================
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: computeResourceNames.logAnalytics
  location: location
  tags: computeTags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: 2 // Reasonable cap for cost control
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: computeResourceNames.appInsights
  location: location
  tags: computeTags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    SamplingPercentage: 75 // Cost optimization
  }
}

// ==================== CONTAINER APPS ENVIRONMENT ====================
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: computeResourceNames.containerAppsEnv
  location: location
  tags: computeTags
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

// ==================== KEY VAULT FOR COMPUTE SECRETS ====================
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: computeResourceNames.keyVault
  location: location
  tags: computeTags
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

// ==================== AZURE CONTAINER REGISTRY (for images) ====================
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: resolvedAcrName
  location: location
  sku: {
    name: acrSku
  }
  tags: computeTags
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      retentionPolicy: {
        status: 'disabled'
        days: 0
      }
    }
  }
}

// Container Apps pull images from ACR automatically. Ensure ACR exists before this deployment.

// ==================== DATA LAYER REFERENCES ====================
// Reference existing SQL Server in data layer
resource existingSqlServer 'Microsoft.Sql/servers@2023-05-01-preview' existing = {
  name: sqlServerName
  scope: resourceGroup(dataResourceGroup)
}

// Reference existing Cosmos account in data layer
resource existingCosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' existing = {
  name: cosmosAccountName
  scope: resourceGroup(dataResourceGroup)
}

// Reference existing storage account in data layer
resource existingStorageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
  scope: resourceGroup(dataResourceGroup)
}

// ==================== BACKEND CONTAINER APP ====================
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: computeResourceNames.backendApp
  location: location
  tags: computeTags
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
          value: 'Server=tcp:${existingSqlServer.properties.fullyQualifiedDomainName},1433;Initial Catalog=${appName}-db-prod;Persist Security Info=False;User ID=${sqlAdminLogin};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
        }
        {
          name: 'cosmos-connection-string'
          value: existingCosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
        }
        {
          name: 'openai-api-key'
          value: openAIApiKey
        }
        {
          name: 'llm-orchestration-api-key'
          value: llmOrchestrationApiKey
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${existingStorageAccount.name};AccountKey=${existingStorageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: 'nginx:alpine' // Placeholder - CI/CD will update
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
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
              name: 'LLM_ORCHESTRATION_URL'
              value: llmOrchestrationUrl
            }
            {
              name: 'LLM_ORCHESTRATION_API_KEY'
              secretRef: 'llm-orchestration-api-key'
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
              value: 'production'
            }
            {
              name: 'AUTH0_DOMAIN'
              value: auth0Domain
            }
            {
              name: 'AUTH0_AUDIENCE'
              value: auth0Audience
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0 // Scale to zero for cost savings
        maxReplicas: 3
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
}

// ==================== FRONTEND CONTAINER APP ====================
resource frontendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: computeResourceNames.frontendApp
  location: location
  tags: computeTags
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
          value: !empty(auth0Domain) ? auth0Domain : 'dev-jwnud3v8ghqnyygr.us.auth0.com'
        }
        {
          name: 'auth0-client-id'
          value: !empty(auth0ClientId) ? auth0ClientId : 'KXu3KpGiyRHHHgiXX90sHuNC4rfYRcNn'
        }
        {
          name: 'auth0-audience'
          value: !empty(auth0Audience) ? auth0Audience : 'https://pathfinder-api.com'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: 'nginx:alpine' // Placeholder - CI/CD will update
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
              value: 'production'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0 // Scale to zero for cost savings
        maxReplicas: 2
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// ==================== OUTPUTS ====================
output backendAppUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output frontendAppUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'
output backendAppName string = backendApp.name
output frontendAppName string = frontendApp.name
output resourceGroupName string = resourceGroup().name
output containerAppsEnvironment string = containerAppsEnv.name
output logAnalyticsWorkspaceId string = logAnalytics.id
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output keyVaultName string = keyVault.name
output acrNameOut string = containerRegistry.name
output acrLoginServer string = containerRegistry.properties.loginServer

// Resume strategy information
output resumeStrategy object = {
  architecture: 'Compute layer connecting to persistent data layer'
  dataLayer: dataResourceGroup
  scaleToZero: 'Both apps scale to zero when idle'
  resumeTime: '5-10 minutes from pause state'
  costSavings: 'Up to 70% savings when paused'
  connectionMethod: 'Cross-resource group references to data layer'
}

output costOptimization object = {
  ephemeralResources: 'All resources in this RG can be safely deleted'
  dataPreservation: 'All data preserved in ${dataResourceGroup}'
  scaleToZero: 'Both frontend and backend scale to zero when idle'
  estimatedMonthlyCost: '$35-50 (compute layer only)'
  pausedCost: '$0 (when this RG is deleted)'
  resumeMethod: 'Redeploy this template with same parameters'
}
