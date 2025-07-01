"""
Vector Database Service for USYD Web Crawler and RAG Application
Integrates with Azure AI Search for vector storage and retrieval
"""

import os
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
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
from openai import AzureOpenAI
import tiktoken

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/usydrag")
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self.search_key = os.getenv("AZURE_SEARCH_KEY", "")
        
        # Azure OpenAI for embeddings
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "")
        )
        
        # Initialize search clients
        self.credential = AzureKeyCredential(self.search_key)
        self.index_client = SearchIndexClient(
            endpoint=self.search_endpoint,
            credential=self.credential
        )
        
        # Initialize tokenizer for text chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create vector_databases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_databases (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    index_name VARCHAR(255) UNIQUE NOT NULL,
                    scraping_job_id VARCHAR(36),
                    document_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending'
                );
            """)
            
            # Create vector_documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_documents (
                    id VARCHAR(36) PRIMARY KEY,
                    database_id VARCHAR(36) REFERENCES vector_databases(id) ON DELETE CASCADE,
                    title VARCHAR(500),
                    content TEXT NOT NULL,
                    url VARCHAR(2048),
                    metadata JSONB,
                    chunk_index INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            conn.close()
            logger.info("Vector store database initialized successfully")
        except Exception as e:
            logger.error(f"Vector store database initialization failed: {str(e)}")
            # Don't raise, as this shouldn't prevent the app from starting
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Break if this is the last chunk
            if i + chunk_size >= len(tokens):
                break
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            embeddings = []
            batch_size = 10  # Process in batches to avoid rate limits
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model="text-embedding-3-small"  # Azure OpenAI embedding model
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def _create_search_index(self, index_name: str) -> bool:
        """Create Azure AI Search index"""
        try:
            # Define the search index schema
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
            
            # Create the search index
            index = SearchIndex(
                name=index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            self.index_client.create_index(index)
            logger.info(f"Created search index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create search index {index_name}: {str(e)}")
            return False
    
    def create_database(self, user_id: int, name: str, scraping_job_id: str) -> str:
        """Create vector database from scraping job"""
        try:
            db_id = str(uuid.uuid4())
            
            # Get scraping job data
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM scraping_jobs 
                WHERE id = %s AND user_id = %s AND status = 'completed';
            """, (scraping_job_id, user_id))
            
            job = cursor.fetchone()
            if not job:
                raise Exception("Scraping job not found or not completed")
            
            # Create Azure Search index
            azure_index_name = f"usyd-rag-{db_id}"
            if not self._create_search_index(azure_index_name):
                raise Exception("Failed to create search index")
            
            # Create vector database record
            cursor.execute("""
                INSERT INTO vector_databases (id, user_id, name, source_url, azure_index_name, status)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (db_id, user_id, name, job['url'], azure_index_name, 'building'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Process scraped data in background task
            from services.vector_store import process_vector_database_creation
            process_vector_database_creation.delay(db_id, scraping_job_id)
            
            logger.info(f"Created vector database {db_id} for user {user_id}")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to create vector database: {str(e)}")
            raise
    
    def _process_scraped_data_async(self, db_id: str, scraping_job_id: str):
        """Process scraped data and add to vector database"""
        try:
            # Load scraped data
            data_file = f"data/raw/{scraping_job_id}/scraped_data.json"
            if not os.path.exists(data_file):
                raise Exception("Scraped data file not found")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            # Get database record
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM vector_databases WHERE id = %s;
            """, (db_id,))
            
            db_record = cursor.fetchone()
            if not db_record:
                raise Exception("Vector database record not found")
            
            azure_index_name = db_record['azure_index_name']
            
            # Create search client for this index
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=azure_index_name,
                credential=self.credential
            )
            
            # Process documents
            documents = []
            document_count = 0
            
            if scraped_data['success']:
                results = scraped_data.get('results', [])
                if not isinstance(results, list):
                    results = [scraped_data]  # Single page result
                
                for result in results:
                    if not result.get('content'):
                        continue
                    
                    # Chunk the content
                    chunks = self._chunk_text(result['content'])
                    
                    # Generate embeddings for chunks
                    embeddings = self._generate_embeddings(chunks)
                    
                    # Create documents for each chunk
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        doc_id = f"{db_id}_{document_count}_{i}"
                        
                        document = {
                            "id": doc_id,
                            "content": chunk,
                            "title": result.get('title', ''),
                            "url": result.get('url', ''),
                            "chunk_index": i,
                            "source_type": "web_scraped",
                            "metadata": json.dumps(result.get('metadata', {})),
                            "content_vector": embedding
                        }
                        
                        documents.append(document)
                    
                    document_count += 1
            
            # Upload documents to Azure Search
            if documents:
                # Upload in batches
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    search_client.upload_documents(documents=batch)
                
                logger.info(f"Uploaded {len(documents)} document chunks to index {azure_index_name}")
            
            # Update database record
            cursor.execute("""
                UPDATE vector_databases 
                SET status = %s, document_count = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, ('ready', document_count, db_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Vector database {db_id} is ready with {document_count} documents")
            
        except Exception as e:
            logger.error(f"Failed to process scraped data for database {db_id}: {str(e)}")
            
            # Update status to error
            try:
                conn = self._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE vector_databases 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, ('error', db_id))
                conn.commit()
                cursor.close()
                conn.close()
            except:
                pass
    
    def get_user_databases(self, user_id: int) -> List[Dict]:
        """Get all vector databases for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM vector_databases 
                WHERE user_id = %s 
                ORDER BY created_at DESC;
            """, (user_id,))
            
            databases = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(db) for db in databases]
            
        except Exception as e:
            logger.error(f"Failed to get user databases: {str(e)}")
            return []
    
    def delete_database(self, db_id: str, user_id: int) -> bool:
        """Delete vector database and its Azure Search index"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get database record
            cursor.execute("""
                SELECT * FROM vector_databases 
                WHERE id = %s AND user_id = %s;
            """, (db_id, user_id))
            
            db_record = cursor.fetchone()
            if not db_record:
                return False
            
            # Delete Azure Search index
            try:
                self.index_client.delete_index(db_record['azure_index_name'])
                logger.info(f"Deleted Azure Search index: {db_record['azure_index_name']}")
            except Exception as e:
                logger.warning(f"Failed to delete Azure Search index: {str(e)}")
            
            # Delete database record
            cursor.execute("""
                DELETE FROM vector_databases WHERE id = %s;
            """, (db_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Deleted vector database {db_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector database: {str(e)}")
            return False
    
    def search(self, db_id: str, user_id: int, query: str, search_type: str = "semantic", top_k: int = 5) -> List[Dict]:
        """Search in vector database"""
        try:
            # Get database record
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM vector_databases 
                WHERE id = %s AND user_id = %s AND status = 'ready';
            """, (db_id, user_id))
            
            db_record = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not db_record:
                raise Exception("Vector database not found or not ready")
            
            azure_index_name = db_record['azure_index_name']
            
            # Create search client
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=azure_index_name,
                credential=self.credential
            )
            
            results = []
            
            if search_type == "semantic" or search_type == "hybrid":
                # Vector search
                query_embedding = self._generate_embeddings([query])[0]
                
                vector_query = VectorizedQuery(
                    vector=query_embedding,
                    k_nearest_neighbors=top_k,
                    fields="content_vector"
                )
                
                if search_type == "semantic":
                    search_results = search_client.search(
                        search_text=None,
                        vector_queries=[vector_query],
                        top=top_k
                    )
                else:  # hybrid
                    search_results = search_client.search(
                        search_text=query,
                        vector_queries=[vector_query],
                        top=top_k
                    )
                
                for result in search_results:
                    results.append({
                        'content': result['content'],
                        'title': result['title'],
                        'url': result['url'],
                        'score': result.get('@search.score', 0),
                        'metadata': json.loads(result.get('metadata', '{}'))
                    })
            
            elif search_type == "keyword":
                # Text search only
                search_results = search_client.search(
                    search_text=query,
                    top=top_k
                )
                
                for result in search_results:
                    results.append({
                        'content': result['content'],
                        'title': result['title'],
                        'url': result['url'],
                        'score': result.get('@search.score', 0),
                        'metadata': json.loads(result.get('metadata', '{}'))
                    })
            
            logger.info(f"Search in database {db_id} returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search in database {db_id}: {str(e)}")
            return []


# Import celery after the class definition to avoid circular imports
from celery import Celery

# Initialize Celery for this module
celery = Celery(
    'vector_store',
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

@celery.task(bind=True)
def process_vector_database_creation(self, db_id: str, scraping_job_id: str):
    """Celery task for processing vector database creation"""
    try:
        logger.info(f"Starting vector database processing for {db_id}")
        
        service = VectorStoreService()
        service._process_scraped_data_async(db_id, scraping_job_id)
        
        logger.info(f"Vector database processing completed for {db_id}")
        return {"status": "completed", "db_id": db_id}
        
    except Exception as e:
        logger.error(f"Vector database processing failed for {db_id}: {str(e)}")
        
        # Update database status to error
        try:
            service = VectorStoreService()
            conn = service._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vector_databases 
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, ('error', db_id))
            conn.commit()
            cursor.close()
            conn.close()
        except:
            pass
        
        raise