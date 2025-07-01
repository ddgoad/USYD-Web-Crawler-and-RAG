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

# Import Celery for background tasks
try:
    from celery import Celery
    from worker import celery_app
    CELERY_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Celery not available, falling back to threading")
    CELERY_AVAILABLE = False

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
            
            # Drop and recreate tables to ensure correct schema
            cursor.execute("DROP TABLE IF EXISTS vector_documents CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS vector_databases CASCADE;")
            
            # Create vector_databases table
            cursor.execute("""
                CREATE TABLE vector_databases (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    source_url VARCHAR(2048),
                    index_name VARCHAR(255) UNIQUE NOT NULL,
                    scraping_job_id VARCHAR(36),
                    document_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending'
                );
            """)
            
            # Create vector_documents table
            cursor.execute("""
                CREATE TABLE vector_documents (
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
        """Create vector database from scraping job (synchronous)"""
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
                INSERT INTO vector_databases 
                (id, user_id, job_id, name, source_url, azure_index_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (db_id, user_id, scraping_job_id, name, job['url'], azure_index_name, 'building'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Process scraped data immediately
            self._process_scraped_data_async(db_id, scraping_job_id)
            
            logger.info(f"Created vector database {db_id} for user {user_id}")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to create vector database: {str(e)}")
            raise

    def create_database_async(self, user_id: int, name: str, 
                             scraping_job_id: str) -> str:
        """Create vector database from scraping job (async processing)"""
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
                INSERT INTO vector_databases
                (id, user_id, job_id, name, source_url, azure_index_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (db_id, user_id, scraping_job_id, name, job['url'], azure_index_name, 
                  'building'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Start processing in background thread
            self._start_vector_processing_background(db_id, scraping_job_id)
            
            logger.info(f"Created vector database {db_id} for user "
                       f"{user_id} (async)")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to create vector database: {str(e)}")
            raise

    def _start_vector_processing_background(self, db_id: str, 
                                          scraping_job_id: str):
        """Start vector database processing using Celery or background thread"""
        if CELERY_AVAILABLE:
            # Use Celery for proper async processing
            try:
                task = create_vector_database_async_task.delay(db_id, scraping_job_id)
                logger.info(f"Started Celery task {task.id} for vector DB {db_id}")
                return task.id
            except Exception as e:
                logger.error(f"Failed to start Celery task: {e}")
                # Fall back to threading
                self._start_processing_with_threading(db_id, scraping_job_id)
        else:
            # Fall back to threading when Celery is not available
            self._start_processing_with_threading(db_id, scraping_job_id)
            
    def _start_processing_with_threading(self, db_id: str, scraping_job_id: str):
        """Fallback method using threading when Celery is not available"""
        def process_vector_db():
            try:
                logger.info("Starting background vector processing (threading)")
                self._process_scraped_data_async(db_id, scraping_job_id)
                logger.info("Background vector processing completed")
            except Exception as e:
                logger.error(f"Error in background vector processing: "
                           f"{str(e)}", exc_info=True)
                # Update status to failed
                try:
                    conn = self._get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE vector_databases 
                        SET status = %s
                        WHERE id = %s;
                    """, ('error', db_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                except Exception as db_error:
                    logger.error(f"Failed to update vector DB status: "
                               f"{db_error}")
        
        import threading
        thread = threading.Thread(target=process_vector_db)
        thread.daemon = True
        thread.start()
        logger.info(f"Started background thread for vector DB {db_id}")
    
    def _process_scraped_data_async(self, db_id: str, scraping_job_id: str):
        """Process scraped data and add to vector database"""
        try:
            # Load scraped data
            data_file = f"data/raw/{scraping_job_id}/scraped_data.json"
            if not os.path.exists(data_file):
                raise Exception(f"Scraped data file not found: {data_file}")
            
            logger.info(f"Loading scraped data from {data_file}")
            
            with open(data_file, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)
            
            logger.info(f"Loaded scraped data: {type(scraped_data)}, success: {scraped_data.get('success', 'N/A')}")
            
            # Get database record
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM vector_databases WHERE id = %s;
            """, (db_id,))
            
            db_record = cursor.fetchone()
            if not db_record:
                raise Exception("Vector database record not found")
            
            azure_index_name = db_record['index_name']
            logger.info(f"Processing data for Azure index: {azure_index_name}")
            
            # Create search client for this index
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=azure_index_name,
                credential=self.credential
            )
            
            # Process documents
            documents = []
            document_count = 0
            
            if scraped_data.get('success'):
                # Handle both single page and multi-page results
                if 'results' in scraped_data and isinstance(scraped_data['results'], list):
                    # Deep crawl results
                    results = scraped_data['results']
                    logger.info(f"Processing {len(results)} pages from deep crawl")
                elif 'content' in scraped_data:
                    # Single page result
                    results = [scraped_data]
                    logger.info("Processing single page result")
                else:
                    logger.warning("No valid content found in scraped data")
                    results = []
                
                for result in results:
                    content = result.get('content', '')
                    if not content or not content.strip():
                        logger.warning(f"Skipping page with no content: {result.get('url', 'unknown')}")
                        continue
                    
                    logger.info(f"Processing page: {result.get('url', 'unknown')} with {len(content)} characters")
                    
                    # Chunk the content
                    chunks = self._chunk_text(content)
                    logger.info(f"Created {len(chunks)} chunks")
                    
                    # Generate embeddings for chunks
                    try:
                        embeddings = self._generate_embeddings(chunks)
                        logger.info(f"Generated {len(embeddings)} embeddings")
                    except Exception as e:
                        logger.error(f"Failed to generate embeddings: {str(e)}")
                        continue
                    
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
            else:
                error_msg = scraped_data.get('error', 'Unknown error in scraped data')
                raise Exception(f"Scraped data indicates failure: {error_msg}")
            
            # Upload documents to Azure Search
            if documents:
                logger.info(f"Uploading {len(documents)} document chunks to Azure Search")
                # Upload in batches
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    try:
                        search_client.upload_documents(documents=batch)
                        logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
                    except Exception as e:
                        logger.error(f"Failed to upload batch {i//batch_size + 1}: {str(e)}")
                        raise
                
                logger.info(f"Successfully uploaded all {len(documents)} document chunks to index {azure_index_name}")
            else:
                logger.warning("No documents to upload - no valid content found")
            
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
            logger.error(f"Failed to process scraped data for database {db_id}: {str(e)}", exc_info=True)
            
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
                logger.info(f"Updated vector database {db_id} status to error")
            except Exception as db_error:
                logger.error(f"Failed to update database status to error: {str(db_error)}")
    
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
                self.index_client.delete_index(db_record['index_name'])
                logger.info(f"Deleted Azure Search index: {db_record['index_name']}")
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
            
            azure_index_name = db_record['index_name']
            
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

    def get_database_status(self, db_id: str, user_id: int) -> Optional[Dict]:
        """Get vector database status for non-blocking progress polling"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, document_count, created_at, updated_at
                FROM vector_databases 
                WHERE id = %s AND user_id = %s;
            """, (db_id, user_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'status': result[0],
                    'document_count': result[1] or 0,
                    'created_at': result[2].isoformat() if result[2] else None,
                    'updated_at': result[3].isoformat() if result[3] else None
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get database status for {db_id}: {str(e)}")
            return None


# Celery task for asynchronous vector database creation
if CELERY_AVAILABLE:
    @celery_app.task(bind=True)
    def create_vector_database_async_task(self, db_id: str, scraping_job_id: str):
        """Celery task for asynchronous vector database creation"""
        try:
            # Create a new instance of VectorStoreService for the task
            service = VectorStoreService()
            
            # Update task status to STARTED
            self.update_state(state='STARTED', meta={'progress': 0, 'status': 'Processing scraped data'})
            
            # Process scraped data and add to vector database
            service._process_scraped_data_async(db_id, scraping_job_id)
            
            # Update task status to SUCCESS
            self.update_state(state='SUCCESS', meta={'progress': 100, 'status': 'Vector database ready'})
            
            return {'progress': 100, 'status': 'Vector database ready'}
            
        except Exception as e:
            logger.error(f"Error in vector database creation task: {str(e)}", exc_info=True)
            
            # Update vector database status to error in database
            try:
                service = VectorStoreService()
                conn = service._get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE vector_databases 
                    SET status = %s
                    WHERE id = %s;
                """, ('error', db_id))
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as db_error:
                logger.error(f"Failed to update vector DB status to error: {db_error}")
            
            # Update task status to FAILURE
            self.update_state(state='FAILURE', meta={'progress': 0, 'status': f'Error: {str(e)}'})
            raise

