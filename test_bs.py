from crawl4ai import AsyncWebCrawler
import asyncio
from bs4 import BeautifulSoup

async def main():
    async with AsyncWebCrawler() as c:
        res = await c.arun('https://www.javbus.com/')
        soup = BeautifulSoup(res.html, 'html.parser')
        print(len(soup.select('.movie-box')))
        print(len(soup.select('a')))
        print(res.html[:500])

asyncio.run(main())
