
import asyncio
from crawl4ai import *

async def capture_javbus():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.javbus.com",
            config=CrawlerRunConfig(screenshot=True)
        )
        if result.success:
            with open("javbus_homepage.png", "wb") as f:
                f.write(base64.b64decode(result.screenshot))
            print("Screenshot saved to javbus_homepage.png")
            print(f"URL: {result.url}")
            # print(f"Markdown: {result.markdown[:500]}")

if __name__ == "__main__":
    import base64
    asyncio.run(capture_javbus())
