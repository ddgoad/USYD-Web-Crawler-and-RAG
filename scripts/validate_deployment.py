#!/usr/bin/env python3
"""
Deployment validation script for USYD Web Crawler and RAG Application
Validates all Azure services and application components are working correctly
"""

import os
import sys
import logging
import requests
import psycopg2
import redis
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test PostgreSQL database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("✗ DATABASE_URL environment variable not set")
            return False
        
        logger.info("Testing database connection...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        # Test our tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE';
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'scraping_jobs', 'vector_databases', 'chat_sessions', 'chat_messages']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"✗ Missing database tables: {missing_tables}")
            return False
        
        cursor.close()
        conn.close()
        
        logger.info("✓ Database connection successful")
        logger.info(f"  Database version: {version[0]}")
        logger.info(f"  Tables found: {len(tables)}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    try:
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            logger.error("✗ REDIS_URL environment variable not set")
            return False
        
        logger.info("Testing Redis connection...")
        r = redis.from_url(redis_url)
        
        # Test basic operations
        r.ping()
        r.set('test_key', 'test_value', ex=10)
        value = r.get('test_key')
        r.delete('test_key')
        
        if value.decode() != 'test_value':
            logger.error("✗ Redis test operation failed")
            return False
        
        logger.info("✓ Redis connection successful")
        logger.info(f"  Redis test operation completed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False

def test_azure_openai_connection():
    """Test Azure OpenAI connection"""
    try:
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_KEY')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2023-12-01-preview')
        
        if not endpoint or not api_key:
            logger.error("✗ Azure OpenAI environment variables not set")
            return False
        
        logger.info("Testing Azure OpenAI connection...")
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        
        # Test embeddings model
        try:
            response = client.embeddings.create(
                input="Test embedding",
                model="text-embedding-3-small"
            )
            if len(response.data[0].embedding) != 1536:
                logger.error("✗ Embedding model returned unexpected dimension")
                return False
            logger.info("✓ Embeddings model working")
        except Exception as e:
            logger.error(f"✗ Embeddings model test failed: {e}")
            return False
        
        # Test chat models
        models_to_test = [
            ("gpt-4o", os.getenv('AZURE_OPENAI_GPT4O_DEPLOYMENT', 'gpt-4o')),
            ("o3-mini", os.getenv('AZURE_OPENAI_O3_MINI_DEPLOYMENT', 'o3-mini'))
        ]
        
        for model_name, deployment_name in models_to_test:
            try:
                response = client.chat.completions.create(
                    model=deployment_name,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                if response.choices and response.choices[0].message.content:
                    logger.info(f"✓ {model_name} model working")
                else:
                    logger.error(f"✗ {model_name} model returned empty response")
                    return False
            except Exception as e:
                logger.error(f"✗ {model_name} model test failed: {e}")
                return False
        
        logger.info("✓ Azure OpenAI connection successful")
        return True
        
    except Exception as e:
        logger.error(f"✗ Azure OpenAI connection failed: {e}")
        return False

def test_azure_search_connection():
    """Test Azure AI Search connection"""
    try:
        endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        api_key = os.getenv('AZURE_SEARCH_KEY')
        
        if not endpoint or not api_key:
            logger.error("✗ Azure Search environment variables not set")
            return False
        
        logger.info("Testing Azure AI Search connection...")
        credential = AzureKeyCredential(api_key)
        index_client = SearchIndexClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # Test service access
        stats = index_client.get_service_statistics()
        logger.info("✓ Azure AI Search connection successful")
        logger.info(f"  Document count: {stats['counters']['document_count']}")
        logger.info(f"  Index count: {stats['counters']['index_count']}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Azure AI Search connection failed: {e}")
        return False

def test_application_health():
    """Test application health endpoint"""
    try:
        # Try to determine the application URL
        app_url = os.getenv('WEB_URI', 'http://localhost:5000')
        
        logger.info(f"Testing application health at {app_url}...")
        
        # Test health endpoint
        health_url = f"{app_url}/health"
        response = requests.get(health_url, timeout=30)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info("✓ Application health check passed")
            logger.info(f"  Status: {health_data.get('status', 'unknown')}")
            logger.info(f"  Version: {health_data.get('version', 'unknown')}")
            return True
        else:
            logger.error(f"✗ Health check failed with status {response.status_code}")
            return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Application health check failed: {e}")
        return False

def test_environment_variables():
    """Test that all required environment variables are set"""
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY',
        'AZURE_SEARCH_ENDPOINT', 
        'AZURE_SEARCH_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'FLASK_SECRET_KEY'
    ]
    
    logger.info("Checking environment variables...")
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            logger.info(f"✓ {var} is set")
    
    if missing_vars:
        logger.error(f"✗ Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✓ All required environment variables are set")
    return True

def run_full_validation():
    """Run complete validation suite"""
    
    logger.info("🚀 Starting USYD Web Crawler and RAG deployment validation...")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Database Connection", test_database_connection),
        ("Redis Connection", test_redis_connection),
        ("Azure OpenAI Connection", test_azure_openai_connection),
        ("Azure AI Search Connection", test_azure_search_connection),
        ("Application Health", test_application_health),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} test crashed: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 Validation Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All validation tests passed! Your deployment is ready.")
        return True
    else:
        logger.error(f"❌ {failed} test(s) failed. Please fix the issues before proceeding.")
        return False

def main():
    """Main validation function"""
    try:
        success = run_full_validation()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Validation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())