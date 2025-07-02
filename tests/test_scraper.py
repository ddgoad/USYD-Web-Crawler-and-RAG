#!/usr/bin/env python3
"""
Simple test script to isolate the scraping issue
"""

import asyncio
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def flush_print(*args, **kwargs):
    """Print with immediate flush"""
    print(*args, **kwargs)
    sys.stdout.flush()

async def test_crawl4ai():
    """Test crawl4ai functionality"""
    try:
        flush_print("=== Testing crawl4ai import ===")
        from crawl4ai import AsyncWebCrawler
        flush_print("✓ crawl4ai imported successfully")
        
        flush_print("=== Testing simple scrape with context manager ===")
        test_url = "https://httpbin.org/html"
        
        async with AsyncWebCrawler(verbose=True) as crawler:
            flush_print("✓ AsyncWebCrawler context created")
            result = await crawler.arun(url=test_url)
            flush_print(f"✓ Scrape result: success={result.success}")
        
        if result.success:
            flush_print(f"✓ Content length: {len(result.markdown)}")
            flush_print(f"✓ Title: {result.metadata.get('title', 'No title')}")
        else:
            flush_print("✗ Scrape failed")
            
        return result.success if result else False
        
    except Exception as e:
        flush_print(f"✗ Error: {str(e)}")
        logger.error("Error in test_crawl4ai", exc_info=True)
        return False

def test_threading_with_asyncio():
    """Test threading with asyncio.run"""
    import threading
    
    flush_print("=== Testing threading + asyncio ===")
    
    def thread_function():
        try:
            flush_print("[THREAD] Starting thread")
            result = asyncio.run(test_crawl4ai())
            flush_print(f"[THREAD] Thread completed, result: {result}")
            return result
        except Exception as e:
            flush_print(f"[THREAD] Thread error: {str(e)}")
            logger.error("Error in thread", exc_info=True)
            return False
    
    thread = threading.Thread(target=thread_function)
    thread.start()
    thread.join(timeout=30)  # 30 second timeout
    
    if thread.is_alive():
        flush_print("✗ Thread is still running after 30 seconds - possible hang")
        return False
    else:
        flush_print("✓ Thread completed successfully")
        return True

if __name__ == "__main__":
    flush_print("=== Starting scraper isolation test ===")
    
    # Test 1: Direct async test
    flush_print("\n--- Test 1: Direct async test ---")
    try:
        result1 = asyncio.run(test_crawl4ai())
        flush_print(f"Direct async test result: {result1}")
    except Exception as e:
        flush_print(f"Direct async test failed: {e}")
        result1 = False
    
    # Test 2: Threading + asyncio test  
    flush_print("\n--- Test 2: Threading + asyncio test ---")
    try:
        result2 = test_threading_with_asyncio()
        flush_print(f"Threading async test result: {result2}")
    except Exception as e:
        flush_print(f"Threading async test failed: {e}")
        result2 = False
    
    flush_print(f"\n=== Test Summary ===")
    flush_print(f"Direct async: {'✓' if result1 else '✗'}")
    flush_print(f"Threading + async: {'✓' if result2 else '✗'}")
    
    if result1 and result2:
        flush_print("✓ All tests passed - scraper should work")
        sys.exit(0)
    else:
        flush_print("✗ Some tests failed - scraper has issues")
        sys.exit(1)
