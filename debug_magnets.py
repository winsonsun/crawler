import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def main():
    gid = "67778147310"
    uc = "0"
    img = "/pics/cover/c4tq_b.jpg"
    page_url = "https://www.javbus.com/START-530"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1",
        "Referer": page_url,
        "X-Requested-With": "XMLHttpRequest"
    }
    
    url = f"https://www.javbus.com/ajax/uncledatoolsbyajax.php?gid={gid}&lang=zh&img={img}&uc={uc}"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
            for tr in soup.select("tr"):
                tds = tr.select("td")
                print([td.text.strip() for td in tds])

asyncio.run(main())
