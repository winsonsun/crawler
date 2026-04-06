# -*- coding: utf-8 -*-
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def test():
    c = Crawler(CrawlerConfig())
    browser_conf = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_conf) as w:
        url = 'https://www.javbus.com/star/11mp'
        print(f"Fetching {url}...")
        soup = await c._fetch_soup_safe(url, w)
        if not soup:
            print("Failed to fetch soup.")
            return
            
        photo_info = soup.select_one('.photo-info')
        if photo_info:
            print("Found .photo-info")
            print(photo_info.prettify())
            for p in photo_info.select('p'):
                print(f"P tag text: '{p.get_text(strip=True)}'")
        else:
            print(".photo-info not found")
            # Print some of the HTML to see what's there
            print(str(soup)[:1000])

if __name__ == "__main__":
    asyncio.run(test())
