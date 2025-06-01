@description('Name of the static web app')
param appName string

@description('Location for resource')
param location string

@description('Resource tags')
param tags object

@description('Backend API URL')
param apiBackendUrl string

// Static Web App for frontend
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: appName
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

// App settings for Static Web App
resource staticWebAppSettings 'Microsoft.Web/staticSites/config@2022-09-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    REACT_APP_API_BASE_URL: apiBackendUrl
    VITE_API_URL: apiBackendUrl
    AUTH0_AUDIENCE: 'https://api.pathfinder.com'
    AUTH0_DOMAIN: 'dev-jwnud3v8ghqnyygr.us.auth0.com'
    APPLICATION_INSIGHTS_CONNECTION_STRING: ''
    ENVIRONMENT: 'production'
  }
}

// Output
output appUrl string = staticWebApp.properties.defaultHostname
output appName string = staticWebApp.name
