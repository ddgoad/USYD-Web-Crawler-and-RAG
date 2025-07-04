"""
USYD Web Crawler and RAG Application - Main Flask Application
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import uuid
from celery import Celery

# Import our service modules
from services.auth import AuthService
from services.scraper import ScrapingService
from services.vector_store import VectorStoreService
from services.llm_service import LLMService
from models.user import User

# Configure logging
import sys

# Force stdout to be unbuffered
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Use stdout with forced flush
    ],
    force=True
)
logger = logging.getLogger(__name__)

# Import document processor after logger is configured
try:
    from services.document_processor import document_processor
    DOCUMENT_UPLOAD_ENABLED = True
    logger.info("✓ Document processor initialized successfully")
except Exception as e:
    logger.warning(f"Document processor not available: {e}")
    document_processor = None
    DOCUMENT_UPLOAD_ENABLED = False


def flush_print(*args, **kwargs):
    """Print with immediate flush to ensure output appears in logs"""
    print(*args, **kwargs)
    sys.stdout.flush()


# Test that logging is working immediately
flush_print("=== APP STARTING: LOGGING TEST ===")
logger.info("Logger test: USYD Web Crawler application starting...")

# Create logs directory and add file handler after ensuring directory exists
try:
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    logger.info("File logging initialized successfully")
except Exception as e:
    logger.warning(f"Could not initialize file logging: {e}")

logger.info("Starting USYD Web Crawler and RAG Application initialization...")

# Validate critical environment variables
required_env_vars = {
    'DATABASE_URL': os.getenv('DATABASE_URL'),
    'REDIS_URL': os.getenv('REDIS_URL'), 
    'AZURE_OPENAI_ENDPOINT': os.getenv('AZURE_OPENAI_ENDPOINT'),
    'AZURE_OPENAI_KEY': os.getenv('AZURE_OPENAI_KEY')
}

missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    logger.warning(f"Missing environment variables: {missing_vars}")
    logger.warning("Application will continue with default/fallback values")
else:
    logger.info("✓ All critical environment variables are set")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize Celery for background tasks with fallback
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    logger.info(f"Connecting to Redis at: {redis_url}")
    celery = Celery(
        app.import_name,
        broker=redis_url,
        backend=redis_url
    )
    logger.info("✓ Celery initialized successfully")
except Exception as e:
    logger.warning(f"❌ Celery initialization failed: {e}")
    # Create a dummy celery object to prevent import errors
    celery = None

# Initialize services with error handling
try:
    logger.info("Initializing authentication service...")
    auth_service = AuthService()
    logger.info("✓ AuthService initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize AuthService: {e}")
    raise

try:
    logger.info("Initializing scraping service...")
    scraping_service = ScrapingService()
    logger.info("✓ ScrapingService initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize ScrapingService: {e}")
    raise

try:
    logger.info("Initializing vector store service...")
    vector_service = VectorStoreService()
    logger.info("✓ VectorStoreService initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize VectorStoreService: {e}")
    raise

try:
    logger.info("Initializing LLM service...")
    llm_service = LLMService()
    logger.info("✓ LLMService initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize LLMService: {e}")
    raise

logger.info("All services initialized successfully!")

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return auth_service.get_user_by_id(user_id)

# Routes
@app.route("/")
def index():
    """Home page - redirect to login if not authenticated, otherwise dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page and authentication"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = auth_service.authenticate_user(username, password)
        if user:
            login_user(user)
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
            logger.warning(f"Failed login attempt for username: {username}")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Logout user"""
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    flash("You have been logged out successfully", "info")
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard page"""
    # Get user's scraping jobs and vector databases
    try:
        scraping_jobs = auth_service.get_user_scraping_jobs(current_user.id)
    except:
        scraping_jobs = []  # Fallback to empty list if error
    
    try:
        vector_dbs = auth_service.get_user_vector_databases(current_user.id)
    except:
        vector_dbs = []  # Fallback to empty list if error
    
    return render_template("dashboard.html", 
                         scraping_jobs=scraping_jobs, 
                         vector_dbs=vector_dbs)

# API Routes

@app.route("/api/auth/status")
def auth_status():
    """Check authentication status"""
    return jsonify({
        "authenticated": current_user.is_authenticated,
        "user": {
            "id": current_user.id,
            "username": current_user.username
        } if current_user.is_authenticated else None
    })

@app.route("/api/vector-dbs/cleanup", methods=["POST"])
@login_required
def cleanup_vector_databases():
    """Clean up unused Azure Search indexes"""
    try:
        result = vector_service.cleanup_unused_indexes(current_user.id)
        logger.info(f"Cleanup completed for user {current_user.username}: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return jsonify({"error": "Failed to cleanup indexes"}), 500

@app.route("/api/vector-dbs/stats")
@login_required
def get_vector_database_stats():
    """Get vector database and index usage statistics"""
    try:
        stats = vector_service.get_index_usage_stats()
        logger.info(f"Index stats for user {current_user.username}: {stats}")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({"error": "Failed to get statistics"}), 500

@app.route("/api/scrape/start", methods=["POST"])
@login_required
def start_scraping():
    """Start web scraping job"""
    try:
        logger.info(f"Scraping request received from user {current_user.username}")
        data = request.get_json()
        url = data.get("url")
        scraping_type = data.get("type", "single")
        config = data.get("config", {})
        
        logger.info(f"Scraping parameters: URL={url}, type={scraping_type}, config={config}")
        
        if not url:
            logger.warning("Scraping request rejected: URL is required")
            return jsonify({"error": "URL is required"}), 400
        
        # Create scraping job
        logger.info(f"Creating scraping job for URL: {url}")
        job_id = scraping_service.create_scraping_job(
            user_id=current_user.id,
            url=url,
            scraping_type=scraping_type,
            config=config
        )
        
        logger.info(f"Created scraping job {job_id} for user {current_user.username}")
        flush_print(f"=== CREATED SCRAPING JOB {job_id} ===")
        
        # Start processing immediately in background thread
        logger.info(f"Starting background processing for job {job_id}")
        scraping_service.start_scraping_job(job_id)
        logger.info(f"Background processing initiated for job {job_id}")
        
        return jsonify({"job_id": job_id, "status": "started"})
        
    except Exception as e:
        logger.error(f"Error starting scraping job: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to start scraping job: {str(e)}"}), 500

@app.route("/api/scrape/status/<job_id>")
@login_required
def scraping_status(job_id):
    """Get scraping job status"""
    try:
        job = scraping_service.get_job_status(job_id, current_user.id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        return jsonify({
            "status": job["status"],
            "progress": job.get("progress", 0),
            "message": job.get("message", ""),
            "result_summary": job.get("result_summary", {})
        })
        
    except Exception as e:
        logger.error(f"Error getting scraping status: {str(e)}")
        return jsonify({"error": "Failed to get job status"}), 500

@app.route("/api/scrape/jobs")
@login_required
def scraping_jobs():
    """Get all scraping jobs for current user"""
    try:
        jobs = scraping_service.get_user_jobs(current_user.id)
        return jsonify({"jobs": jobs})
    except Exception as e:
        logger.error(f"Error getting scraping jobs: {str(e)}")
        return jsonify({"error": "Failed to get scraping jobs"}), 500

@app.route("/api/scrape/jobs/<job_id>", methods=["DELETE"])
@login_required
def delete_scraping_job(job_id):
    """Delete scraping job and its associated data"""
    try:
        success = scraping_service.delete_scraping_job(job_id, current_user.id)
        if success:
            logger.info(f"Deleted scraping job {job_id} for user {current_user.username}")
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Job not found or not authorized"}), 404
    except Exception as e:
        logger.error(f"Error deleting scraping job: {str(e)}")
        return jsonify({"error": "Failed to delete scraping job"}), 500

@app.route("/api/scrape/completed-jobs")
@login_required
def completed_scraping_jobs():
    """Get completed scraping jobs available for vector database creation"""
    try:
        jobs = scraping_service.get_completed_jobs(current_user.id)
        return jsonify({"jobs": jobs})
    except Exception as e:
        logger.error(f"Error getting completed scraping jobs: {str(e)}")
        return jsonify({"error": "Failed to get completed jobs"}), 500

@app.route("/api/vector-dbs")
@login_required
def vector_databases():
    """Get all vector databases for current user"""
    try:
        dbs = vector_service.get_user_databases(current_user.id)
        return jsonify({"databases": dbs})
    except Exception as e:
        logger.error(f"Error getting vector databases: {str(e)}")
        return jsonify({"error": "Failed to get vector databases"}), 500

@app.route("/api/vector-dbs/create", methods=["POST"])
@login_required
def create_vector_database():
    """Create vector database from scraping job"""
    try:
        data = request.get_json()
        name = data.get("name")
        scraping_job_id = data.get("scraping_job_id")
        
        if not name or not scraping_job_id:
            return jsonify({"error": "Name and scraping job ID are required"}), 400
        
        # Create database record and start processing in background
        db_id = vector_service.create_database_async(
            user_id=current_user.id,
            name=name,
            scraping_job_id=scraping_job_id
        )
        
        logger.info(f"Created vector database {db_id} for user "
                    f"{current_user.username}")
        return jsonify({"db_id": db_id, "status": "building"})
        
    except Exception as e:
        logger.error(f"Error creating vector database: {str(e)}",
                     exc_info=True)
        return jsonify({"error": f"Failed to create vector database: "
                        f"{str(e)}"}), 500


@app.route("/api/vector-dbs/<db_id>", methods=["DELETE"])
@login_required
def delete_vector_database(db_id):
    """Delete vector database"""
    try:
        success = vector_service.delete_database(db_id, current_user.id)
        if success:
            logger.info(f"Deleted vector database {db_id} for user {current_user.username}")
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Database not found or not authorized"}), 404
    except Exception as e:
        logger.error(f"Error deleting vector database: {str(e)}")
        return jsonify({"error": "Failed to delete vector database"}), 500


@app.route("/api/vector-dbs/<db_id>/status")
@login_required
def get_vector_database_status(db_id):
    """Get vector database creation status for non-blocking polling"""
    try:
        status_info = vector_service.get_database_status(db_id, current_user.id)
        if status_info:
            return jsonify(status_info)
        else:
            return jsonify({"error": "Database not found or not authorized"}), 404
    except Exception as e:
        logger.error(f"Error getting vector database status: {str(e)}")
        return jsonify({"error": "Failed to get database status"}), 500

@app.route("/api/vector-dbs/<db_id>/search", methods=["POST"])
@login_required
def search_vector_database(db_id):
    """Search in vector database"""
    try:
        data = request.get_json()
        query = data.get("query")
        search_type = data.get("search_type", "semantic")
        top_k = data.get("top_k", 5)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        results = vector_service.search(
            db_id=db_id,
            user_id=current_user.id,
            query=query,
            search_type=search_type,
            top_k=top_k
        )
        
        return jsonify({"results": results})
        
    except Exception as e:
        logger.error(f"Error searching vector database: {str(e)}")
        return jsonify({"error": "Failed to search vector database"}), 500

@app.route("/api/chat/start", methods=["POST"])
@login_required
def start_chat():
    """Start chat session"""
    try:
        data = request.get_json()
        vector_db_id = data.get("vector_db_id")
        model = data.get("model", "gpt-4o")
        config = data.get("config", {})
        
        if not vector_db_id:
            return jsonify({"error": "Vector database ID is required"}), 400
        
        session_id = llm_service.create_chat_session(
            user_id=current_user.id,
            vector_db_id=vector_db_id,
            model=model,
            config=config
        )
        
        logger.info(f"Started chat session {session_id} for user {current_user.username}")
        return jsonify({"session_id": session_id})
        
    except Exception as e:
        logger.error(f"Error starting chat session: {str(e)}")
        return jsonify({"error": "Failed to start chat session"}), 500

@app.route("/api/chat/message", methods=["POST"])
@login_required
def chat_message():
    """Send message to chat session"""
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        message = data.get("message")
        
        if not session_id or not message:
            return jsonify({"error": "Session ID and message are required"}), 400
        
        response = llm_service.process_message(
            session_id=session_id,
            user_id=current_user.id,
            message=message
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return jsonify({"error": "Failed to process message"}), 500

@app.route("/api/chat/history/<session_id>")
@login_required
def chat_history(session_id):
    """Get chat history"""
    try:
        messages = llm_service.get_chat_history(session_id, current_user.id)
        return jsonify({"messages": messages})
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({"error": "Failed to get chat history"}), 500

# Document Upload and Processing Endpoints

@app.route("/api/documents/upload", methods=["POST"])
@login_required
def upload_documents():
    """Upload and process documents for vector database creation"""
    
    # Check if document processor is available
    if not DOCUMENT_UPLOAD_ENABLED or document_processor is None:
        return jsonify({
            "error": "Document upload not available - Azure Storage not configured"
        }), 503
        
    try:
        if 'documents' not in request.files:
            return jsonify({"error": "No documents provided"}), 400
        
        files = request.files.getlist('documents')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No documents selected"}), 400
        
        processed_documents = []
        uploaded_blobs = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # Read file data
            file_data = file.read()
            file_size = len(file_data)
            
            # Validate document
            validation = document_processor.validate_document(
                file.filename, file_size, file_data
            )
            
            if not validation["valid"]:
                return jsonify({"error": validation["error"]}), 400
            
            # Upload to Azure Blob Storage
            try:
                blob_name = document_processor.upload_document(
                    file_data, file.filename, current_user.id
                )
                uploaded_blobs.append(blob_name)
            except Exception as e:
                # Clean up any already uploaded blobs
                for blob in uploaded_blobs:
                    document_processor.delete_document(blob)
                return jsonify({"error": f"Upload failed: {str(e)}"}), 500
        
        # Process all uploaded documents
        try:
            documents = document_processor.process_uploaded_documents(
                uploaded_blobs, current_user.id
            )
            
            if not documents:
                # Clean up uploaded blobs if processing failed
                for blob in uploaded_blobs:
                    document_processor.delete_document(blob)
                return jsonify({"error": "No content could be extracted from documents"}), 400
            
            # Prepare file metadata
            file_metadata = {
                "user_id": current_user.id,
                "uploaded_files": [{"filename": f.filename, "blob_name": blob} 
                                 for f, blob in zip(files, uploaded_blobs)],
                "file_count": len(files),
                "total_chunks": len(documents),
                "upload_timestamp": datetime.now().isoformat()
            }
            
            # Save to storage using the same mechanism as scraper
            doc_job_id = document_processor.save_processed_documents_to_storage(
                current_user.id, documents, file_metadata
            )
            
            return jsonify({
                "success": True,
                "document_job_id": doc_job_id,
                "documents_processed": len(documents),
                "files_uploaded": len(files)
            })
            
        except Exception as e:
            # Clean up uploaded blobs if processing failed
            for blob in uploaded_blobs:
                document_processor.delete_document(blob)
            logger.error(f"Document processing failed: {str(e)}")
            return jsonify({"error": f"Document processing failed: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        return jsonify({"error": "Failed to upload documents"}), 500


@app.route("/api/documents/jobs")
@login_required
def get_document_jobs():
    """Get all document jobs for the current user"""
    if not DOCUMENT_UPLOAD_ENABLED:
        return jsonify({
            "jobs": [],
            "message": "Document upload not available"
        })
        
    try:
        jobs = document_processor.get_user_document_jobs(current_user.id)
        return jsonify({"jobs": jobs})
    except Exception as e:
        logger.error(f"Error getting document jobs: {str(e)}")
        return jsonify({"error": "Failed to get document jobs"}), 500


@app.route("/api/vector-dbs/create-hybrid", methods=["POST"])
@login_required
def create_hybrid_vector_database():
    """Create vector database from combined web scraped and document sources"""
    try:
        data = request.get_json()
        name = data.get("name")
        description = data.get("description", "")
        scraping_job_id = data.get("scraping_job_id")
        document_job_ids = data.get("document_job_ids", [])
        
        if not name:
            return jsonify({"error": "Database name is required"}), 400
        
        # If document upload is disabled, ignore document job IDs
        if not DOCUMENT_UPLOAD_ENABLED:
            document_job_ids = []
        
        if not scraping_job_id and not document_job_ids:
            error_msg = ("At least one source (scraping job or document jobs) "
                         "is required")
            return jsonify({"error": error_msg}), 400
        
        db_id = vector_service.create_database_from_hybrid_sources(
            user_id=current_user.id,
            name=name,
            description=description,
            scraping_job_id=scraping_job_id,
            document_job_ids=document_job_ids
        )
        
        return jsonify({
            "success": True,
            "database_id": db_id,
            "message": "Hybrid vector database creation started"
        })
        
    except Exception as e:
        logger.error(f"Error creating hybrid vector database: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        auth_service._get_db_connection().close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return jsonify({
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return render_template('error.html', error="Internal server error"), 500

# Create logs directory if it doesn't exist
try:
    os.makedirs("logs", exist_ok=True)
    logger.info("Logs directory created/verified successfully")
except Exception as e:
    logger.warning(f"Could not create logs directory: {e}")

# WSGI entry point for production deployment
def create_app():
    """Application factory function for WSGI deployment"""
    return app

if __name__ == "__main__":
    # Development server (for local development only)
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"Starting USYD Web Crawler and RAG application on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    
    if debug:
        logger.warning("Running in development mode - not suitable for production!")
        app.run(host="0.0.0.0", port=port, debug=debug)
    else:
        logger.error("Production mode detected - use Gunicorn to start the application!")
        logger.error("Example: gunicorn --bind 0.0.0.0:5000 app:app")
        exit(1)