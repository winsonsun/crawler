import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def test():
    config = CrawlerConfig(site="javdb")
    c = Crawler(config)
    
    browser_conf = BrowserConfig(
        headless=True,
        extra_args=["--no-sandbox"]
    )
    
    async with AsyncWebCrawler(config=browser_conf) as w:
        url = 'https://javdb.com/v/yrOMa'
        print(f"Fetching {url}...")
        
        # We need to bypass cloudflare first
        await c._fetch_soup_safe('https://javdb.com', w)
        
        result = await w.arun(
            url=url,
            config=c.crawl_config,
            headers=c._get_http_headers()
        )
        
        print("\n--- Result Markdown Snippet ---")
        print(result.markdown[:1000])
        
        from sites.javdb import page_parser
        detail = page_parser.parse_from_text(result.markdown, id_hint="MIST-001")
        
        print("\n--- Extracted Detail ---")
        import pprint
        pprint.pprint(detail)

if __name__ == "__main__":
    asyncio.run(test())
