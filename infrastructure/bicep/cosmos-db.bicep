@description('Cosmos DB account name')
param accountName string

@description('Location for resource')
param location string

@description('Resource tags')
param tags object

// Cosmos DB Account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: accountName
  location: location
  tags: tags
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxStalenessPrefix: 100
      maxIntervalInSeconds: 300
    }
    enableAutomaticFailover: true
    enableMultipleWriteLocations: false
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 720
      }
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
  }
}

// SQL Database (container)
resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosDbAccount
  name: 'PathfinderDB'
  properties: {
    resource: {
      id: 'PathfinderDB'
    }
  }
}

// Containers for different data types
resource itinerariesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'Itineraries'
  properties: {
    resource: {
      id: 'Itineraries'
      partitionKey: {
        paths: ['/tripId_segmentId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

resource messagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'ChatMessages'
  properties: {
    resource: {
      id: 'ChatMessages'
      partitionKey: {
        paths: ['/tripId_date']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

resource statusContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'LiveStatus'
  properties: {
    resource: {
      id: 'LiveStatus'
      partitionKey: {
        paths: ['/tripId_familyId']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
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
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

resource aiCacheContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'AICache'
  properties: {
    resource: {
      id: 'AICache'
      partitionKey: {
        paths: ['/cacheKey_type']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/response/*'
          }
        ]
      },
      defaultTtl: 86400  // 24 hours
    }
  }
}

// Outputs
output accountName string = cosmosDbAccount.name
output databaseName string = cosmosDatabase.name
output connectionString string = listConnectionStrings(cosmosDbAccount.id, cosmosDbAccount.apiVersion).connectionStrings[0].connectionString
