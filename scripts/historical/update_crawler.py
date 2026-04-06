import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Add aiohttp import and lock
if "import aiohttp" not in content:
    content = content.replace("import asyncio", "import asyncio\nimport aiohttp")

if "self.search_lock =" not in content:
    content = re.sub(
        r"self\.session_id =.*?magic=True,\n\s+user_agent=self\.dynamic_user_agent\n\s+\)",
        "\\g<0>\n        self.search_lock = asyncio.Lock()",
        content,
        flags=re.DOTALL
    )

# 2. Async save_search_result
def async_save_replace(match):
    return """
    async def _save_search_result(self, scene_name, data):
        self.search_dir.mkdir(exist_ok=True)
        filename = self.search_dir / f"{self.config.site}_search.json"
        
        async with self.search_lock:
            def sync_save():
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    existing_data = {}
                existing_data[scene_name] = data
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
            await asyncio.to_thread(sync_save)
            print(f"Saved search result for '{scene_name}' to '{filename}'")
"""
content = re.sub(
    r"\s+def _save_search_result\(self, scene_name, data\):.*?(?=\s+def parse_line)",
    async_save_replace,
    content,
    flags=re.DOTALL
)

# 3. Update run_search to await _save_search_result
content = content.replace("self._save_search_result(scene_name, result)", "await self._save_search_result(scene_name, result)")

# 4. Update run_download to use process_detail_file_async
download_replace = """
                headers = {
                    'Cookie': self.dynamic_cookie,
                    'User-Agent': self.dynamic_user_agent,
                    'Referer': SITES_CONFIG.get(self.config.site, {}).get("home_url", "")
                }
                
                res = await downloader.process_detail_file_async(detail_file, media_dir=str(self.media_dir), headers=headers)
"""
content = re.sub(
    r"headers = \{\s*'Cookie': self\.dynamic_cookie,\s*'User-Agent': self\.dynamic_user_agent,\s*'Referer':.*?\}.*?res = downloader\.process_detail_file\(.*?headers=headers\)",
    download_replace.strip(),
    content,
    flags=re.DOTALL
)

# 5. Optimize _fetch_soup_safe to use aiohttp first
soup_replace = """
    async def _fetch_soup_safe(self, url: str, web_crawler: AsyncWebCrawler):
        from bs4 import BeautifulSoup
        
        # Fast path: Try lightweight aiohttp first
        async with aiohttp.ClientSession(headers=self._get_http_headers()) as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'lxml')
                        if soup.select('.movie-box') or soup.select('.bigImage'):
                            return soup
            except Exception as e:
                print(f"aiohttp fallback triggered for {url}: {e}")

        # Slow path: Fallback to crawl4ai for age-gate/cookie refresh
        js_inject_cookies = f'''
        return (() => {{
            if (!document.cookie.includes('age=verified')) {{
                document.cookie = "{self.dynamic_cookie.replace('"', '\\"')}";
                console.log("Cookies injected");
            }}
            const ageCheck = document.querySelector('input[type="checkbox"]');
            if (ageCheck) {{
                ageCheck.click();
                const buttons = Array.from(document.querySelectorAll('button, a'));
                const submitBtn = buttons.find(b => b.innerText.includes('成年') || b.innerText.includes('18歳以上') || b.innerText.includes('確認'));
                if (submitBtn) submitBtn.click();
            }}
            return {{
                cookie: document.cookie,
                userAgent: navigator.userAgent
            }};
        }})();
        '''
        result = await web_crawler.arun(url=url, config=self.crawl_config, headers=self._get_http_headers(), js_code=js_inject_cookies)
        
        js_out = getattr(result, 'js_execution_result', None) or {}
        results_arr = js_out.get('results', [])
        if isinstance(results_arr, list) and results_arr:
            res = results_arr[0]
            self.dynamic_cookie = res.get('cookie', self.dynamic_cookie)
            self.dynamic_user_agent = res.get('userAgent', self.dynamic_user_agent)
            
        soup = BeautifulSoup(result.html or "", 'lxml')
        
        if not soup.select('.movie-box') and not soup.select('.bigImage'):
            print(f"Content not found on {url}. Retrying with wait...")
            result = await web_crawler.arun(
                url=url, 
                config=self.crawl_config,
                headers=self._get_http_headers(),
                wait_for=".movie-box, .bigImage"
            )
            soup = BeautifulSoup(result.html or "", 'lxml')
            
        return soup
"""
content = re.sub(
    r"\s+async def _fetch_soup_safe\(self, url: str, web_crawler: AsyncWebCrawler\):.*?(?=\s+def _check_and_save_magnets)",
    soup_replace,
    content,
    flags=re.DOTALL
)

# 6. Concurrency in process_scenes
scenes_replace = """
            if not self.config.discover and not self.config.collection_scan:
                # Use a Semaphore to limit concurrent Playwright pages
                semaphore = asyncio.Semaphore(3)
                
                async def process_with_semaphore(idx, scene_name):
                    async with semaphore:
                        if not self.config.force and self._is_complete(scene_name):
                            print(f"Skipping '{scene_name}' as it appears complete. Use --force to re-process.")
                            return
                        try:
                            res = await self._process_single_scene(scene_name, web_crawler, run_search, run_parse, run_download)
                            scene_skipped = isinstance(res, dict) and res.get('scene_skipped', False)
                            
                            # Random delay inside the task to stagger load
                            if idx < len(self.config.scenes) - 1 and not scene_skipped:
                                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                                print(f"[{scene_name}] Waiting for {delay:.2f} seconds before next scene...")
                                await asyncio.sleep(delay)
                        except Exception as e:
                            print(f"Failed to process scene '{scene_name}' after multiple attempts: {e}", file=sys.stderr)
                
                tasks = [process_with_semaphore(i, sc) for i, sc in enumerate(self.config.scenes)]
                if tasks:
                    await asyncio.gather(*tasks)
"""
content = re.sub(
    r"\s+if not self\.config\.discover and not self\.config\.collection_scan:\s+for i, scene in enumerate\(self\.config\.scenes\):.*?(?=\s+def parse_time)",
    scenes_replace,
    content,
    flags=re.DOTALL
)

# Use lxml in process_scenes / discovery mode explicitly if BeautifulSoup is there
content = content.replace("BeautifulSoup(result.html or \"\", 'html.parser')", "BeautifulSoup(result.html or \"\", 'lxml')")

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
