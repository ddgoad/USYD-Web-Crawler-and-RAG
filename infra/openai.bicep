@description('Azure OpenAI Service')
param openaiServiceName string
param location string = resourceGroup().location
param tags object = {}
param principalId string = ''

resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openaiServiceName
  location: location
  tags: tags
  kind: 'OpenAI'
  properties: {
    customSubDomainName: openaiServiceName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
  sku: {
    name: 'S0'
  }
}

// Deploy GPT-4o model
resource gpt4oDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openai
  name: 'gpt-4o'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: 10
  }
}

// Deploy o1-mini model
resource o1MiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openai
  name: 'o1-mini'
  dependsOn: [gpt4oDeployment]
  properties: {
    model: {
      format: 'OpenAI'
      name: 'o1-mini'
      version: '2024-09-12'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: 10
  }
}

// Deploy text-embedding-3-small model
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openai
  name: 'text-embedding-3-small'
  dependsOn: [o1MiniDeployment]
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
    raiPolicyName: 'Microsoft.Default'
  }
  sku: {
    name: 'Standard'
    capacity: 120
  }
}

// Assign Cognitive Services OpenAI User role to the principal
resource openaiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(openai.id, principalId, 'a97b65f3-24c7-4388-baec-2e87135dc908')
  scope: openai
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908') // Cognitive Services OpenAI User
    principalId: principalId
  }
}

output endpoint string = openai.properties.endpoint
output apiKey string = openai.listKeys().key1
output name string = openai.name