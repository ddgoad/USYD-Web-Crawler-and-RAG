#!/usr/bin/env python3
"""
Celery worker script for USYD Web Crawler and RAG Application
Handles background task processing for web scraping and vector database operations
"""

import os
import sys
import logging
from celery import Celery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'usyd_rag_worker',
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=['services.scraper', 'services.vector_store']  # Include modules with tasks
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

if __name__ == '__main__':
    logger.info("Starting Celery worker for USYD Web Crawler and RAG...")
    celery_app.start()