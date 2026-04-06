import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Add download_actor_covers method to Crawler class
download_actor_method = """
    async def download_actor_covers(self, actor_name: str):
        print(f"\\n--- Downloading covers for {actor_name} ---")
        media_list_path = Path("actress") / actor_name / "media_list.json"
        
        if not media_list_path.exists():
            print(f"Media list for {actor_name} not found at {media_list_path}")
            return
            
        with open(media_list_path, 'r', encoding='utf-8') as f:
            media_list = json.load(f)
            
        headers = self._get_http_headers()
        headers['Referer'] = SITES_CONFIG.get(self.config.site, {}).get("home_url", "https://www.javbus.com") + "/"
        
        tasks = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for item in media_list:
                scene_id = item.get("id")
                if not scene_id: continue
                
                detail_path = self.media_dir / scene_id / f"{scene_id}.json"
                if not detail_path.exists():
                    print(f"Missing detail JSON for {scene_id}, skipping cover download.")
                    continue
                    
                with open(detail_path, 'r', encoding='utf-8') as df:
                    try:
                        detail = json.load(df)
                    except json.JSONDecodeError:
                        continue
                        
                cover_url = detail.get("cover_image")
                if cover_url:
                    if not cover_url.startswith('http'):
                        cover_url = "https://www.javbus.com" + cover_url
                        
                    from urllib import parse
                    parsed = parse.urlparse(cover_url)
                    name = Path(parsed.path).name
                    ext = '.' + name.split('.')[-1] if '.' in name else '.jpg'
                    
                    dest = self.media_dir / scene_id / f"cover{ext}"
                    
                    async def download_file(session, url, dest):
                        if dest.exists() and dest.stat().st_size > 0:
                            return True
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        try:
                            async with session.get(url, timeout=20) as resp:
                                resp.raise_for_status()
                                with open(dest, 'wb') as fh:
                                    async for chunk in resp.content.iter_chunked(8192):
                                        fh.write(chunk)
                                return True
                        except Exception as e:
                            if dest.exists() and dest.stat().st_size == 0:
                                try: dest.unlink()
                                except OSError: pass
                            print(f"Failed to download {url}: {e}", file=sys.stderr)
                            return False

                    tasks.append(download_file(session, cover_url, dest))
            
            if tasks:
                print(f"Found {len(tasks)} covers to download. Starting concurrent downloads...")
                semaphore = asyncio.Semaphore(10)
                async def sem_task(t):
                    async with semaphore:
                        return await t
                
                results = await asyncio.gather(*(sem_task(t) for t in tasks))
                success = sum(1 for r in results if r)
                print(f"Successfully downloaded/verified {success} covers for {actor_name}.")
            else:
                print(f"No covers found to download for {actor_name}.")

    async def process_scenes"""

content = content.replace("    async def process_scenes", download_actor_method)

# 2. Add argparse argument for --download-actor-covers
argparse_old = """    parser.add_argument("--active-scan", default="", help="Active scan file")"""
argparse_new = """    parser.add_argument("--active-scan", default="", help="Active scan file")
    parser.add_argument("--download-actor-covers", default="", help="Download all covers for the specified actor from their media_list.json")"""
content = content.replace(argparse_old, argparse_new)

# 3. Add to config object assignment
config_old = """    config.active_scan_file = args.active_scan"""
config_new = """    config.active_scan_file = args.active_scan
    config.download_actor_covers = args.download_actor_covers"""
content = content.replace(config_old, config_new)

# 4. Add config definition
config_def_old = """    active_scan_file: str = "" """
config_def_new = """    active_scan_file: str = ""
    download_actor_covers: str = "" """
content = content.replace(config_def_old, config_def_new)

# 5. Add execution logic
exec_old = """    if not any([run_search, run_parse, run_download]):
        run_search = run_parse = run_download = True

    await c.process_scenes(run_search, run_parse, run_download)"""

exec_new = """    if config.download_actor_covers:
        await c.download_actor_covers(config.download_actor_covers)
        return

    if not any([run_search, run_parse, run_download]):
        run_search = run_parse = run_download = True

    await c.process_scenes(run_search, run_parse, run_download)"""
content = content.replace(exec_old, exec_new)

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
