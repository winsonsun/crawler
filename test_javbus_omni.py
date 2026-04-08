
import asyncio
import os
from src.crawler.crawler import CrawlerConfig, AsyncWebCrawler, Crawler

async def test_javbus():
    config = CrawlerConfig(site="javbus", verbose=True)
    # Use a known ID that might trigger search or direct hit
    scene_name = "葵つかさ" 
    
    async with AsyncWebCrawler() as web_crawler:
        crawler = Crawler(config)
        try:
            result = await crawler.run_search(scene_name, web_crawler)
            print(f"Search Result: {result}")
        except Exception as e:
            print(f"Search Failed: {e}")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set")
    else:
        asyncio.run(test_javbus())
