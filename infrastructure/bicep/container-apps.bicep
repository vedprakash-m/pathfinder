@description('Name of the container app')
param appName string

@description('Container app environment resource ID')
param containerEnvId string

@description('Location for resources')
param location string

@description('Resource tags')
param tags object

@description('Cosmos DB connection string')
@secure()
param cosmosConnectionString string

@description('SQL Database connection string')
@secure()
param sqlConnectionString string

@description('OpenAI API key')
@secure()
param openAIApiKey string = ''

@description('Application Insights connection string')
@secure()
param appInsightsConnectionString string

@description('Storage account connection string')
@secure()
param storageAccountConnectionString string

@description('Image to deploy')
param image string = 'ghcr.io/vedprakashmishra/pathfinder-backend:latest'

@description('Target port for the application')
param targetPort int = 8000

// Backend Container App with auto-scaling
resource backendApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerEnvId
    configuration: {
      secrets: [
        {
          name: 'cosmos-connection-string'
          value: cosmosConnectionString
        }
        {
          name: 'sql-connection-string'
          value: sqlConnectionString
        }
        {
          name: 'openai-api-key'
          value: openAIApiKey
        }
        {
          name: 'app-insights-connection-string'
          value: appInsightsConnectionString
        }
        {
          name: 'storage-connection-string'
          value: storageAccountConnectionString
        }
      ]
      ingress: {
        external: true
        targetPort: targetPort
        allowInsecure: false
        transport: 'auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      registries: []
      activeRevisionsMode: 'Multiple'
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: image
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'COSMOS_CONNECTION_STRING'
              secretRef: 'cosmos-connection-string'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'sql-connection-string'
            }
            {
              name: 'OPENAI_API_KEY'
              secretRef: 'openai-api-key'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'app-insights-connection-string'
            }
            {
              name: 'STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'LOG_LEVEL'
              value: 'info'
            }
          ]
          probes: [
            {
              type: 'startup'
              httpGet: {
                path: '/api/health'
                port: targetPort
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'liveness'
              httpGet: {
                path: '/api/health'
                port: targetPort
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 5
            }
            {
              type: 'readiness'
              httpGet: {
                path: '/api/health/ready'
                port: targetPort
              }
              initialDelaySeconds: 15
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
          {
            name: 'cpu-scaling'
            custom: {
              type: 'cpu'
              metadata: {
                type: 'Utilization'
                value: '70'
              }
            }
          }
        ]
      }
    }
  }
}

output appUrl string = backendApp.properties.configuration.ingress.fqdn
output appName string = backendApp.name
