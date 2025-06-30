"""
Authentication Service for USYD Web Crawler and RAG Application
Handles user authentication, session management, and user data operations
"""

import os
import logging
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models.user import User

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///usydrag.db")
        self.db_path = self.db_url.replace("sqlite:///", "")
        self.db_initialized = False
        self._init_database()
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            if self.db_url.startswith("sqlite:"):
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row  # This makes rows behave like dictionaries
                return conn
            else:
                # Keep PostgreSQL support for production
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
                return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            logger.info(f"Initializing database: {self.db_url}")
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create users table for SQLite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    preferences TEXT DEFAULT '{}'
                )
            """)
            
            conn.commit()
            
            # Create default admin user if it doesn't exist
            self._create_default_admin_user(conn)
            
            conn.close()
            self.db_initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            logger.warning("Application will continue with limited functionality")
            self.db_initialized = False
    
    def _create_default_admin_user(self, conn):
        """Create default admin user if it doesn't exist"""
        try:
            cursor = conn.cursor()
            
            # Check if the desired user exists
            if self.db_url.startswith("sqlite:"):
                cursor.execute(
                    "SELECT id FROM users WHERE username = ?",
                    ("USYDScrapper",)
                )
            else:
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s",
                    ("USYDScrapper",)
                )
            
            if not cursor.fetchone():
                # Create USYDScrapper user
                admin_id = "usyd-scrapper-001"
                admin_password_hash = generate_password_hash("USYDRocks!")
                
                if self.db_url.startswith("sqlite:"):
                    cursor.execute("""
                        INSERT INTO users
                        (id, username, email, password_hash, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        admin_id,
                        "USYDScrapper",
                        "usydscrapper@usyd.edu.au",
                        admin_password_hash,
                        True
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO users
                        (id, username, email, password_hash, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        admin_id,
                        "USYDScrapper",
                        "usydscrapper@usyd.edu.au",
                        admin_password_hash,
                        True
                    ))
                
                conn.commit()
                logger.info(
                    "Default USYDScrapper user created successfully "
                    "(username: USYDScrapper, password: USYDRocks!)"
                )
            else:
                logger.info("USYDScrapper user already exists")
            
        except Exception as e:
            logger.error(f"Failed to create default admin user: {str(e)}")
            # Don't raise, as this shouldn't prevent the app from starting
    
    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user credentials"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT id, username, password_hash, created_at, last_login
                    FROM users
                    WHERE username = ?;
                """, (username,))
            else:
                cursor.execute("""
                    SELECT id, username, password_hash, created_at, last_login
                    FROM users
                    WHERE username = %s;
                """, (username,))
            
            user_data = cursor.fetchone()
            
            if user_data:
                # Convert to dict-like access
                if self.db_url.startswith("sqlite:"):
                    user_dict = {
                        'id': user_data[0],
                        'username': user_data[1], 
                        'password_hash': user_data[2],
                        'created_at': user_data[3],
                        'last_login': user_data[4]
                    }
                else:
                    user_dict = dict(user_data)
                
                if check_password_hash(user_dict['password_hash'], password):
                    # Update last login
                    if self.db_url.startswith("sqlite:"):
                        cursor.execute("""
                            UPDATE users
                            SET last_login = datetime('now')
                            WHERE id = ?;
                        """, (user_dict['id'],))
                    else:
                        cursor.execute("""
                            UPDATE users
                            SET last_login = CURRENT_TIMESTAMP
                            WHERE id = %s;
                        """, (user_dict['id'],))
                    conn.commit()
                    
                    user = User(
                        user_id=user_dict['id'],
                        username=user_dict['username'],
                        password_hash=user_dict['password_hash'],
                        created_at=user_dict['created_at'],
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
    
    def get_user_by_id(self, user_id) -> User:
        """Get user by ID for Flask-Login"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT id, username, password_hash, created_at, last_login
                    FROM users
                    WHERE id = ?;
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, username, password_hash, created_at, last_login
                    FROM users
                    WHERE id = %s;
                """, (user_id,))
            
            user_data = cursor.fetchone()
            
            if user_data:
                # Convert to dict-like access
                if self.db_url.startswith("sqlite:"):
                    user_dict = {
                        'id': user_data[0],
                        'username': user_data[1], 
                        'password_hash': user_data[2],
                        'created_at': user_data[3],
                        'last_login': user_data[4]
                    }
                else:
                    user_dict = dict(user_data)
                
                user = User(
                    user_id=user_dict['id'],
                    username=user_dict['username'],
                    password_hash=user_dict['password_hash'],
                    created_at=user_dict['created_at'],
                    last_login=user_dict['last_login']
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
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?);
                """, (username, password_hash))
            else:
                cursor.execute("""
                    INSERT INTO users (username, password_hash)
                    VALUES (%s, %s);
                """, (username, password_hash))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created new user: {username}")
            return True
            
        except Exception as e:
            logger.warning(f"User creation failed (username may already exist): {username} - {str(e)}")
            return False
    
    def get_user_scraping_jobs(self, user_id) -> list:
        """Get scraping jobs for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT id, url, scraping_type, status, config, 
                           created_at, completed_at, result_summary
                    FROM scraping_jobs 
                    WHERE user_id = ?
                    ORDER BY created_at DESC;
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, url, scraping_type, status, config, 
                           created_at, completed_at, result_summary
                    FROM scraping_jobs 
                    WHERE user_id = %s
                    ORDER BY created_at DESC;
                """, (user_id,))
            
            jobs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert to list of dicts
            if self.db_url.startswith("sqlite:"):
                job_list = []
                for job in jobs:
                    job_dict = {
                        'id': job[0],
                        'url': job[1],
                        'scraping_type': job[2],
                        'status': job[3],
                        'config': job[4],
                        'created_at': job[5],
                        'completed_at': job[6],
                        'result_summary': job[7]
                    }
                    job_list.append(job_dict)
                return job_list
            else:
                return [dict(job) for job in jobs]
            
        except Exception as e:
            logger.error(f"Get user scraping jobs failed: {str(e)}")
            return []
    
    def get_user_vector_databases(self, user_id) -> list:
        """Get vector databases for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT id, name, source_url, azure_index_name, 
                           document_count, status, created_at, updated_at
                    FROM vector_databases 
                    WHERE user_id = ?
                    ORDER BY created_at DESC;
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT id, name, source_url, azure_index_name, 
                           document_count, status, created_at, updated_at
                    FROM vector_databases 
                    WHERE user_id = %s
                    ORDER BY created_at DESC;
                """, (user_id,))
            
            databases = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert to list of dicts
            if self.db_url.startswith("sqlite:"):
                db_list = []
                for db in databases:
                    db_dict = {
                        'id': db[0],
                        'name': db[1],
                        'source_url': db[2],
                        'azure_index_name': db[3],
                        'document_count': db[4],
                        'status': db[5],
                        'created_at': db[6],
                        'updated_at': db[7]
                    }
                    db_list.append(db_dict)
                return db_list
            else:
                return [dict(db) for db in databases]
            
        except Exception as e:
            logger.error(f"Get user vector databases failed: {str(e)}")
            return []