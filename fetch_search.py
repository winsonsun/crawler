import asyncio
import sys
import os
from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def main():
    name = "葵つかさ"
    config = CrawlerConfig(site="javbus")
    c = Crawler(config)
    
    browser_conf = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_conf) as web_crawler:
        url = f"https://www.javbus.com/search/{name}"
        soup = await c._fetch_soup_safe(url, web_crawler)
        if soup:
            with open("javbus_search.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print("Saved javbus_search.html")
        else:
            print("Failed to fetch search page.")

if __name__ == "__main__":
    asyncio.run(main())
