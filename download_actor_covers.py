import argparse
import json
import os
import asyncio
import aiohttp
from pathlib import Path
from urllib import parse

def _safe_ext_from_url(u: str) -> str:
    parsed = parse.urlparse(u)
    name = Path(parsed.path).name
    if '.' in name: return '.' + name.split('.')[-1]
    return '.jpg'

async def download_file(session, url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with session.get(url, timeout=20) as resp:
            resp.raise_for_status()
            with open(dest, 'wb') as f:
                async for chunk in resp.content.iter_chunked(8192):
                    f.write(chunk)
            return True
    except Exception as e:
        if dest.exists() and dest.stat().st_size == 0:
            try:
                dest.unlink()
            except:
                pass
        print(f"Failed to download {url}: {e}")
        return False

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("actor", help="Name of the actor")
    args = parser.parse_args()
    
    media_list_path = Path(f"actress/{args.actor}/media_list.json")
    if not media_list_path.exists():
        print(f"Media list for {args.actor} not found at {media_list_path}")
        return
        
    with open(media_list_path, 'r', encoding='utf-8') as f:
        media_list = json.load(f)
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36',
        'Cookie': 'PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1',
        'Referer': 'https://www.javbus.com/'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for item in media_list:
            scene_id = item.get("id")
            if not scene_id: continue
            
            detail_path = Path(f"media_detail/{scene_id}/{scene_id}.json")
            if not detail_path.exists():
                print(f"Missing detail JSON for {scene_id}")
                continue
                
            with open(detail_path, 'r', encoding='utf-8') as df:
                try:
                    detail = json.load(df)
                except Exception:
                    continue
                    
            cover_url = detail.get("cover_image")
            if cover_url:
                if not cover_url.startswith('http'):
                    cover_url = "https://www.javbus.com" + cover_url
                ext = _safe_ext_from_url(cover_url)
                dest = Path(f"media_detail/{scene_id}/cover{ext}")
                tasks.append(download_file(session, cover_url, dest))
        
        if tasks:
            print(f"Found {len(tasks)} covers to download. Starting concurrent downloads...")
            # Run concurrently in batches of 10 to avoid overwhelming the network/server
            semaphore = asyncio.Semaphore(10)
            async def sem_task(t):
                async with semaphore:
                    return await t
            
            results = await asyncio.gather(*(sem_task(t) for t in tasks))
            success = sum(1 for r in results if r)
            print(f"Successfully downloaded/verified {success} covers.")
        else:
            print("No covers found to download.")

if __name__ == '__main__':
    asyncio.run(main())
