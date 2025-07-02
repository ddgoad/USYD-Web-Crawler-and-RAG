@description('Container App Configuration')
param containerAppName string
param location string = resourceGroup().location
param environmentId string
param imageName string
param azureOpenAIEndpoint string
@secure()
param azureOpenAIKey string
param azureSearchEndpoint string
@secure()
param azureSearchKey string
@secure()
param databaseUrl string
@secure()
param redisUrl string
@secure()
param secretKey string
param userAssignedIdentityId string
param registryLoginServer string
param storageAccountName string
param tags object = {}

// Get storage account key directly within this module
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: union(tags, {
    'azd-service-name': 'web'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: registryLoginServer
          identity: userAssignedIdentityId
        }
      ]
      ingress: {
        external: true
        targetPort: 5000
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
        }
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
      }
      secrets: [
        {
          name: 'azure-openai-key'
          value: azureOpenAIKey
        }
        {
          name: 'azure-search-key'
          value: azureSearchKey
        }
        {
          name: 'database-url'
          value: databaseUrl
        }
        {
          name: 'redis-url'  
          value: redisUrl
        }
        {
          name: 'secret-key'
          value: secretKey
        }
        {
          name: 'storage-account-key'
          value: storageAccount.listKeys().keys[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          image: imageName
          name: 'usyd-web-crawler'
          env: [
            {
              name: 'AZURE_OPENAI_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_SEARCH_KEY'
              secretRef: 'azure-search-key'
            }
            {
              name: 'DATABASE_URL'
              secretRef: 'database-url'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-url'
            }
            {
              name: 'FLASK_SECRET_KEY'
              secretRef: 'secret-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: azureSearchEndpoint
            }
            {
              name: 'FLASK_ENV'
              value: 'production'
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: '2023-12-01-preview'
            }
            {
              name: 'AZURE_OPENAI_GPT4O_DEPLOYMENT'
              value: 'gpt-4o'
            }
            {
              name: 'AZURE_OPENAI_O3_MINI_DEPLOYMENT'
              value: 'o3-mini'
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
              value: 'text-embedding-3-small'
            }
            {
              name: 'PORT'
              value: '5000'
            }
          ]
          volumeMounts: [
            {
              volumeName: 'scraped-data-volume'
              mountPath: '/app/data'
            }
          ]
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 5000
              }
              initialDelaySeconds: 30
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 5000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
            }
          ]
        }
      ]
      volumes: [
        {
          name: 'scraped-data-volume'
          storageType: 'AzureFile'
          storageName: 'scraped-data-storage'
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output containerAppName string = containerApp.name
