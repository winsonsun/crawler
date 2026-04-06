import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup

async def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Cookie": "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1"
    }
    url = "https://www.javbus.com/START-530"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            html = await resp.text()
            print("HTML Length:", len(html))
            print("GID Match:", bool(re.search(r"gid = [0-9]+", html)))
            print("IMG Match:", bool(re.search(r"img = '[^']+'", html)))
            print("UC Match:", bool(re.search(r"uc = [0-9]+", html)))
            
            with open("debug_page.html", "w") as f:
                f.write(html)

asyncio.run(main())
