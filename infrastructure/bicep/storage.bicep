@description('Storage account name')
param accountName string

@description('Location for resource')
param location string

@description('Resource tags')
param tags object

// Storage account for file storage
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

// Container for trip documents (itineraries, PDFs)
resource tripDocumentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/trip-documents'
  properties: {
    publicAccess: 'None'
  }
}

// Container for user uploads (profile pictures)
resource userUploadsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  name: '${storageAccount.name}/default/user-uploads'
  properties: {
    publicAccess: 'None'
  }
}

// Configure lifecycle management for blob storage
resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: true
    changeFeed: {
      enabled: true
      retentionInDays: 7
    }
  }
}

// Output
output connectionString string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
output accountName string = storageAccount.name
