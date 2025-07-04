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

# Import Celery for background tasks (future enhancement)
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Celery not available, using threading for async processing")
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
        self._init_hybrid_database_tables()
        self._init_hybrid_database_tables()
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create vector_databases table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_databases (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    source_url VARCHAR(2048),
                    azure_index_name VARCHAR(255) UNIQUE NOT NULL,
                    scraping_job_id VARCHAR(36),
                    document_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'pending'
                );
            """)
            
            # Create vector_documents table if it doesn't exist
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
            
            # Get embedding model deployment name from environment
            embedding_deployment = os.getenv(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
                "text-embedding-ada-002"
            )
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = self.openai_client.embeddings.create(
                    input=batch,
                    model=embedding_deployment
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def list_search_indexes(self) -> List[Dict]:
        """List all Azure Search indexes"""
        try:
            indexes = self.index_client.list_indexes()
            return [{"name": index.name, "fields_count": len(index.fields)}
                    for index in indexes]
        except Exception as e:
            logger.error(f"Failed to list search indexes: {str(e)}")
            return []
    
    def cleanup_unused_indexes(self, user_id: int = None) -> Dict:
        """Clean up unused Azure Search indexes"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all indexes from Azure Search
            all_indexes = self.index_client.list_indexes()
            azure_index_names = {index.name for index in all_indexes}
            
            # Get all index names from database
            if user_id:
                cursor.execute("""
                    SELECT azure_index_name FROM vector_databases
                    WHERE user_id = %s;
                """, (user_id,))
            else:
                cursor.execute(
                    "SELECT azure_index_name FROM vector_databases;"
                )

            db_index_names = {row['azure_index_name']
                              for row in cursor.fetchall()}
            
            # Find orphaned indexes (exists in Azure but not in database)
            orphaned_indexes = azure_index_names - db_index_names
            
            # Delete orphaned indexes
            deleted_count = 0
            failed_deletions = []
            
            for index_name in orphaned_indexes:
                # Only delete indexes that match our naming pattern
                if index_name.startswith('usyd-rag-'):
                    try:
                        self.index_client.delete_index(index_name)
                        deleted_count += 1
                        logger.info(f"Deleted orphaned index: {index_name}")
                    except Exception as e:
                        failed_deletions.append(index_name)
                        logger.error(
                            f"Failed to delete orphaned index "
                            f"{index_name}: {str(e)}"
                        )
            
            cursor.close()
            conn.close()
            
            result = {
                "total_indexes": len(azure_index_names),
                "orphaned_found": len(orphaned_indexes),
                "deleted_count": deleted_count,
                "failed_deletions": failed_deletions
            }
            
            logger.info(f"Cleanup results: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to cleanup unused indexes: {str(e)}")
            return {
                "total_indexes": 0,
                "orphaned_found": 0,
                "deleted_count": 0,
                "failed_deletions": [],
                "error": str(e)
            }

    def get_index_usage_stats(self) -> Dict:
        """Get statistics about index usage"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all indexes from Azure Search
            all_indexes = self.index_client.list_indexes()
            azure_index_count = len(list(all_indexes))
            
            # Get database stats
            cursor.execute(
                "SELECT COUNT(*) as total_dbs FROM vector_databases;"
            )
            total_dbs = cursor.fetchone()['total_dbs']

            cursor.execute(
                "SELECT COUNT(*) as active_dbs FROM vector_databases "
                "WHERE status = 'ready';"
            )
            active_dbs = cursor.fetchone()['active_dbs']

            cursor.execute(
                "SELECT COUNT(*) as building_dbs FROM vector_databases "
                "WHERE status = 'building';"
            )
            building_dbs = cursor.fetchone()['building_dbs']

            cursor.execute(
                "SELECT COUNT(*) as error_dbs FROM vector_databases "
                "WHERE status = 'error';"
            )
            error_dbs = cursor.fetchone()['error_dbs']
            
            cursor.close()
            conn.close()
            
            return {
                "azure_index_count": azure_index_count,
                "azure_index_limit": 15,  # Free tier limit
                "total_databases": total_dbs,
                "active_databases": active_dbs,
                "building_databases": building_dbs,
                "error_databases": error_dbs,
                "indexes_available": 15 - azure_index_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get index usage stats: {str(e)}")
            return {
                "azure_index_count": 0,
                "azure_index_limit": 15,
                "total_databases": 0,
                "active_databases": 0,
                "building_databases": 0,
                "error_databases": 0,
                "indexes_available": 0,
                "error": str(e)
            }

    def _create_search_index(self, index_name: str) -> bool:
        """Create Azure AI Search index with improved error handling"""
        try:
            # Check if we've exceeded the index quota before creating
            stats = self.get_index_usage_stats()
            if stats.get('indexes_available', 0) <= 0:
                logger.warning("Index quota exceeded. Attempting cleanup...")
                cleanup_result = self.cleanup_unused_indexes()
                logger.info(f"Cleanup result: {cleanup_result}")
                
                # Recheck after cleanup
                stats = self.get_index_usage_stats()
                if stats.get('indexes_available', 0) <= 0:
                    raise Exception(
                        "Index quota exceeded and cleanup did not free "
                        "enough space. Please delete unused vector "
                        "databases manually."
                    )

            # Define the search index schema
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String,
                           key=True),
                SearchField(name="content", type=SearchFieldDataType.String,
                           searchable=True),
                SearchField(name="title", type=SearchFieldDataType.String,
                           searchable=True, filterable=True),
                SearchField(name="url", type=SearchFieldDataType.String,
                           filterable=True),
                SearchField(name="chunk_index",
                           type=SearchFieldDataType.Int32, filterable=True),
                SearchField(name="source_type",
                           type=SearchFieldDataType.String, filterable=True),
                SearchField(name="metadata", type=SearchFieldDataType.String,
                           searchable=True),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(
                        SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,
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
            error_msg = str(e)
            if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                logger.error(f"Index quota exceeded when creating "
                           f"{index_name}: {error_msg}")
            else:
                logger.error(f"Failed to create search index "
                           f"{index_name}: {error_msg}")
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
                (id, user_id, scraping_job_id, name, source_url, azure_index_name, status)
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
                (id, user_id, scraping_job_id, name, source_url,
                 azure_index_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (db_id, user_id, scraping_job_id, name, job['url'],
                  azure_index_name, 'building'))
            
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
        """Start vector database processing using background thread (simplified approach)"""
        # Use threading approach which is more reliable and simpler
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
            
            azure_index_name = db_record['azure_index_name']
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
                index_name = db_record['azure_index_name']
                self.index_client.delete_index(index_name)
                logger.info(f"Deleted Azure Search index: {index_name}")
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

    def create_database_from_hybrid_sources(self, user_id: int, name: str, 
                                          scraping_job_id: str = None, 
                                          document_job_ids: List[str] = None, 
                                          description: str = None) -> str:
        """Create vector database from combined web scraped and document sources"""
        try:
            db_id = str(uuid.uuid4())
            
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            source_url = None
            
            # Validate scraping job if provided
            if scraping_job_id:
                cursor.execute("""
                    SELECT * FROM scraping_jobs
                    WHERE id = %s AND user_id = %s AND status = 'completed';
                """, (scraping_job_id, user_id))
                
                job = cursor.fetchone()
                if not job:
                    raise Exception("Scraping job not found or not completed")
                source_url = job['url']
            
            # Validate document jobs if provided
            if document_job_ids:
                for doc_job_id in document_job_ids:
                    cursor.execute("""
                        SELECT * FROM document_jobs
                        WHERE id = %s AND user_id = %s AND status = 'completed';
                    """, (doc_job_id, user_id))
                    
                    doc_job = cursor.fetchone()
                    if not doc_job:
                        raise Exception(f"Document job {doc_job_id} not found or not completed")
            
            # At least one source must be provided
            if not scraping_job_id and not document_job_ids:
                raise Exception("At least one source (scraping job or document jobs) must be provided")
            
            # Create Azure Search index
            azure_index_name = f"usyd-rag-{db_id}"
            if not self._create_search_index(azure_index_name):
                raise Exception("Failed to create search index")
            
            # Create vector database record
            cursor.execute("""
                INSERT INTO vector_databases 
                (id, user_id, scraping_job_id, name, description, source_url, azure_index_name, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (db_id, user_id, scraping_job_id, name, description, source_url, azure_index_name, 'building'))
            
            # Link document jobs to the vector database
            if document_job_ids:
                for doc_job_id in document_job_ids:
                    cursor.execute("""
                        INSERT INTO vector_database_sources 
                        (vector_db_id, source_type, source_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING;
                    """, (db_id, 'document_job', doc_job_id))
            
            # Link scraping job to the vector database
            if scraping_job_id:
                cursor.execute("""
                    INSERT INTO vector_database_sources 
                    (vector_db_id, source_type, source_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (db_id, 'scraping_job', scraping_job_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Start processing both sources in background
            self._start_hybrid_processing_background(db_id, scraping_job_id, document_job_ids)
            
            logger.info(f"Created hybrid vector database {db_id} for user {user_id}")
            return db_id
            
        except Exception as e:
            logger.error(f"Failed to create hybrid vector database: {str(e)}")
            raise
    
    def _start_hybrid_processing_background(self, db_id: str, scraping_job_id: str = None, 
                                          document_job_ids: List[str] = None):
        """Start hybrid vector database processing using background thread"""
        def process_hybrid_vector_db():
            try:
                logger.info("Starting background hybrid vector processing (threading)")
                self._process_hybrid_data_async(db_id, scraping_job_id, document_job_ids)
                logger.info("Background hybrid vector processing completed")
            except Exception as e:
                logger.error(f"Error in background hybrid vector processing: {str(e)}", exc_info=True)
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
                    logger.error(f"Failed to update vector DB status: {db_error}")
        
        import threading
        thread = threading.Thread(target=process_hybrid_vector_db)
        thread.daemon = True
        thread.start()
        logger.info(f"Started background thread for hybrid vector DB {db_id}")

    def _process_hybrid_data_async(self, db_id: str, scraping_job_id: str = None, 
                                 document_job_ids: List[str] = None):
        """Process both scraped data and documents and add to vector database"""
        try:
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
            logger.info(f"Processing hybrid data for Azure index: {azure_index_name}")
            
            # Create search client for this index
            search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=azure_index_name,
                credential=self.credential
            )
            
            # Process all sources
            all_documents = []
            document_count = 0
            
            # Process scraped data if available
            if scraping_job_id:
                scraped_docs = self._load_and_process_scraped_source(scraping_job_id, db_id)
                all_documents.extend(scraped_docs)
                document_count += len(scraped_docs)
                logger.info(f"Processed {len(scraped_docs)} documents from scraped data")
            
            # Process document data if available
            if document_job_ids:
                for doc_job_id in document_job_ids:
                    doc_documents = self._load_and_process_document_source(doc_job_id, db_id)
                    all_documents.extend(doc_documents)
                    document_count += len(doc_documents)
                    logger.info(f"Processed {len(doc_documents)} documents from document job {doc_job_id}")
            
            # Upload all documents to Azure Search
            if all_documents:
                logger.info(f"Uploading {len(all_documents)} total document chunks to Azure Search")
                # Upload in batches
                batch_size = 100
                for i in range(0, len(all_documents), batch_size):
                    batch = all_documents[i:i + batch_size]
                    try:
                        search_client.upload_documents(documents=batch)
                        logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(all_documents) + batch_size - 1)//batch_size}")
                    except Exception as e:
                        logger.error(f"Failed to upload batch {i//batch_size + 1}: {str(e)}")
                        raise
                
                logger.info(f"Successfully uploaded all {len(all_documents)} document chunks to index {azure_index_name}")
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
            
            logger.info(f"Hybrid vector database {db_id} is ready with {document_count} documents")
            
        except Exception as e:
            logger.error(f"Failed to process hybrid data for database {db_id}: {str(e)}", exc_info=True)
            
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

    def _load_and_process_scraped_source(self, scraping_job_id: str, db_id: str) -> List[Dict]:
        """Load and process scraped data source"""
        data_file = f"data/raw/{scraping_job_id}/scraped_data.json"
        if not os.path.exists(data_file):
            logger.warning(f"Scraped data file not found: {data_file}")
            return []
        
        logger.info(f"Loading scraped data from {data_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        
        documents = []
        chunk_counter = 0
        
        if scraped_data.get('success'):
            # Handle both single page and multi-page results
            if 'results' in scraped_data and isinstance(scraped_data['results'], list):
                results = scraped_data['results']
            elif 'content' in scraped_data:
                results = [scraped_data]
            else:
                results = []
            
            for result in results:
                content = result.get('content', '')
                if not content or not content.strip():
                    continue
                
                # Chunk the content
                chunks = self._chunk_text(content)
                
                # Generate embeddings for chunks
                try:
                    embeddings = self._generate_embeddings(chunks)
                except Exception as e:
                    logger.error(f"Failed to generate embeddings: {str(e)}")
                    continue
                
                # Create documents for each chunk
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    doc_id = f"{db_id}_scraped_{chunk_counter}_{i}"
                    
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
                
                chunk_counter += 1
        
        return documents

    def _load_and_process_document_source(self, document_job_id: str, db_id: str) -> List[Dict]:
        """Load and process document data source"""
        data_file = f"data/raw/{document_job_id}/scraped_data.json"
        if not os.path.exists(data_file):
            logger.warning(f"Document data file not found: {data_file}")
            return []
        
        logger.info(f"Loading document data from {data_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            document_data = json.load(f)
        
        documents = []
        chunk_counter = 0
        
        if document_data.get('success') and 'results' in document_data:
            for result in document_data['results']:
                content = result.get('content', '')
                if not content or not content.strip():
                    continue
                
                # Content is already chunked by the document processor
                # Generate embeddings for the chunk
                try:
                    embeddings = self._generate_embeddings([content])
                    embedding = embeddings[0]
                except Exception as e:
                    logger.error(f"Failed to generate embeddings: {str(e)}")
                    continue
                
                # Create document
                doc_id = f"{db_id}_doc_{chunk_counter}_{result.get('chunk_index', 0)}"
                
                document = {
                    "id": doc_id,
                    "content": content,
                    "title": result.get('title', ''),
                    "url": result.get('url', result.get('filename', '')),
                    "chunk_index": result.get('chunk_index', 0),
                    "source_type": "uploaded_document",
                    "metadata": json.dumps(result.get('metadata', {})),
                    "content_vector": embedding
                }
                
                documents.append(document)
                chunk_counter += 1
        
        return documents

    def _init_hybrid_database_tables(self):
        """Initialize additional tables for hybrid vector databases"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create vector_database_sources table to track multiple sources per database
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_database_sources (
                    id SERIAL PRIMARY KEY,
                    vector_db_id VARCHAR(36) REFERENCES vector_databases(id) ON DELETE CASCADE,
                    source_type VARCHAR(20) NOT NULL,  -- 'scraping_job' or 'document_job'
                    source_id VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vector_db_id, source_type, source_id)
                );
            """)
            
            # Add description column to vector_databases if it doesn't exist
            cursor.execute("""
                ALTER TABLE vector_databases 
                ADD COLUMN IF NOT EXISTS description TEXT;
            """)
            
            conn.commit()
            conn.close()
            logger.info("Hybrid vector store database tables initialized successfully")
        except Exception as e:
            logger.error(f"Hybrid vector store database initialization failed: {str(e)}")
            # Don't raise, as this shouldn't prevent the app from starting

