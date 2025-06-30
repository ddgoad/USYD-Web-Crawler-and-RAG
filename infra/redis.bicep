@description('Azure Cache for Redis')
param cacheName string
param location string = resourceGroup().location
param tags object = {}

resource redisCache 'Microsoft.Cache/redis@2023-08-01' = {
  name: cacheName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    redisConfiguration: {
      'maxmemory-reserved': '30'
      'maxfragmentationmemory-reserved': '30'
    }
    enableNonSslPort: false
    redisVersion: '6'
    publicNetworkAccess: 'Enabled'
  }
}

output redisHostName string = redisCache.properties.hostName
output redisPort string = string(redisCache.properties.sslPort)