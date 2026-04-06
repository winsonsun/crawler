# -*- coding: utf-8 -*-
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def main():
    config = CrawlerConfig()
    # Force profile re-extraction
    config.force = True
    c = Crawler(config)
    
    active_scan_data = c._load_active_scan()
    if not active_scan_data:
        print("No active scan data found.")
        return

    browser_conf = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_conf) as web_crawler:
        for name, url in active_scan_data.items():
            if not url: continue
            
            # Check if it needs fixing (has 3 or fewer keys)
            actor_file = c.actress_dir / name / f"{name}.json"
            needs_fix = True
            if actor_file.exists():
                import json
                try:
                    with open(actor_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if len(data.keys()) > 3:
                            needs_fix = False
                except: pass
            
            if needs_fix:
                print(f"Fixing profile for {name}...")
                await c._extract_and_save_actor_info(url, name, web_crawler)
                # Sleep a bit to be nice
                await asyncio.sleep(2)
            else:
                print(f"Profile for {name} is already correct.")

if __name__ == "__main__":
    asyncio.run(main())
