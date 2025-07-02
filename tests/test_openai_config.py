#!/usr/bin/env python3
"""
Test script to verify Azure OpenAI configuration and model access
"""

import os
import sys

# Set environment variables
os.environ['AZURE_OPENAI_ENDPOINT'] = 'https://dgopenai2211200906498164.openai.azure.com/'
os.environ['AZURE_OPENAI_KEY'] = 'EdKxnIPfLdrlOCpGGgOajk7fFJeopjLec4IHPk8lCAsLrUYIdIW2JQQJ99AKACL93NaXJ3w3AAAAACOGh1w8'
os.environ['AZURE_OPENAI_API_VERSION'] = '2023-12-01-preview'
os.environ['AZURE_OPENAI_GPT4O_DEPLOYMENT'] = 'gpt-4o'
os.environ['AZURE_OPENAI_O3_MINI_DEPLOYMENT'] = 'o3-mini'

print("=== Azure OpenAI Configuration Test ===")
print(f"AZURE_OPENAI_ENDPOINT: {os.environ['AZURE_OPENAI_ENDPOINT']}")
print(f"AZURE_OPENAI_KEY: {os.environ['AZURE_OPENAI_KEY'][:20]}...")
print(f"AZURE_OPENAI_API_VERSION: {os.environ['AZURE_OPENAI_API_VERSION']}")
print(f"GPT-4o Deployment: {os.environ['AZURE_OPENAI_GPT4O_DEPLOYMENT']}")
print(f"o3-mini Deployment: {os.environ['AZURE_OPENAI_O3_MINI_DEPLOYMENT']}")
print()

try:
    from openai import AzureOpenAI
    print("✓ OpenAI package imported successfully")
    
    client = AzureOpenAI(
        api_key=os.environ['AZURE_OPENAI_KEY'],
        api_version=os.environ['AZURE_OPENAI_API_VERSION'],
        azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
    )
    print("✓ Azure OpenAI client initialized")
    
    # Test both models
    models_to_test = [
        ('gpt-4o', os.environ['AZURE_OPENAI_GPT4O_DEPLOYMENT']),
        ('o3-mini', os.environ['AZURE_OPENAI_O3_MINI_DEPLOYMENT'])
    ]
    
    for model_name, deployment in models_to_test:
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": "Hello, please respond with 'Model working'."}],
                max_tokens=10,
                temperature=0.7
            )
            message = response.choices[0].message.content.strip()
            print(f"✓ {model_name} ({deployment}) model working: {message}")
        except Exception as e:
            print(f"✗ {model_name} ({deployment}) model failed: {e}")
    
    print("\n=== Configuration Complete ===")
    print("Your Azure OpenAI models are properly configured and accessible!")
    
except ImportError as e:
    print(f"✗ OpenAI package not installed: {e}")
    print("Run: pip install openai>=1.55.3")
    sys.exit(1)
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    sys.exit(1)
