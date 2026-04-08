
import asyncio
from crawl4ai import *

async def capture_javbus():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.javbus.com",
            config=CrawlerRunConfig(screenshot=True)
        )
        if result.success:
            with open("javbus_home.html", "w", encoding="utf-8") as f:
                f.write(result.html or "")
            print("HTML saved to javbus_home.html")

if __name__ == "__main__":
    asyncio.run(capture_javbus())
