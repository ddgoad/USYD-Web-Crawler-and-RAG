@description('Azure Storage Account for persistent file storage')
param storageAccountName string
param location string = resourceGroup().location
param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
}

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  name: 'scraped-data'
  parent: fileService
  properties: {
    shareQuota: 100
    enabledProtocols: 'SMB'
  }
}

output storageAccountName string = storageAccount.name
output fileShareName string = fileShare.name
output storageAccountId string = storageAccount.id
output storageAccountUrl string = storageAccount.properties.primaryEndpoints.blob
