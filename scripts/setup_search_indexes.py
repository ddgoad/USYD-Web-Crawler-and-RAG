#!/usr/bin/env python3
"""
Azure AI Search index setup script for USYD Web Crawler and RAG Application
Creates the default search index configuration and validates the setup
"""

import os
import sys
import logging
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchField,
    VectorSearchAlgorithmKind,
)
from azure.core.credentials import AzureKeyCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_search_config():
    """Get Azure Search configuration from environment"""
    config = {
        'endpoint': os.getenv('AZURE_SEARCH_ENDPOINT', ''),
        'key': os.getenv('AZURE_SEARCH_KEY', ''),
    }
    
    if not config['endpoint']:
        raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is required")
    if not config['key']:
        raise ValueError("AZURE_SEARCH_KEY environment variable is required")
    
    return config

def create_search_index_schema():
    """Create the standard search index schema for USYD RAG"""
    
    # Define the search index fields
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
        SearchField(name="title", type=SearchFieldDataType.String, searchable=True, filterable=True),
        SearchField(name="url", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True),
        SearchField(name="source_type", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="metadata", type=SearchFieldDataType.String, searchable=True),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # text-embedding-3-small dimension
            vector_search_profile_name="default-vector-profile"
        ),
    ]
    
    # Configure vector search
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="default-hnsw-algorithm",
                kind=VectorSearchAlgorithmKind.HNSW,
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="default-vector-profile",
                algorithm_configuration_name="default-hnsw-algorithm"
            )
        ]
    )
    
    return fields, vector_search

def create_test_index(index_client):
    """Create a test index to validate the configuration"""
    test_index_name = "usyd-rag-test-index"
    
    try:
        fields, vector_search = create_search_index_schema()
        
        # Create the search index
        index = SearchIndex(
            name=test_index_name,
            fields=fields,
            vector_search=vector_search
        )
        
        logger.info(f"Creating test index: {test_index_name}")
        index_client.create_index(index)
        logger.info("✓ Test index created successfully")
        
        # Validate the index
        created_index = index_client.get_index(test_index_name)
        logger.info(f"✓ Test index validated: {created_index.name}")
        
        # Clean up - delete the test index
        index_client.delete_index(test_index_name)
        logger.info("✓ Test index cleaned up")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create test index: {e}")
        
        # Try to clean up if index was partially created
        try:
            index_client.delete_index(test_index_name)
        except:
            pass
        
        return False

def validate_search_service(index_client):
    """Validate the search service configuration"""
    
    try:
        # Get service statistics
        stats = index_client.get_service_statistics()
        logger.info(f"✓ Search service is accessible")
        logger.info(f"  Storage used: {stats['counters']['storage_size']} bytes")
        logger.info(f"  Documents: {stats['counters']['document_count']}")
        logger.info(f"  Indexes: {stats['counters']['index_count']}")
        
        # List existing indexes
        indexes = index_client.list_indexes()
        existing_indexes = [idx.name for idx in indexes]
        logger.info(f"  Existing indexes: {len(existing_indexes)}")
        for idx_name in existing_indexes:
            logger.info(f"    - {idx_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Search service validation failed: {e}")
        return False

def validate_vector_search_support(index_client):
    """Validate that the search service supports vector search"""
    
    try:
        # Try to create a simple vector search index to test support
        test_fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(
                name="test_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=3,
                vector_search_profile_name="test-profile"
            ),
        ]
        
        test_vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="test-algorithm",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    parameters={"m": 4, "efConstruction": 400, "efSearch": 500, "metric": "cosine"}
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="test-profile",
                    algorithm_configuration_name="test-algorithm"
                )
            ]
        )
        
        test_index = SearchIndex(
            name="vector-support-test",
            fields=test_fields,
            vector_search=test_vector_search
        )
        
        # Try to create the index
        index_client.create_index(test_index)
        logger.info("✓ Vector search is supported")
        
        # Clean up
        index_client.delete_index("vector-support-test")
        
        return True
        
    except Exception as e:
        logger.error(f"Vector search validation failed: {e}")
        logger.error("❌ This search service may not support vector search")
        logger.error("   Please ensure you're using a supported Azure AI Search tier")
        return False

def main():
    """Main setup function"""
    try:
        logger.info("Starting Azure AI Search setup validation...")
        
        # Get configuration
        config = get_search_config()
        logger.info(f"Search endpoint: {config['endpoint']}")
        
        # Initialize search client
        credential = AzureKeyCredential(config['key'])
        index_client = SearchIndexClient(
            endpoint=config['endpoint'],
            credential=credential
        )
        
        # Validate search service
        logger.info("Validating search service...")
        if not validate_search_service(index_client):
            logger.error("❌ Search service validation failed")
            return 1
        
        # Validate vector search support
        logger.info("Validating vector search support...")
        if not validate_vector_search_support(index_client):
            logger.error("❌ Vector search validation failed")
            return 1
        
        # Create and test index schema
        logger.info("Testing index schema...")
        if not create_test_index(index_client):
            logger.error("❌ Index schema test failed")
            return 1
        
        logger.info("✅ Azure AI Search setup validation completed successfully!")
        logger.info("🚀 Your search service is ready for the USYD Web Crawler and RAG application")
        
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())