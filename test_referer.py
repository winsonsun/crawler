import asyncio
import aiohttp

async def fetch(ref):
    headers = {
        'Cookie': 'PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1', 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36', 
        'Referer': ref
    }
    url = "https://www.javbus.com/pics/sample/c45t_1.jpg"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            print(f"Referer: {ref} => {resp.status}")

async def main():
    await fetch("https://www.javbus.com")
    await fetch("https://www.javbus.com/")

asyncio.run(main())
