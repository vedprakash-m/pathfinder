// Azure SignalR Service module - Free tier

@description('Azure region for resources')
param location string

@description('Unique suffix for resource names')
param uniqueSuffix string

@description('Environment name')
param environment string

// SignalR name
var signalRName = 'pf-signalr-${uniqueSuffix}'

// SignalR Service - Free tier
resource signalR 'Microsoft.SignalRService/signalR@2023-08-01-preview' = {
  name: signalRName
  location: location
  kind: 'SignalR'
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  sku: {
    name: 'Free_F1'
    tier: 'Free'
    capacity: 1
  }
  properties: {
    features: [
      {
        flag: 'ServiceMode'
        value: 'Serverless' // Serverless mode for Azure Functions
      }
      {
        flag: 'EnableConnectivityLogs'
        value: 'true'
      }
      {
        flag: 'EnableMessagingLogs'
        value: 'true'
      }
    ]
    cors: {
      allowedOrigins: [
        '*' // Will be restricted in production
      ]
    }
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
    disableAadAuth: false
  }
}

// Outputs
output signalRName string = signalR.name
output hostName string = signalR.properties.hostName
