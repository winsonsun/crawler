import re

with open("src/crawler/crawler.py", "r") as f:
    content = f.read()

# 1. Improve _fetch_soup_safe to be more robust with age gates
soup_safe_fix = """
    async def _fetch_soup_safe(self, url: str, web_crawler: AsyncWebCrawler):
        from bs4 import BeautifulSoup
        
        # Fast path: Try lightweight aiohttp first
        async with aiohttp.ClientSession(headers=self._get_http_headers()) as session:
            try:
                async with session.get(url, timeout=10, allow_redirects=True) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        if "你是否已經成年" not in html and "確認" not in html:
                            soup = BeautifulSoup(html, 'lxml')
                            if soup.select('.movie-box') or soup.select('.bigImage'):
                                return soup
            except Exception as e:
                pass

        # Slow path: Fallback to crawl4ai for age-gate bypass
        js_bypass = '''
        return (() => {
            const ageCheck = document.querySelector('input[type="checkbox"]');
            if (ageCheck) ageCheck.click();
            const btn = Array.from(document.querySelectorAll('button, a')).find(b => b.innerText.includes('成年') || b.innerText.includes('確認'));
            if (btn) btn.click();
            return { cookie: document.cookie, userAgent: navigator.userAgent };
        })();
        '''
        
        # Run once to click the button
        result = await web_crawler.arun(
            url=url, 
            config=self.crawl_config, 
            headers=self._get_http_headers(), 
            js_code=js_bypass,
            wait_for=".movie-box, .bigImage, button:has-text('成年')"
        )
        
        # Update cookies
        js_out = getattr(result, 'js_execution_result', None) or {}
        results_arr = js_out.get('results', [])
        if isinstance(results_arr, list) and results_arr:
            res = results_arr[0]
            if isinstance(res, dict):
                self.dynamic_cookie = res.get('cookie', self.dynamic_cookie)
                self.dynamic_user_agent = res.get('userAgent', self.dynamic_user_agent)

        # If still on age gate, we might need a second pass or wait
        if "你是否已經成年" in (result.html or ""):
             result = await web_crawler.arun(
                url=url, 
                config=self.crawl_config,
                headers=self._get_http_headers(),
                wait_for=".movie-box, .bigImage"
            )

        return BeautifulSoup(result.html or "", 'lxml')
"""
content = re.sub(
    r"\s+async def _fetch_soup_safe\(self, url: str, web_crawler: AsyncWebCrawler\):.*?(?=\s+def _check_and_save_magnets)",
    soup_safe_fix,
    content,
    flags=re.DOTALL
)

# 2. Improve run_parse to handle JS extractor better and handle age gates
run_parse_fix = """
    async def run_parse(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler):
        headers = self._get_http_headers()
        url = search_result.get('page_url')
        if not url: return

        print(f"Scraping page URL: {url}")
        
        detail_js_extractor = SITES_CONFIG.get(self.config.site, {}).get("detail_js_extractor")
        
        # Use a wrapper JS to handle age gate before extraction
        js_wrapper = f'''
        return (async () => {{
            const ageBtn = Array.from(document.querySelectorAll('button, a')).find(b => b.innerText.includes('成年') || b.innerText.includes('確認'));
            if (ageBtn) {{
                const ageCheck = document.querySelector('input[type="checkbox"]');
                if (ageCheck) ageCheck.click();
                ageBtn.click();
                await new Promise(r => setTimeout(r, 2000)); // Wait for reload
            }}
            
            {detail_js_extractor if detail_js_extractor else "return {html: document.documentElement.innerHTML};"}
        }})();
        '''
        
        result = await web_crawler.arun(
            url=url, 
            config=self.crawl_config, 
            headers=headers, 
            js_code=js_wrapper,
            wait_for=".bigImage, .header, #magnet-table" if self.config.site == "javbus" else None
        )
        
        js_out = getattr(result, 'js_execution_result', None) or {}
        results_arr = js_out.get('results', [])
        detail = {}
        
        if results_arr and isinstance(results_arr[0], dict):
            detail = results_arr[0]
            # If it just returned HTML (fallback), parse it manually
            if "html" in detail and not detail.get("id"):
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(detail["html"], "lxml")
                # Simple extraction for javbus if JS extractor failed
                if self.config.site == "javbus":
                    detail["id"] = soup.select_one(".header") .text.split(" ")[0] if soup.select_one(".header") else scene_name
                    detail["title"] = soup.title.text if soup.title else scene_name
                    detail["cover_image"] = soup.select_one(".bigImage img")["src"] if soup.select_one(".bigImage img") else ""
        
        if not detail or not detail.get("id") or detail.get("id") == "JavBus":
            # Fallback to markdown parsing
            try:
                from .sites.javdb import page_parser
                detail = page_parser.parse_from_text(str(result.markdown), id_hint=scene_name)
            except: pass

        if detail:
            # Cleanup detail
            detail.pop('cookie', None)
            detail.pop('userAgent', None)
            detail.pop('html', None)
            if not detail.get("id"): detail["id"] = scene_name
            
            media_dir = self.media_dir / detail["id"]
            media_dir.mkdir(parents=True, exist_ok=True)
            detail_file = media_dir / f"{detail['id']}.json"
            
            with open(detail_file, 'w', encoding='utf-8') as fh:
                json.dump(detail, fh, ensure_ascii=False, indent=2)
            print(f"Wrote {detail_file}")
            
            if self.config.merge_detail:
                try:
                    from .lib import merge_detail_into_search as merger
                    merger.merge_detail(detail_file, self.config.site, search_dir=str(self.search_dir))
                except: pass
"""
content = re.sub(
    r"\s+async def run_parse\(self, scene_name: str, search_result: dict, web_crawler: AsyncWebCrawler\):.*?(?=\s+async def run_download)",
    run_parse_fix,
    content,
    flags=re.DOTALL
)

with open("src/crawler/crawler.py", "w") as f:
    f.write(content)
