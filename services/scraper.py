"""
Web Scraping Service for USYD Web Crawler and RAG Application
Uses Crawl4AI for intelligent web content extraction
"""

import os
import logging
import json
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import requests
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import asyncio
import threading
import time

logger = logging.getLogger(__name__)

class ScrapingService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///usydrag.db")
        self.db_path = self.db_url.replace("sqlite:///", "")
        self._init_database()
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            if self.db_url.startswith("sqlite:"):
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
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
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            # Create scraping_jobs table
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_jobs (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        url TEXT NOT NULL,
                        scraping_type TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        config TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        result_summary TEXT
                    )
                """)
            else:
                # PostgreSQL schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraping_jobs (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        url VARCHAR(2048) NOT NULL,
                        scraping_type VARCHAR(20) NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        config JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        result_summary JSONB
                    );
                """)
            
            conn.commit()
            conn.close()
            logger.info("Scraping database initialized successfully")
        except Exception as e:
            logger.error(f"Scraping database initialization failed: {str(e)}")
            # Don't raise, as this shouldn't prevent the app from starting
    
    def create_scraping_job(self, user_id, url: str, 
                           scraping_type: str, config: Dict) -> str:
        """Create a new scraping job"""
        try:
            job_id = str(uuid.uuid4())
            
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    INSERT INTO scraping_jobs (id, user_id, url, scraping_type, status, config)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (job_id, user_id, url, scraping_type, 'pending', json.dumps(config)))
            else:
                cursor.execute("""
                    INSERT INTO scraping_jobs (id, user_id, url, scraping_type, status, config)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (job_id, user_id, url, scraping_type, 'pending', json.dumps(config)))
            
            conn.commit()
            
            # Verify the job was created by reading it back
            if self.db_url.startswith("sqlite:"):
                cursor.execute("SELECT id FROM scraping_jobs WHERE id = ?", (job_id,))
            else:
                cursor.execute("SELECT id FROM scraping_jobs WHERE id = %s", (job_id,))
            
            if not cursor.fetchone():
                raise Exception(f"Failed to verify job creation for {job_id}")
            
            cursor.close()
            conn.close()
            
            logger.info(f"Created scraping job {job_id} for user {user_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create scraping job: {str(e)}")
            raise

    def start_scraping_job(self, job_id: str):
        """Start a scraping job in a background thread"""
        def process_job():
            try:
                # Small delay to ensure database transaction is fully committed
                time.sleep(0.5)
                logger.info(f"Starting background thread for job {job_id}")
                
                # Run the async scraping function
                asyncio.run(self._process_scraping_job_async(job_id))
                
                logger.info(f"Background thread completed for job {job_id}")
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        
        logger.info(f"Creating background thread for job {job_id}")
        thread = threading.Thread(target=process_job, name=f"scraper-{job_id}")
        thread.daemon = True
        thread.start()
        logger.info(f"Background thread started for job {job_id}")

    async def _process_scraping_job_async(self, job_id: str):
        """Process a scraping job asynchronously"""
        try:
            logger.info(f"Processing scraping job {job_id} - getting job details")
            
            # Get job details
            conn = self._get_db_connection()
            if self.db_url.startswith("sqlite:"):
                cursor = conn.cursor()
            else:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT * FROM scraping_jobs WHERE id = ?;
                """, (job_id,))
            else:
                cursor.execute("""
                    SELECT * FROM scraping_jobs WHERE id = %s;
                """, (job_id,))
            
            job = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not job:
                logger.error(f"Job {job_id} not found in database")
                self._update_job_status(job_id, 'failed', 0, f"Job {job_id} not found in database")
                raise Exception(f"Job {job_id} not found")
            
            logger.info(f"Found job {job_id}, starting processing")
            
            # Convert job to dict format
            if self.db_url.startswith("sqlite:"):
                job_dict = {
                    'id': job[0],
                    'user_id': job[1],
                    'url': job[2],
                    'scraping_type': job[3],
                    'status': job[4],
                    'config': job[5],
                    'created_at': job[6],
                    'completed_at': job[7],
                    'result_summary': job[8]
                }
            else:
                job_dict = dict(job)
            
            # Update status to running
            self._update_job_status(job_id, 'running', 10, 'Starting scraping process')
            
            # Run the appropriate scraping method
            # Handle config parsing based on whether it's already parsed or a JSON string
            if isinstance(job_dict['config'], str):
                try:
                    config = json.loads(job_dict['config']) if job_dict['config'] else {}
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse config JSON: {job_dict['config']}")
                    config = {}
            elif isinstance(job_dict['config'], dict):
                config = job_dict['config'] or {}
            else:
                config = {}
            
            result = None
            if job_dict['scraping_type'] == 'single':
                self._update_job_status(job_id, 'running', 30, 'Scraping single page')
                result = await self.scrape_single_page(job_dict['url'])
            elif job_dict['scraping_type'] == 'deep':
                max_depth = config.get('max_depth', 3)
                max_pages = config.get('max_pages', 50)
                self._update_job_status(job_id, 'running', 30, f'Starting deep crawl (depth: {max_depth}, max pages: {max_pages})')
                result = await self.scrape_website_deep(job_dict['url'], max_depth, max_pages)
            elif job_dict['scraping_type'] == 'sitemap':
                max_pages = config.get('max_pages', 100)
                self._update_job_status(job_id, 'running', 30, f'Starting sitemap crawl (max pages: {max_pages})')
                result = await self.scrape_from_sitemap(job_dict['url'], max_pages)
            else:
                raise Exception(f"Unknown scraping type: {job_dict['scraping_type']}")
            
            if result and result.get('success'):
                self._update_job_status(job_id, 'running', 80, 'Saving scraped data')
                
                # Save scraped data to file
                data_dir = f"data/raw/{job_id}"
                os.makedirs(data_dir, exist_ok=True)
                
                with open(f"{data_dir}/scraped_data.json", 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                self._update_job_status(job_id, 'completed', 100, 'Scraping completed successfully', result)
                logger.info(f"Scraping job {job_id} completed successfully")
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'Scraping failed with no result'
                self._update_job_status(job_id, 'failed', 0, f"Scraping failed: {error_msg}")
                logger.error(f"Scraping job {job_id} failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"Error processing scraping job {job_id}: {str(e)}", exc_info=True)
            self._update_job_status(job_id, 'failed', 0, f"Error: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str, user_id) -> Optional[Dict]:
        """Get scraping job status"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT * FROM scraping_jobs 
                    WHERE id = ? AND user_id = ?;
                """, (job_id, user_id))
            else:
                cursor.execute("""
                    SELECT * FROM scraping_jobs 
                    WHERE id = %s AND user_id = %s;
                """, (job_id, user_id))
            
            job = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if job:
                if self.db_url.startswith("sqlite:"):
                    return {
                        'id': job[0],
                        'user_id': job[1],
                        'url': job[2],
                        'scraping_type': job[3],
                        'status': job[4],
                        'config': job[5],
                        'created_at': job[6],
                        'completed_at': job[7],
                        'result_summary': job[8]
                    }
                else:
                    return dict(job)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job status: {str(e)}")
            return None
    
    def get_user_jobs(self, user_id) -> List[Dict]:
        """Get all scraping jobs for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT * FROM scraping_jobs 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC;
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT * FROM scraping_jobs 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC;
                """, (user_id,))
            
            jobs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if self.db_url.startswith("sqlite:"):
                job_list = []
                for job in jobs:
                    job_dict = {
                        'id': job[0],
                        'user_id': job[1],
                        'url': job[2],
                        'scraping_type': job[3],
                        'status': job[4],
                        'config': job[5],
                        'created_at': job[6],
                        'completed_at': job[7],
                        'result_summary': job[8]
                    }
                    job_list.append(job_dict)
                return job_list
            else:
                return [dict(job) for job in jobs]
            
        except Exception as e:
            logger.error(f"Failed to get user jobs: {str(e)}")
            return []
    
    def _update_job_status(self, job_id: str, status: str, progress: int = 0, 
                          message: str = "", result_summary: Dict = None):
        """Update job status in database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if status in ['completed', 'failed']:
                if self.db_url.startswith("sqlite:"):
                    cursor.execute("""
                        UPDATE scraping_jobs 
                        SET status = ?, completed_at = datetime('now'), result_summary = ?
                        WHERE id = ?;
                    """, (status, json.dumps(result_summary) if result_summary else None, job_id))
                else:
                    cursor.execute("""
                        UPDATE scraping_jobs 
                        SET status = %s, completed_at = CURRENT_TIMESTAMP, result_summary = %s
                        WHERE id = %s;
                    """, (status, json.dumps(result_summary) if result_summary else None, job_id))
            else:
                # Store progress in result_summary for running jobs
                progress_data = result_summary or {}
                progress_data.update({
                    'status': status,
                    'progress': progress,
                    'message': message
                })
                
                if self.db_url.startswith("sqlite:"):
                    cursor.execute("""
                        UPDATE scraping_jobs 
                        SET status = ?, result_summary = ?
                        WHERE id = ?;
                    """, (status, json.dumps(progress_data), job_id))
                else:
                    cursor.execute("""
                        UPDATE scraping_jobs 
                        SET status = %s, result_summary = %s
                        WHERE id = %s;
                    """, (status, json.dumps(progress_data), job_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
    
    async def scrape_single_page(self, url: str) -> Dict:
        """Scrape a single web page"""
        try:
            # Use context manager pattern for proper resource management
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url=url)
                
                if result.success:
                    return {
                        'success': True,
                        'url': url,
                        'title': result.metadata.get('title', ''),
                        'content': result.markdown,
                        'links': result.links,
                        'media': result.media,
                        'metadata': result.metadata
                    }
                else:
                    return {
                        'success': False,
                        'url': url,
                        'error': 'Failed to scrape page'
                    }
                
        except Exception as e:
            logger.error(f"Failed to scrape single page {url}: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    async def scrape_website_deep(self, url: str, max_depth: int = 3, max_pages: int = 50) -> Dict:
        """Deep crawl a website"""
        try:
            scraped_urls = set()
            to_scrape = [(url, 0)]  # (url, depth)
            results = []
            
            # Use context manager pattern for proper resource management
            async with AsyncWebCrawler(verbose=True) as crawler:
                while to_scrape and len(scraped_urls) < max_pages:
                    current_url, depth = to_scrape.pop(0)
                    
                    if current_url in scraped_urls or depth > max_depth:
                        continue
                    
                    scraped_urls.add(current_url)
                    
                    try:
                        result = await crawler.arun(url=current_url)
                        
                        if result.success:
                            page_data = {
                                'url': current_url,
                                'title': result.metadata.get('title', ''),
                                'content': result.markdown,
                                'links': result.links,
                                'media': result.media,
                                'metadata': result.metadata,
                                'depth': depth
                            }
                            results.append(page_data)
                            
                            # Add internal links for further crawling
                            if depth < max_depth:
                                base_domain = urlparse(url).netloc
                                for link in result.links.get('internal', []):
                                    link_url = urljoin(current_url, link['href'])
                                    link_domain = urlparse(link_url).netloc
                                    
                                    if link_domain == base_domain and link_url not in scraped_urls:
                                        to_scrape.append((link_url, depth + 1))
                        
                    except Exception as e:
                        logger.warning(f"Failed to scrape {current_url}: {str(e)}")
                        continue
            
            return {
                'success': True,
                'root_url': url,
                'pages_scraped': len(results),
                'max_depth_reached': max([r.get('depth', 0) for r in results]) if results else 0,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to deep crawl {url}: {str(e)}")
            return {
                'success': False,
                'root_url': url,
                'error': str(e)
            }
    
    async def scrape_from_sitemap(self, sitemap_url: str, max_pages: int = 100) -> Dict:
        """Scrape URLs from sitemap"""
        try:
            # Download and parse sitemap
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Handle different sitemap formats
            urls = []
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Try to find URL elements
            for url_elem in root.findall('.//ns:url', namespaces):
                loc_elem = url_elem.find('ns:loc', namespaces)
                if loc_elem is not None:
                    urls.append(loc_elem.text)
            
            # If no URLs found, try without namespace
            if not urls:
                for url_elem in root.findall('.//url'):
                    loc_elem = url_elem.find('loc')
                    if loc_elem is not None:
                        urls.append(loc_elem.text)
            
            # Limit URLs
            urls = urls[:max_pages]
            
            # Scrape each URL
            results = []
            # Use context manager pattern for proper resource management
            async with AsyncWebCrawler(verbose=True) as crawler:
                for url in urls:
                    try:
                        result = await crawler.arun(url=url)
                        
                        if result.success:
                            page_data = {
                                'url': url,
                                'title': result.metadata.get('title', ''),
                                'content': result.markdown,
                                'links': result.links,
                                'media': result.media,
                                'metadata': result.metadata
                            }
                            results.append(page_data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to scrape {url}: {str(e)}")
                        continue
            
            return {
                'success': True,
                'sitemap_url': sitemap_url,
                'total_urls_found': len(urls),
                'pages_scraped': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape from sitemap {sitemap_url}: {str(e)}")
            return {
                'success': False,
                'sitemap_url': sitemap_url,
                'error': str(e)
            }
    
    def delete_scraping_job(self, job_id: str, user_id: int) -> bool:
        """Delete scraping job and its associated data"""
        try:
            conn = self._get_db_connection()
            if self.db_url.startswith("sqlite:"):
                cursor = conn.cursor()
                
                # Check if job exists and belongs to user
                cursor.execute("""
                    SELECT id FROM scraping_jobs 
                    WHERE id = ? AND user_id = ?;
                """, (job_id, user_id))
                
                if not cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return False
                
                # Delete the job
                cursor.execute("""
                    DELETE FROM scraping_jobs WHERE id = ? AND user_id = ?;
                """, (job_id, user_id))
            else:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Check if job exists and belongs to user
                cursor.execute("""
                    SELECT id FROM scraping_jobs 
                    WHERE id = %s AND user_id = %s;
                """, (job_id, user_id))
                
                if not cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return False
                
                # Delete the job
                cursor.execute("""
                    DELETE FROM scraping_jobs WHERE id = %s AND user_id = %s;
                """, (job_id, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Delete associated data files
            import shutil
            data_dir = f"data/raw/{job_id}"
            if os.path.exists(data_dir):
                try:
                    shutil.rmtree(data_dir)
                    logger.info(f"Deleted data directory: {data_dir}")
                except Exception as e:
                    logger.warning(f"Failed to delete data directory {data_dir}: {str(e)}")
            
            logger.info(f"Deleted scraping job {job_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete scraping job {job_id}: {str(e)}")
            return False

    def get_completed_jobs(self, user_id: int) -> List[Dict]:
        """Get completed scraping jobs that are available for vector database creation"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            if self.db_url.startswith("sqlite:"):
                cursor.execute("""
                    SELECT sj.id, sj.url, sj.scraping_type, sj.status, sj.created_at, sj.completed_at,
                           sj.result_summary, vd.id as vector_db_id
                    FROM scraping_jobs sj
                    LEFT JOIN vector_databases vd ON sj.id = vd.job_id AND sj.user_id = vd.user_id
                    WHERE sj.user_id = ? AND sj.status = 'completed'
                    ORDER BY sj.completed_at DESC;
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT sj.id, sj.url, sj.scraping_type, sj.status, sj.created_at, sj.completed_at,
                           sj.result_summary, vd.id as vector_db_id
                    FROM scraping_jobs sj
                    LEFT JOIN vector_databases vd ON sj.id = vd.job_id AND sj.user_id = vd.user_id
                    WHERE sj.user_id = %s AND sj.status = 'completed'
                    ORDER BY sj.completed_at DESC;
                """, (user_id,))
            
            jobs = []
            for row in cursor.fetchall():
                if self.db_url.startswith("sqlite:"):
                    job = {
                        'id': row[0],
                        'url': row[1],
                        'scraping_type': row[2],
                        'status': row[3],
                        'created_at': row[4],
                        'completed_at': row[5],
                        'result_summary': json.loads(row[6]) if row[6] else {},
                        'has_vector_db': row[7] is not None
                    }
                else:
                    job = {
                        'id': row[0],
                        'url': row[1],
                        'scraping_type': row[2],
                        'status': row[3],
                        'created_at': row[4].isoformat() if row[4] else None,
                        'completed_at': row[5].isoformat() if row[5] else None,
                        'result_summary': row[6] if row[6] else {},
                        'has_vector_db': row[7] is not None
                    }
                jobs.append(job)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(jobs)} completed jobs for user {user_id}")
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get completed jobs for user {user_id}: {str(e)}")
            return []
