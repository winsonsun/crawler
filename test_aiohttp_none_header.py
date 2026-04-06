import asyncio
import aiohttp

async def main():
    headers = {"User-Agent": None}
    try:
        session = aiohttp.ClientSession(headers=headers)
        async with session.get("http://example.com") as resp:
            print("Success")
        await session.close()
    except Exception as e:
        print(f"Exception: {type(e).__name__} - {e}")

asyncio.run(main())
