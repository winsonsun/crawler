import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from src.crawler.crawler import CrawlerConfig, Crawler

async def test():
    config = CrawlerConfig(site="javbus", download_image=False, force=True, verbose=False)
    c = Crawler(config)
    browser_conf = BrowserConfig(headless=True, extra_args=['--no-sandbox'])
    
    async with AsyncWebCrawler(config=browser_conf) as web_crawler:
        c.dynamic_cookie = "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1"
        try:
            await c.run_parse("SORA-631", {"page_url": "https://www.javbus.com/SORA-631"}, web_crawler)
        except Exception as e:
            print("ERROR", e)

asyncio.run(test())
