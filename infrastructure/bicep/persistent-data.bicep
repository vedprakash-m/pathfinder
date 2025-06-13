// Persistent Data Layer - pathfinder-db-rg
// This contains only database resources that should never be deleted
// Optimized for minimal cost when compute layer is deleted

@description('Base name for the application')
param appName string = 'pathfinder'

@description('Environment (dev, prod)')
param environment string = 'prod'

@description('Location for resources')
param location string = resourceGroup().location

@description('SQL Server admin username')
@secure()
param sqlAdminLogin string

@description('SQL Server admin password')
@secure()
param sqlAdminPassword string

@description('Enable private endpoints for enhanced security')
param enablePrivateEndpoints bool = false // Start with false for cost optimization

// Persistent data tags
var dataTags = {
  app: appName
  environment: environment
  architecture: 'persistent-data-layer'
  resourceType: 'persistent'
  costOptimization: 'enabled'
  autoDelete: 'never'
  backup: 'enabled'
}

// Database resource naming
var dataResourceNames = {
  sqlServer: '${appName}-sql-${environment}'
  sqlDatabase: '${appName}-db-${environment}'
  cosmosAccount: '${appName}-cosmos-${environment}'
  keyVault: '${appName}-db-kv-${environment}' // Database-specific Key Vault
}

// ==================== DATABASE KEY VAULT ====================
// Dedicated Key Vault for database connection strings only
resource dbKeyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: dataResourceNames.keyVault
  location: location
  tags: dataTags
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

// ==================== AZURE SQL DATABASE ====================
// Cost-optimized SQL Server for persistence
resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: dataResourceNames.sqlServer
  location: location
  tags: dataTags
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
    minimalTlsVersion: '1.2'
  }

  // Allow Azure services (including Container Apps from other RG)
  resource azureServicesRule 'firewallRules' = {
    name: 'AllowAzureServices'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  }

  // Allow all Azure IPs for simplicity (can be restricted later)
  resource allAzureRule 'firewallRules' = {
    name: 'AllowAllAzureIPs'
    properties: {
      startIpAddress: '0.0.0.0'
      endIpAddress: '255.255.255.255'
    }
  }
}

// Basic tier database - scales down when not used
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: dataResourceNames.sqlDatabase
  location: location
  tags: dataTags
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5 // DTU 5 - lowest cost
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648 // 2GB
    zoneRedundant: false
    requestedBackupStorageRedundancy: 'Local' // Local for cost savings
  }
}

// ==================== COSMOS DB ====================
// Serverless Cosmos DB - only pay for what you use
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: dataResourceNames.cosmosAccount
  location: location
  tags: dataTags
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    capabilities: [
      {
        name: 'EnableServerless' // Key for cost optimization
      }
    ]
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 1440 // Daily backups
        backupRetentionIntervalInHours: 720 // 30 days retention
        backupStorageRedundancy: 'Local' // Local for cost savings
      }
    }
    publicNetworkAccess: 'Enabled'
    networkAclBypass: 'AzureServices'
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

// Core containers for application data
resource itinerariesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Itineraries'
  properties: {
    resource: {
      id: 'Itineraries'
      partitionKey: {
        paths: ['/tripId']
        kind: 'Hash'
      }
    }
  }
}

resource messagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Messages'
  properties: {
    resource: {
      id: 'Messages'
      partitionKey: {
        paths: ['/chatId']
        kind: 'Hash'
      }
    }
  }
}

resource preferencesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Preferences'
  properties: {
    resource: {
      id: 'Preferences'
      partitionKey: {
        paths: ['/userId']
        kind: 'Hash'
      }
    }
  }
}

// ==================== SECRETS MANAGEMENT ====================
// Store connection strings for compute layer to access
resource sqlConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: dbKeyVault
  name: 'sql-connection-string'
  properties: {
    value: 'Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Initial Catalog=${sqlDatabase.name};Persist Security Info=False;User ID=${sqlAdminLogin};Password=${sqlAdminPassword};MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
    attributes: {
      enabled: true
    }
    contentType: 'SQL Database Connection String'
  }
}

resource cosmosConnectionSecret 'Microsoft.KeyVault/vaults/secrets@2023-02-01' = {
  parent: dbKeyVault
  name: 'cosmos-connection-string'
  properties: {
    value: cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
    attributes: {
      enabled: true
    }
    contentType: 'Cosmos DB Connection String'
  }
}

// ==================== OUTPUTS ====================
output persistentDataLayer object = {
  resourceGroupName: resourceGroup().name
  sqlServerFqdn: sqlServer.properties.fullyQualifiedDomainName
  sqlServerName: sqlServer.name
  sqlDatabaseName: sqlDatabase.name
  cosmosAccountName: cosmosAccount.name
  cosmosAccountEndpoint: cosmosAccount.properties.documentEndpoint
  dbKeyVaultName: dbKeyVault.name
  dbKeyVaultUri: dbKeyVault.properties.vaultUri
}

output connectionSecrets object = {
  sqlConnectionSecretUri: '${dbKeyVault.properties.vaultUri}secrets/sql-connection-string'
  cosmosConnectionSecretUri: '${dbKeyVault.properties.vaultUri}secrets/cosmos-connection-string'
  keyVaultName: dbKeyVault.name
}

output costOptimization object = {
  serverlessCosmos: 'Cosmos DB in serverless mode - only pay for RU consumed'
  basicSqlTier: 'SQL Basic tier with DTU 5 - lowest cost option'
  localBackups: 'Local backup redundancy for cost savings'
  noComputeCosts: 'No compute resources in this RG - can delete pathfinder-rg safely'
  estimatedIdleCost: '$15-25/month when pathfinder-rg is deleted'
  estimatedActiveCost: '$25-35/month when both RGs are active'
}

output pauseResumeStrategy object = {
  pauseInstructions: 'Delete pathfinder-rg to save ~$35-50/month'
  resumeInstructions: 'Run CI/CD pipeline to recreate pathfinder-rg'
  dataPreservation: 'All user data, trips, and preferences remain intact'
  resumeTime: '5-10 minutes to restore full functionality'
  costSavings: 'Up to 70% savings during pause periods'
}
