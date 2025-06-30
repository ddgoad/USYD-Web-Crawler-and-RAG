"""
Web Scraping Service for USYD Web Crawler and RAG Application
Uses Crawl4AI for intelligent web content extraction
"""

import os
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from celery import Celery
import requests
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import asyncio

logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery(
    'scraper',
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

class ScrapingService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/usydrag")
        self.crawler = None
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    async def _get_crawler(self):
        """Get or create WebCrawler instance"""
        if not self.crawler:
            self.crawler = WebCrawler(verbose=True)
            await self.crawler.astart()
        return self.crawler
    
    def create_scraping_job(self, user_id: int, url: str, scraping_type: str, config: Dict) -> str:
        """Create a new scraping job"""
        try:
            job_id = str(uuid.uuid4())
            
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraping_jobs (id, user_id, url, scraping_type, status, config)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (job_id, user_id, url, scraping_type, 'pending', json.dumps(config)))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created scraping job {job_id} for user {user_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create scraping job: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str, user_id: int) -> Optional[Dict]:
        """Get scraping job status"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM scraping_jobs 
                WHERE id = %s AND user_id = %s;
            """, (job_id, user_id))
            
            job = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return dict(job) if job else None
            
        except Exception as e:
            logger.error(f"Failed to get job status: {str(e)}")
            return None
    
    def get_user_jobs(self, user_id: int) -> List[Dict]:
        """Get all scraping jobs for a user"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM scraping_jobs 
                WHERE user_id = %s 
                ORDER BY created_at DESC;
            """, (user_id,))
            
            jobs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(job) for job in jobs]
            
        except Exception as e:
            logger.error(f"Failed to get user jobs: {str(e)}")
            return []
    
    def _update_job_status(self, job_id: str, status: str, progress: int = 0, message: str = "", result_summary: Dict = None):
        """Update job status in database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            
            update_data = {
                'status': status,
                'progress': progress,
                'message': message
            }
            
            if result_summary:
                update_data['result_summary'] = result_summary
            
            if status in ['completed', 'failed']:
                cursor.execute("""
                    UPDATE scraping_jobs 
                    SET status = %s, completed_at = CURRENT_TIMESTAMP, result_summary = %s
                    WHERE id = %s;
                """, (status, json.dumps(result_summary) if result_summary else None, job_id))
            else:
                # Store progress in result_summary for running jobs
                progress_data = result_summary or {}
                progress_data.update(update_data)
                
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
            crawler = await self._get_crawler()
            
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
            
            crawler = await self._get_crawler()
            
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
            crawler = await self._get_crawler()
            
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
    
    @celery.task(bind=True)
    def process_scraping_job(self, job_id: str):
        """Background task for processing scraping jobs"""
        try:
            # Get job details
            conn = psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://localhost:5432/usydrag"))
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM scraping_jobs WHERE id = %s;
            """, (job_id,))
            
            job = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not job:
                raise Exception(f"Job {job_id} not found")
            
            # Update status to running
            service = ScrapingService()
            service._update_job_status(job_id, 'running', 0, 'Starting scraping process')
            
            # Run the appropriate scraping method
            config = job['config'] if job['config'] else {}
            
            async def run_scraping():
                if job['scraping_type'] == 'single':
                    return await service.scrape_single_page(job['url'])
                elif job['scraping_type'] == 'deep':
                    max_depth = config.get('max_depth', 3)
                    max_pages = config.get('max_pages', 50)
                    return await service.scrape_website_deep(job['url'], max_depth, max_pages)
                elif job['scraping_type'] == 'sitemap':
                    max_pages = config.get('max_pages', 100)
                    return await service.scrape_from_sitemap(job['url'], max_pages)
                else:
                    raise Exception(f"Unknown scraping type: {job['scraping_type']}")
            
            # Run the scraping
            result = asyncio.run(run_scraping())
            
            if result['success']:
                service._update_job_status(job_id, 'completed', 100, 'Scraping completed successfully', result)
                
                # Save scraped data to file
                data_dir = f"data/raw/{job_id}"
                os.makedirs(data_dir, exist_ok=True)
                
                with open(f"{data_dir}/scraped_data.json", 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Scraping job {job_id} completed successfully")
            else:
                service._update_job_status(job_id, 'failed', 0, f"Scraping failed: {result.get('error', 'Unknown error')}")
                logger.error(f"Scraping job {job_id} failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error processing scraping job {job_id}: {str(e)}")
            service = ScrapingService()
            service._update_job_status(job_id, 'failed', 0, f"Error: {str(e)}")
            raise