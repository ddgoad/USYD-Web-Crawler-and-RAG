#!/usr/bin/env python3
"""
Database initialization script for USYD Web Crawler and RAG Application
Creates all required database tables and default data
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL", "postgresql://localhost:5432/usydrag")

def create_tables(cursor):
    """Create all required database tables"""
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
    """)
    logger.info("✓ Created users table")
    
    # Scraping jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scraping_jobs (
            id VARCHAR(36) PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            url VARCHAR(2048) NOT NULL,
            scraping_type VARCHAR(20) NOT NULL CHECK (scraping_type IN ('single', 'deep', 'sitemap')),
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
            config JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result_summary JSONB
        );
    """)
    logger.info("✓ Created scraping_jobs table")
    
    # Vector databases table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vector_databases (
            id VARCHAR(36) PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            job_id VARCHAR(36) REFERENCES scraping_jobs(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            source_url VARCHAR(2048) NOT NULL,
            azure_index_name VARCHAR(100) NOT NULL UNIQUE,
            document_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'building' CHECK (status IN ('building', 'ready', 'error')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, job_id)
        );
    """)
    logger.info("✓ Created vector_databases table")
    
    # Chat sessions table
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
    logger.info("✓ Created chat_sessions table")
    
    # Chat messages table
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
    logger.info("✓ Created chat_messages table")

def create_indexes(cursor):
    """Create database indexes for better performance"""
    
    indexes = [
        # Users indexes
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        
        # Scraping jobs indexes
        "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_user_id ON scraping_jobs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_status ON scraping_jobs(status);",
        "CREATE INDEX IF NOT EXISTS idx_scraping_jobs_created_at ON scraping_jobs(created_at DESC);",
        
        # Vector databases indexes
        "CREATE INDEX IF NOT EXISTS idx_vector_databases_user_id ON vector_databases(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_vector_databases_status ON vector_databases(status);",
        "CREATE INDEX IF NOT EXISTS idx_vector_databases_created_at ON vector_databases(created_at DESC);",
        
        # Chat sessions indexes
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_vector_db_id ON chat_sessions(vector_db_id);",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);",
        
        # Chat messages indexes
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at ASC);",
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    logger.info("✓ Created database indexes")

def create_default_users(cursor):
    """Create default users"""
    
    # Check if admin user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin';")
    admin_exists = cursor.fetchone()[0] > 0
    
    if not admin_exists:
        admin_password_hash = generate_password_hash("admin123")
        cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s);
        """, ("admin", admin_password_hash))
        logger.info("✓ Created default admin user (username: admin, password: admin123)")
    else:
        logger.info("✓ Admin user already exists")

def create_functions(cursor):
    """Create useful database functions"""
    
    # Function to update updated_at timestamp
    cursor.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Trigger for vector_databases table
    cursor.execute("""
        DROP TRIGGER IF EXISTS update_vector_databases_updated_at ON vector_databases;
        CREATE TRIGGER update_vector_databases_updated_at
            BEFORE UPDATE ON vector_databases
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)
    
    logger.info("✓ Created database functions and triggers")

def verify_tables(cursor):
    """Verify all tables exist and have correct structure"""
    
    expected_tables = [
        'users',
        'scraping_jobs', 
        'vector_databases',
        'chat_sessions',
        'chat_messages'
    ]
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE';
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    for table in expected_tables:
        if table in existing_tables:
            logger.info(f"✓ Table '{table}' exists")
        else:
            logger.error(f"✗ Table '{table}' is missing!")
            return False
    
    return True

def main():
    """Main initialization function"""
    try:
        logger.info("Starting database initialization...")
        
        # Get database connection
        db_url = get_database_url()
        logger.info(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Create tables
        logger.info("Creating database tables...")
        create_tables(cursor)
        
        # Create indexes
        logger.info("Creating database indexes...")
        create_indexes(cursor)
        
        # Create functions and triggers
        logger.info("Creating database functions...")
        create_functions(cursor)
        
        # Create default users
        logger.info("Creating default users...")
        create_default_users(cursor)
        
        # Commit changes
        conn.commit()
        
        # Verify tables
        logger.info("Verifying database structure...")
        if verify_tables(cursor):
            logger.info("✅ Database initialization completed successfully!")
        else:
            logger.error("❌ Database initialization failed - missing tables")
            return 1
        
        # Close connection
        cursor.close()
        conn.close()
        
        return 0
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())