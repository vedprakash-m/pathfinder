// Azure Cosmos DB module - Serverless configuration
// IDEMPOTENT: Uses deterministic naming based on subscription

@description('Azure region for resources')
param location string

@description('Unique ID for globally unique resources')
param uniqueId string

@description('Environment name')
param environment string

// Cosmos DB account name - globally unique, deterministic per subscription
var cosmosAccountName = 'pf-cosmos-${uniqueId}'
var databaseName = 'pathfinder'
var containerName = 'data'

// Cosmos DB Account - Serverless
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: environment == 'dev' // Use free tier for dev
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
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
    backupPolicy: {
      type: 'Continuous'
      continuousModeProperties: {
        tier: 'Continuous7Days'
      }
    }
    publicNetworkAccess: 'Enabled'
  }
}

// Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Container with composite partition key strategy
resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: ['/pk']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/"_etag"/?'
          }
        ]
        compositeIndexes: [
          [
            { path: '/entity_type', order: 'ascending' }
            { path: '/created_at', order: 'descending' }
          ]
          [
            { path: '/entity_type', order: 'ascending' }
            { path: '/user_id', order: 'ascending' }
          ]
          [
            { path: '/entity_type', order: 'ascending' }
            { path: '/trip_id', order: 'ascending' }
          ]
        ]
      }
      defaultTtl: -1 // No automatic expiration
    }
  }
}

// Outputs
output accountName string = cosmosAccount.name
output endpoint string = cosmosAccount.properties.documentEndpoint
