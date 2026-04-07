import asyncio
import sys
import os
from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def main():
    name = "葵つかさ"
    config = CrawlerConfig(site="javbus", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
    c = Crawler(config)
    
    # We'll use AsyncWebCrawler to find the star page
    browser_conf = BrowserConfig(headless=True)
    async with AsyncWebCrawler(config=browser_conf) as web_crawler:
        # Search for the star
        search_url = f"https://www.javbus.com/search/{name}&type=star"
        print(f"Searching for {name} at {search_url}")
        
        from bs4 import BeautifulSoup
        
        # Try a few URLs
        urls = [
            f"https://www.javbus.com/search/{name}&type=star",
            f"https://www.javbus.com/search/{name}"
        ]
        
        star_url = None
        for url in urls:
            soup = await c._fetch_soup_safe(url, web_crawler)
            if soup:
                # Find links containing /star/
                links = soup.select('a[href*="/star/"]')
                for link in links:
                    if name in link.text:
                        star_url = link['href']
                        if not star_url.startswith('http'):
                            star_url = "https://www.javbus.com" + star_url
                        print(f"Found star URL: {star_url}")
                        break
            if star_url: break
            
        if not star_url:
            print("Failed to find star URL via search.")
            # Hardcoded fallback if search fails (common IDs)
            # star_url = "https://www.javbus.com/star/2mo" # for instance
            return

        # Now we have the star URL, let's extract her media list
        # We can use the crawler's _extract_and_save_actor_info if it's suitable,
        # but let's just do it here to see what happens.
        await c._extract_and_save_actor_info(star_url, name, web_crawler)
        print(f"Extraction for {name} complete.")

if __name__ == "__main__":
    asyncio.run(main())
