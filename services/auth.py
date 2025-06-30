"""
Authentication Service for USYD Web Crawler and RAG Application
Handles user authentication, session management, and user data operations
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models.user import User

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/usydrag")
        self._init_database()
    
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
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                );
            """)
            
            # Create scraping_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_jobs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    url VARCHAR(2048) NOT NULL,
                    scraping_type VARCHAR(20) NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    config JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result_summary JSONB
                );
            """)
            
            # Create vector_databases table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_databases (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    name VARCHAR(100) NOT NULL,
                    source_url VARCHAR(2048) NOT NULL,
                    azure_index_name VARCHAR(100) NOT NULL,
                    document_count INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'building',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    vector_db_id INTEGER REFERENCES vector_databases(id),
                    model_name VARCHAR(50) NOT NULL,
                    config JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create chat_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES chat_sessions(id),
                    role VARCHAR(10) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create a default user if none exists
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                default_password_hash = generate_password_hash("admin123")
                cursor.execute("""
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s);
                """, ("admin", default_password_hash))
                logger.info("Created default admin user (username: admin, password: admin123)")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user credentials"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, username, password_hash, created_at, last_login
                FROM users 
                WHERE username = %s;
            """, (username,))
            
            user_data = cursor.fetchone()
            
            if user_data and check_password_hash(user_data['password_hash'], password):
                # Update last login
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = %s;
                """, (user_data['id'],))
                conn.commit()
                
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at'],
                    last_login=datetime.utcnow()
                )
                
                cursor.close()
                conn.close()
                return user
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID for Flask-Login"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, username, password_hash, created_at, last_login
                FROM users 
                WHERE id = %s;
            """, (user_id,))
            
            user_data = cursor.fetchone()
            
            if user_data:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at'],
                    last_login=user_data['last_login']
                )
                
                cursor.close()
                conn.close()
                return user
            
            cursor.close()
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Get user by ID failed: {str(e)}")
            return None
    
    def create_user(self, username: str, password: str) -> bool:
        """Create new user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s);
            """, (username, password_hash))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created new user: {username}")
            return True
            
        except psycopg2.IntegrityError:
            logger.warning(f"Username already exists: {username}")
            return False
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False
    
    def get_user_scraping_jobs(self, user_id: int) -> list:
        """Get scraping jobs for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, url, scraping_type, status, config, created_at, completed_at, result_summary
                FROM scraping_jobs 
                WHERE user_id = %s
                ORDER BY created_at DESC;
            """, (user_id,))
            
            jobs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(job) for job in jobs]
            
        except Exception as e:
            logger.error(f"Get user scraping jobs failed: {str(e)}")
            return []
    
    def get_user_vector_databases(self, user_id: int) -> list:
        """Get vector databases for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, name, source_url, azure_index_name, document_count, status, created_at, updated_at
                FROM vector_databases 
                WHERE user_id = %s
                ORDER BY created_at DESC;
            """, (user_id,))
            
            databases = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(db) for db in databases]
            
        except Exception as e:
            logger.error(f"Get user vector databases failed: {str(e)}")
            return []