targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Name of the resource group to deploy resources to')
param resourceGroupName string = 'rg-${environmentName}'

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName))
var tags = { 'azd-env-name': environmentName }

// Create resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// Storage Account for persistent data - moved up to be available for other modules
module storage 'storage.bicep' = {
  name: 'storage'
  scope: resourceGroup
  params: {
    storageAccountName: 'st${resourceToken}'
    location: location
    tags: tags
  }
}

// Container apps environment
module containerAppsEnvironment 'container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  scope: resourceGroup
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    storageAccountName: storage.outputs.storageAccountName
    fileShareName: storage.outputs.fileShareName
    tags: tags
  }
}

// PostgreSQL database
module database 'database.bicep' = {
  name: 'database'
  scope: resourceGroup
  params: {
    serverName: '${abbrs.dBforPostgreSQLServers}${resourceToken}'
    location: location
    administratorLogin: 'usydragadmin'
    administratorPassword: 'P@ssw0rd123!${resourceToken}'
    tags: tags
  }
}

// Redis Cache
module redis 'redis.bicep' = {
  name: 'redis'
  scope: resourceGroup
  params: {
    cacheName: '${abbrs.cacheRedis}${resourceToken}'
    location: location
    tags: tags
  }
}

// Note: Azure OpenAI Service is pre-provisioned and accessed via environment variables

// Azure AI Search Service
module search 'search.bicep' = {
  name: 'search'
  scope: resourceGroup
  params: {
    searchServiceName: '${abbrs.searchSearchServices}${resourceToken}'
    location: location
    tags: tags
    principalId: principalId
  }
}

// Container App
module containerApp 'containerapp.bicep' = {
  name: 'containerapp'
  scope: resourceGroup
  params: {
    containerAppName: '${abbrs.appContainerApps}${resourceToken}'
    location: location
    environmentId: containerAppsEnvironment.outputs.environmentId
    imageName: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
    azureOpenAIEndpoint: 'https://dgopenai2211200906498164.openai.azure.com/'
    azureOpenAIKey: 'EdKxnIPfLdrlOCpGGgOajk7fFJeopjLec4IHPk8lCAsLrUYIdIW2JQQJ99AKACL93NaXJ3w3AAAAACOGh1w8'
    azureSearchEndpoint: search.outputs.endpoint
    azureSearchName: search.outputs.name
    databaseUrl: 'postgresql://${database.outputs.administratorLogin}:P%40ssw0rd123%21${resourceToken}@${database.outputs.serverFqdn}:5432/${database.outputs.databaseName}?sslmode=require'
    redisName: redis.outputs.redisName
    redisHostName: redis.outputs.redisHostName
    redisPort: redis.outputs.redisPort
    secretKey: 'usyd-rag-secret-key-${resourceToken}'
    userAssignedIdentityId: containerAppsEnvironment.outputs.userAssignedIdentityId
    registryLoginServer: containerAppsEnvironment.outputs.registryLoginServer
    storageAccountName: storage.outputs.storageAccountName
    tags: tags
  }
}

// App outputs
output APPLICATIONINSIGHTS_CONNECTION_STRING string = containerAppsEnvironment.outputs.appInsightsConnectionString
output AZURE_CONTAINER_APPS_ENVIRONMENT_ID string = containerAppsEnvironment.outputs.environmentId
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerAppsEnvironment.outputs.registryLoginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerAppsEnvironment.outputs.registryName
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output RESOURCE_GROUP_ID string = resourceGroup.id

// Service outputs
output AZURE_OPENAI_ENDPOINT string = 'https://dgopenai2211200906498164.openai.azure.com/'
output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output AZURE_STORAGE_ACCOUNT_URL string = storage.outputs.storageAccountUrl
output DATABASE_URL string = 'postgresql://[secret]@${database.outputs.serverFqdn}:5432/${database.outputs.databaseName}?sslmode=require'
output REDIS_URL string = 'rediss://[secret]@${redis.outputs.redisHostName}:${redis.outputs.redisPort}/0'
output WEB_URI string = containerApp.outputs.containerAppUrl
