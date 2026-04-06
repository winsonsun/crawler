import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def main():
    url = "https://www.javbus.com/star/b64"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "lxml")
            
            info = {}
            avatar = soup.select_one(".photo-frame img")
            if avatar:
                info["avatar"] = avatar.get("src", "")
                if not info["avatar"].startswith("http"):
                    info["avatar"] = "https://www.javbus.com" + info["avatar"]
                info["name"] = avatar.get("title", "")
                
            for p in soup.select(".photo-info p"):
                text = p.text.strip()
                if ":" in text:
                    k, v = text.split(":", 1)
                    info[k.strip()] = v.strip()
            
            print(info)

asyncio.run(main())
