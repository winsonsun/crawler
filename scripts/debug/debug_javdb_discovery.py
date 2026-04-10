import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig
from bs4 import BeautifulSoup

async def test():
    config = CrawlerConfig(site="javdb")
    c = Crawler(config)
    
    browser_conf = BrowserConfig(
        headless=True,
        extra_args=["--no-sandbox"]
    )
    
    async with AsyncWebCrawler(config=browser_conf) as w:
        url = 'https://javdb.com/'
        print(f"Fetching {url}...")
        
        soup = await c._fetch_soup_safe(url, w)
        
        print("\n--- HTML Selectors Check ---")
        selectors = ['.movie-box', '.item', '.movie-list', '.container', '.video-title', '.uid']
        for sel in selectors:
            found = soup.select(sel)
            print(f"Selector '{sel}': {len(found)} items found")
            if found and len(found) > 0:
                print(f"  Sample text: {found[0].text.strip()[:50]}")
                if sel == '.item':
                    print("\n  Detailed .item[0] structure:")
                    box = found[0].select_one('a.box')
                    if box:
                        print(f"    Box href: {box.get('href')}")
                        uid = box.select_one('.uid')
                        print(f"    UID (.uid): {uid.text.strip() if uid else 'NOT FOUND'}")
                        title = box.select_one('.video-title')
                        print(f"    Title (.video-title): {title.text.strip() if title else 'NOT FOUND'}")
                        meta = box.select_one('.meta')
                        print(f"    Meta (.meta): {meta.text.strip() if meta else 'NOT FOUND'}")

        # Try to find items manually if standard selectors fail
        if not soup.select('.item'):
            print("\nSearching for all <a> tags with 'v/' in href...")
            v_links = soup.select('a[href*="/v/"]')
            print(f"Found {len(v_links)} potential links")
            for link in v_links[:5]:
                print(f"  Link: {link.get('href')} | Text: {link.text.strip()}")

if __name__ == "__main__":
    asyncio.run(test())
