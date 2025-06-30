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

// Optional parameters to override the default azd resource naming conventions.
// Add the following to main.parameters.json to provide values:
// "resourceGroupName": {
//      "value": "myGroupName"
// }
param resourceGroupName string = ''

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName))
var tags = { 'azd-env-name': environmentName }

// Organize resources in a resource group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: !empty(resourceGroupName) ? resourceGroupName : '${abbrs.resourcesResourceGroups}${environmentName}'
  location: location
  tags: tags
}

// Container apps environment
module containerAppsEnvironment 'container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
  }
}

// PostgreSQL database
module database 'database.bicep' = {
  name: 'database'
  scope: rg
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
  scope: rg
  params: {
    cacheName: '${abbrs.cacheRedis}${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure OpenAI Service
module openai 'openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    openaiServiceName: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: location
    tags: tags
    principalId: principalId
  }
}

// Azure AI Search Service
module search 'search.bicep' = {
  name: 'search'
  scope: rg
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
  scope: rg
  params: {
    containerAppName: '${abbrs.appContainerApps}${resourceToken}'
    location: location
    environmentId: containerAppsEnvironment.outputs.environmentId
    imageName: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
    azureOpenAIEndpoint: openai.outputs.endpoint
    azureOpenAIKey: ''
    azureSearchEndpoint: search.outputs.endpoint
    azureSearchKey: ''
    databaseUrl: 'postgresql://${database.outputs.administratorLogin}@${database.outputs.serverFqdn}:5432/${database.outputs.databaseName}?sslmode=require'
    redisUrl: 'rediss://${redis.outputs.redisHostName}:${redis.outputs.redisPort}/0'
    secretKey: 'usyd-rag-secret-key-${resourceToken}'
    userAssignedIdentityId: containerAppsEnvironment.outputs.userAssignedIdentityId
    registryLoginServer: containerAppsEnvironment.outputs.registryLoginServer
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
output RESOURCE_GROUP_ID string = rg.id

// Service outputs
output AZURE_OPENAI_ENDPOINT string = openai.outputs.endpoint
output AZURE_SEARCH_ENDPOINT string = search.outputs.endpoint
output DATABASE_URL string = 'postgresql://${database.outputs.administratorLogin}@${database.outputs.serverFqdn}:5432/${database.outputs.databaseName}?sslmode=require'
output REDIS_URL string = 'rediss://${redis.outputs.redisHostName}:${redis.outputs.redisPort}/0'
output WEB_URI string = containerApp.outputs.containerAppUrl