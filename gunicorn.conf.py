# Gunicorn configuration file for USYD Web Crawler and RAG Application
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = ('%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
                     '"%(f)s" "%(a)s" %(D)s')

# Process naming
proc_name = "usyd-rag-app"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if certificates are provided)
keyfile = None
certfile = None

# Application
wsgi_module = "app:app"

# Performance tuning
preload_app = True
enable_stdio_inheritance = True

# Worker lifecycle


def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 Starting Gunicorn server for USYD RAG Application")


def on_reload(server):
    """Called to recycle workers during a reload."""
    server.log.info("🔄 Reloading Gunicorn workers")


def worker_init(worker):
    """Called just after a worker has been forked."""
    worker.log.info(f"🔧 Worker {worker.pid} initialized")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.warning(f"⚠️ Worker {worker.pid} aborted")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.debug(f"🍴 About to fork worker {worker.pid}")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"✅ Worker {worker.pid} forked successfully")


def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("🔄 Pre-exec: About to exec new master process")


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("✅ Gunicorn server is ready to handle requests")


def worker_int(worker):
    """Called just after a worker has been interrupted."""
    worker.log.warning(f"⚠️ Worker {worker.pid} interrupted")


def on_exit(server):
    """Called just before the master process exits."""
    server.log.info("🛑 Gunicorn server shutting down")
