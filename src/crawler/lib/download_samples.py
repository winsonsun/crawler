#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download sample images and cover_image from a media detail JSON.

Usage:
  python3 download_samples.py media_detail/MIST-001/MIST-001.json

Saves samples to `media_detail/{id}/samples/` and cover to `media_detail/{id}/cover{ext}`.
"""
import argparse
import json
import os
import time
import asyncio
import aiohttp
from pathlib import Path
from urllib import parse
from .exceptions import DownloadHttpError, DownloadUrlError, DownloadError

CRAW_DATA = os.environ.get("CRAW_DATA", "./data")
DEFAULT_MEDIA_DIR = os.path.join(CRAW_DATA, "media_detail")

DEFAULT_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
DEFAULT_COOKIE = 'PHPSESSID=chekskp1bf9hssrr3gq7e5mag0; existmag=mag; age=verified; dv=1'

def _safe_ext_from_url(u: str) -> str:
    parsed = parse.urlparse(u)
    path = parsed.path
    name = Path(path).name
    if '.' in name:
        return '.' + name.split('.')[-1]
    return '.jpg'


async def download_url_async(session: aiohttp.ClientSession, url: str, dest: Path, timeout: int = 20) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            with open(dest, 'wb') as fh:
                async for chunk in resp.content.iter_chunked(8192):
                    fh.write(chunk)
            return True
    except aiohttp.ClientResponseError as e:
        if dest.exists() and not dest.stat().st_size:
            try: dest.unlink()
            except OSError: pass
        raise DownloadHttpError(f"HTTP error {e.status} for {url}", status_code=e.status)
    except Exception as e:
        if dest.exists() and not dest.stat().st_size:
            try: dest.unlink()
            except OSError: pass
        raise DownloadError(f"A non-network error occurred: {e}") from e

def download_url(url: str, dest: Path, timeout: int = 20, headers: dict = None) -> bool:
    async def _run():
        req_headers = {
            'User-Agent': DEFAULT_UA,
            'Cookie': DEFAULT_COOKIE,
            'Referer': 'https://www.javbus.com/'
        }
        if headers:
            req_headers.update(headers)
        async with aiohttp.ClientSession(headers=req_headers) as session:
            return await download_url_async(session, url, dest, timeout)
    return asyncio.run(_run())

def is_scene_complete(detail_file: Path, media_dir: str = DEFAULT_MEDIA_DIR) -> bool:
    """Check if a scene is complete based on its detail JSON and existing files."""
    if not detail_file.is_file():
        return False
    
    try:
        data = json.loads(detail_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, IOError):
        return False
    
    sid = data.get('id') or detail_file.stem
    outdir = Path(media_dir) / sid
    
    # Check cover
    cover_url = data.get('cover_image')
    if cover_url:
        cover_ext = _safe_ext_from_url(cover_url)
        cover_path = outdir / f'cover{cover_ext}'
        if not cover_path.exists() or cover_path.stat().st_size == 0:
            return False
    
    # Check samples
    samples_dir = outdir / 'samples'
    samples = data.get('sample_images') or []
    if not samples:  # If no samples are listed, consider it complete if the cover is there
        return True
        
    for i, u in enumerate(samples):
        ext = _safe_ext_from_url(u)
        fname = f'sample_{i:02d}{ext}'
        dst = samples_dir / fname
        if not dst.exists() or dst.stat().st_size == 0:
            return False
            
    return True


async def process_detail_file_async(path: Path, timeout: int = 20, download_cover: bool = True, skip_existing: bool = True, media_dir: str = DEFAULT_MEDIA_DIR, headers: dict = None, session: aiohttp.ClientSession = None):
    data = json.loads(path.read_text(encoding='utf-8'))
    sid = data.get('id') or path.stem
    outdir = Path(media_dir) / sid
    samples_dir = outdir / 'samples'
    samples_dir.mkdir(parents=True, exist_ok=True)

    results = {'id': sid, 'downloaded': [], 'skipped': [], 'failed': []}

    if skip_existing and is_scene_complete(path, media_dir=media_dir):
        results['scene_skipped'] = True
        results['skipped'].append(str(outdir))
        return results

    tasks = []
    semaphore = asyncio.Semaphore(5)
    
    async def _dl_task(url, dest_path):
        if skip_existing and dest_path.exists() and dest_path.stat().st_size > 0:
            results['skipped'].append(str(dest_path))
            return
        async with semaphore:
            try:
                ok = await download_url_async(session, url, dest_path, timeout=timeout)
                if ok: results['downloaded'].append(str(dest_path))
                else: results['failed'].append(url)
            except Exception:
                results['failed'].append(url)

    # Use provided session or create a temporary one
    close_session = False
    if session is None:
        req_headers = {
            'User-Agent': DEFAULT_UA,
            'Cookie': DEFAULT_COOKIE,
            'Referer': 'https://www.javbus.com/'
        }
        if headers:
            req_headers.update(headers)
        session = aiohttp.ClientSession(headers=req_headers)
        close_session = True

    try:
        # Cover
        cover_url = data.get('cover_image')
        if download_cover and cover_url:
            cover_ext = _safe_ext_from_url(cover_url)
            cover_path = outdir / f'cover{cover_ext}'
            tasks.append(_dl_task(cover_url, cover_path))

        # Samples
        samples = data.get('sample_images') or []
        for i, u in enumerate(samples):
            ext = _safe_ext_from_url(u)
            fname = f'sample_{i:02d}{ext}'
            dst = samples_dir / fname
            tasks.append(_dl_task(u, dst))

        # Download all images concurrently
        if tasks:
            await asyncio.gather(*tasks)
            
    finally:
        if close_session:
            await session.close()
            
    return results

def process_detail_file(path: Path, timeout: int = 20, download_cover: bool = True, skip_existing: bool = True, media_dir: str = DEFAULT_MEDIA_DIR, headers: dict = None):
    return asyncio.run(process_detail_file_async(path, timeout, download_cover, skip_existing, media_dir, headers))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('path', help='detail json file or directory')
    p.add_argument('--timeout', type=int, default=20, help='HTTP timeout seconds')
    p.add_argument('--no-cover', dest='cover', action='store_false', help='Do not download cover image')
    p.add_argument('--no-skip', dest='skip', action='store_false', help='Do not skip existing files')
    p.add_argument('--media-dir', default=DEFAULT_MEDIA_DIR, help='Directory to save media details')
    args = p.parse_args()

    path = Path(args.path)
    all_results = []
    if path.is_dir():
        for j in sorted(path.glob('*.json')):
            res = process_detail_file(j, timeout=args.timeout, download_cover=args.cover, skip_existing=args.skip, media_dir=args.media_dir)
            all_results.append(res)
            print(f"{j}: downloaded={len(res['downloaded'])} skipped={len(res['skipped'])} failed={len(res['failed'])}")
    else:
        if not path.exists():
            print(f"Not found: {path}")
            raise SystemExit(2)
        res = process_detail_file(path, timeout=args.timeout, download_cover=args.cover, skip_existing=args.skip, media_dir=args.media_dir)
        print(f"{path}: downloaded={len(res['downloaded'])} skipped={len(res['skipped'])} failed={len(res['failed'])}")


if __name__ == '__main__':
    main()
