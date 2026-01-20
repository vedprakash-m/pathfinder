// Azure Static Web Apps module - Free tier

@description('Azure region for resources')
param location string = 'westus2'

@description('Unique suffix for resource names')
param uniqueSuffix string

@description('Environment name')
param environment string

@description('Function App URL for API proxy')
param functionAppUrl string

// Static Web App name
var staticWebAppName = 'pf-swa-${uniqueSuffix}'

// Static Web App - Free tier
resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticWebAppName
  location: location // Note: SWA has limited region availability
  tags: {
    project: 'pathfinder'
    environment: environment
  }
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    stagingEnvironmentPolicy: 'Enabled'
    allowConfigFileUpdates: true
    buildProperties: {
      appLocation: 'frontend'
      apiLocation: '' // No API in SWA, using linked Functions
      outputLocation: 'dist'
      appBuildCommand: 'npm run build'
    }
  }
}

// Static Web App configuration
resource staticWebAppConfig 'Microsoft.Web/staticSites/config@2023-12-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_URL: functionAppUrl
    VITE_ENTRA_EXTERNAL_TENANT_ID: 'vedid.onmicrosoft.com'
    // Client ID will be set during deployment
  }
}

// Link to backend Function App
resource linkedBackend 'Microsoft.Web/staticSites/linkedBackends@2023-12-01' = {
  parent: staticWebApp
  name: 'backend'
  properties: {
    backendResourceId: resourceId('Microsoft.Web/sites', 'pf-func-${uniqueSuffix}')
    region: location
  }
}

// Outputs
output staticWebAppName string = staticWebApp.name
output defaultHostname string = staticWebApp.properties.defaultHostname
