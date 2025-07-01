#!/usr/bin/env python3
"""
Test crawl4ai API directly
"""

import asyncio

async def test_api():
    try:
        from crawl4ai import AsyncWebCrawler
        print("✓ Import successful")
        
        # Check methods
        print("Methods:", [method for method in dir(AsyncWebCrawler) if not method.startswith('_')])
        
        # Try to create and use crawler
        async with AsyncWebCrawler() as crawler:
            print("✓ Created crawler with context manager")
            result = await crawler.arun(url="https://httpbin.org/html")
            print(f"✓ Result: {result.success if result else 'None'}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
