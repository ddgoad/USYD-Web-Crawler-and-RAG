"""
Large Language Model Service for USYD Web Crawler and RAG Application
Integrates with Azure OpenAI for chat and RAG capabilities
"""

import os
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import AzureOpenAI
from services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/usydrag")
        
        # Initialize Azure OpenAI client
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY", "EdKxnIPfLdrlOCpGGgOajk7fFJeopjLec4IHPk8lCAsLrUYIdIW2JQQJ99AKACL93NaXJ3w3AAAAACOGh1w8"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "https://dgopenai2211200906498164.openai.azure.com/")
        )
        
        # Initialize vector store service for RAG
        self.vector_service = VectorStoreService()
        
        # Initialize database
        self._init_database()
        
        # Model configurations
        self.model_configs = {
            "gpt-4o": {
                "deployment_name": os.getenv("AZURE_OPENAI_GPT4O_DEPLOYMENT", "gpt-4o"),
                "max_tokens": 4096,
                "temperature": 0.7,
                "system_prompt": self._get_system_prompt()
            },
            "o3-mini": {
                "deployment_name": os.getenv("AZURE_OPENAI_O3_MINI_DEPLOYMENT", "o3-mini"),
                "max_tokens": 4096,
                "temperature": 0.3,
                "system_prompt": self._get_system_prompt()
            }
        }
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create chat_sessions table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    vector_db_id VARCHAR(36) REFERENCES vector_databases(id) ON DELETE CASCADE,
                    model_name VARCHAR(50) NOT NULL,
                    config JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create chat_messages table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(36) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("LLM service database initialized successfully")
        except Exception as e:
            logger.error(f"LLM service database initialization failed: {str(e)}")
            # Don't raise, as this shouldn't prevent the app from starting

    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI assistant"""
        return """You are an intelligent assistant for the USYD Web Crawler and RAG system. 
        
Your primary function is to help users understand and analyze web content that has been scraped and processed. 

Guidelines:
1. Always base your responses on the provided context from the scraped web content
2. If you don't have relevant information in the context, clearly state that
3. Always cite your sources by mentioning the URL or page title when possible
4. Provide accurate, helpful, and concise responses
5. When asked about specific information, try to find it in the scraped content first
6. If multiple sources contain relevant information, synthesize them appropriately
7. Be honest about limitations - if the scraped content doesn't contain enough information to answer a question fully, say so

Remember: Your knowledge comes from the scraped web content provided to you. Always prioritize this information over your general training data when answering questions about the scraped content."""
    
    def create_chat_session(self, user_id: int, vector_db_id: str, model: str, config: Dict) -> str:
        """Create a new chat session"""
        try:
            session_id = str(uuid.uuid4())
            
            # Validate model
            if model not in self.model_configs:
                raise Exception(f"Unsupported model: {model}")
            
            # Validate vector database access
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM vector_databases 
                WHERE id = %s AND user_id = %s AND status = 'ready';
            """, (vector_db_id, user_id))
            
            db_record = cursor.fetchone()
            if not db_record:
                raise Exception("Vector database not found or not ready")
            
            # Create chat session
            session_config = {
                **self.model_configs[model],
                **config  # User overrides
            }
            
            cursor.execute("""
                INSERT INTO chat_sessions (id, user_id, vector_db_id, model_name, config)
                VALUES (%s, %s, %s, %s, %s);
            """, (session_id, user_id, vector_db_id, model, json.dumps(session_config)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created chat session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create chat session: {str(e)}")
            raise
    
    def process_message(self, session_id: str, user_id: int, message: str) -> Dict:
        """Process a chat message and generate response"""
        try:
            # Get session details
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT cs.*, vd.id as vector_db_id, vd.name as vector_db_name
                FROM chat_sessions cs
                JOIN vector_databases vd ON cs.vector_db_id = vd.id
                WHERE cs.id = %s AND cs.user_id = %s;
            """, (session_id, user_id))
            
            session = cursor.fetchone()
            if not session:
                raise Exception("Chat session not found")
            
            # Store user message
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s);
            """, (session_id, 'user', message, json.dumps({})))
            
            # Get relevant context from vector database
            search_results = self.vector_service.search(
                db_id=session['vector_db_id'],
                user_id=user_id,
                query=message,
                search_type="hybrid",  # Use hybrid search for best results
                top_k=5
            )
            
            # Prepare context for the AI
            context_parts = []
            sources = []
            
            for result in search_results:
                context_parts.append(f"Source: {result['title']} ({result['url']})\nContent: {result['content']}")
                sources.append({
                    'title': result['title'],
                    'url': result['url'],
                    'score': result['score']
                })
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Get session configuration
            config = session['config'] if session['config'] else {}
            model_name = session['model_name']
            
            # Build messages for the AI
            messages = [
                {
                    "role": "system",
                    "content": config.get('system_prompt', self.model_configs[model_name]['system_prompt'])
                },
                {
                    "role": "user",
                    "content": f"Based on the following context from scraped web content, please answer the user's question.\n\nContext:\n{context}\n\nUser Question: {message}"
                }
            ]
            
            # Get recent conversation history for context
            cursor.execute("""
                SELECT role, content FROM chat_messages 
                WHERE session_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10;
            """, (session_id,))
            
            recent_messages = cursor.fetchall()
            
            # Add recent conversation to context (reversed to maintain chronological order)
            for msg in reversed(recent_messages):
                if msg['role'] != 'user' or msg['content'] != message:  # Skip the current message
                    messages.insert(-1, {
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # Generate response using Azure OpenAI
            response = self.openai_client.chat.completions.create(
                model=config.get('deployment_name', self.model_configs[model_name]['deployment_name']),
                messages=messages,
                max_tokens=config.get('max_tokens', self.model_configs[model_name]['max_tokens']),
                temperature=config.get('temperature', self.model_configs[model_name]['temperature']),
                top_p=config.get('top_p', 0.95),
                frequency_penalty=config.get('frequency_penalty', 0),
                presence_penalty=config.get('presence_penalty', 0)
            )
            
            ai_response = response.choices[0].message.content
            
            # Store AI response
            response_metadata = {
                'model': model_name,
                'sources_used': len(sources),
                'total_tokens': response.usage.total_tokens if response.usage else 0,
                'finish_reason': response.choices[0].finish_reason
            }
            
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s);
            """, (session_id, 'assistant', ai_response, json.dumps(response_metadata)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Processed message in session {session_id}")
            
            return {
                'response': ai_response,
                'sources': sources,
                'metadata': response_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")
            raise
    
    def generate_response(self, query: str, context: str, model: str = "gpt-4o", config: Dict = None) -> str:
        """Generate AI response based on query and context (standalone method)"""
        try:
            if model not in self.model_configs:
                raise Exception(f"Unsupported model: {model}")
            
            model_config = self.model_configs[model]
            if config:
                model_config.update(config)
            
            messages = [
                {
                    "role": "system",
                    "content": model_config['system_prompt']
                },
                {
                    "role": "user",
                    "content": f"Based on the following context, please answer the user's question.\n\nContext:\n{context}\n\nQuestion: {query}"
                }
            ]
            
            response = self.openai_client.chat.completions.create(
                model=model_config['deployment_name'],
                messages=messages,
                max_tokens=model_config['max_tokens'],
                temperature=model_config['temperature']
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise
    
    def get_chat_history(self, session_id: str, user_id: int) -> List[Dict]:
        """Get chat history for a session"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Verify session belongs to user
            cursor.execute("""
                SELECT id FROM chat_sessions 
                WHERE id = %s AND user_id = %s;
            """, (session_id, user_id))
            
            if not cursor.fetchone():
                raise Exception("Chat session not found")
            
            # Get messages
            cursor.execute("""
                SELECT role, content, metadata, created_at
                FROM chat_messages 
                WHERE session_id = %s 
                ORDER BY created_at ASC;
            """, (session_id,))
            
            messages = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(msg) for msg in messages]
            
        except Exception as e:
            logger.error(f"Failed to get chat history: {str(e)}")
            return []
    
    def delete_chat_session(self, session_id: str, user_id: int) -> bool:
        """Delete a chat session and its messages"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Delete messages first (foreign key constraint)
            cursor.execute("""
                DELETE FROM chat_messages 
                WHERE session_id = %s;
            """, (session_id,))
            
            # Delete session
            cursor.execute("""
                DELETE FROM chat_sessions 
                WHERE id = %s AND user_id = %s;
            """, (session_id, user_id))
            
            deleted_count = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Deleted chat session {session_id}")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Failed to delete chat session: {str(e)}")
            return False
    
    def get_user_chat_sessions(self, user_id: int) -> List[Dict]:
        """Get all chat sessions for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT cs.id, cs.model_name, cs.created_at, vd.name as vector_db_name
                FROM chat_sessions cs
                JOIN vector_databases vd ON cs.vector_db_id = vd.id
                WHERE cs.user_id = %s 
                ORDER BY cs.created_at DESC;
            """, (user_id,))
            
            sessions = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(session) for session in sessions]
            
        except Exception as e:
            logger.error(f"Failed to get user chat sessions: {str(e)}")
            return []