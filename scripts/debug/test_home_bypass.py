import asyncio
import os
import sys
import base64
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crawler.crawler import Crawler, CrawlerConfig
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawler.lib.omni_solver import GeminiOmniSolver, SolverAction

async def test_home_bypass():
    print("--- Starting JavBus First Page Crawl Test ---")
    # Use standard config
    config = CrawlerConfig(site="javbus")
    c = Crawler(config)
    
    # Use a fresh persistent session to ensure we see the challenges if they exist
    session_path = os.path.join(os.getcwd(), "config", "browser_profile_test")
    browser_conf = BrowserConfig(
        headless=True,
        user_data_dir=session_path,
        use_managed_browser=True,
        extra_args=["--no-sandbox", "--disable-gpu"]
    )
    
    async with AsyncWebCrawler(config=browser_conf) as w:
        url = "https://www.javbus.com"
        print(f"Target URL: {url}")
        
        # This will now trigger: 
        # 1. Proactive cookie injection
        # 2. Fast aiohttp check
        # 3. Medium static JS bypass
        # 4. Slow OmniSolver (if reCAPTCHA or complex gate exists)
        soup = await c._fetch_soup_safe(url, w)
        
        if soup:
            # Check for movie boxes which indicate a successful load of the first page
            items = soup.select('.movie-box')
            if items:
                print(f"SUCCESS: Found {len(items)} movie items on the first page.")
                # Print some IDs as proof
                for item in items[:3]:
                    date_tag = item.select_one('date')
                    if date_tag:
                        print(f" - Found Item ID: {date_tag.text.strip()}")
            else:
                print("FAILED: Page loaded but no movie items found. Might be blocked or parsed incorrectly.")
                # Save debug screenshot if failed
                await _save_debug(url, w, c)
        else:
            print("FAILED: Could not load home page after all bypass attempts.")
            await _save_debug(url, w, c)

async def _save_debug(url, w, c):
    result = await w.arun(url=url, config=c.crawl_config)
    b64 = getattr(result, 'screenshot', None) or getattr(result, 'base64_screenshot', None)
    if b64:
        with open("debug_home_fail.jpg", "wb") as f:
            f.write(base64.b64decode(b64))
        print("Saved debug screenshot: debug_home_fail.jpg")
    with open("debug_home_fail.html", "w", encoding="utf-8") as f:
        f.write(result.html or "")
    print("Saved debug HTML: debug_home_fail.html")

if __name__ == "__main__":
    asyncio.run(test_home_bypass())
