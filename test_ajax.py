import asyncio
import aiohttp

async def main():
    gid = "67778147310"
    uc = "0"
    img = "/pics/cover/c4tq_b.jpg"
    page_url = "https://www.javbus.com/START-530"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Cookie": "PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1",
        "Referer": page_url,
        "X-Requested-With": "XMLHttpRequest"
    }
    
    endpoints = [
        "https://www.javbus.com/ajax/uncensored-torrent.php",
        "https://www.javbus.com/ajax/torrent.php"
    ]
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for ep in endpoints:
            url = f"{ep}?gid={gid}&lang=zh&img={img}&uc={uc}"
            print(f"Fetching: {url}")
            async with session.get(url) as resp:
                text = await resp.text()
                print(f"Status: {resp.status}")
                print(f"Response: {text[:500]}")

asyncio.run(main())
